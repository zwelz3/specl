"""spec_to_rdf.py — translate a specl markdown spec to Turtle.

Usage: specl-translate <spec.md> <spec.ttl> [--fail-on-warning]

Parses markdown with YAML front-matter, H1 sections, ID-bulleted items
(R1.1, US3, OQ1, D2), and optional indented sub-bullet annotations that
populate the structured RDF properties the shapes graph asks for.

Sub-bullet annotation syntax (Phase 1, specl 0.2.0):

    - R1.1 The library MUST create holons addressable by IRI.
      - priority: MUST
      - constrains: HolonicDataset, HolonicStore
      - acceptance: Given a fresh dataset, when add_holon is called, iri appears in list_holons
      - verifiedBy: tests/test_client.py::test_add_holon

Comma-separated values on a multi-valued sub-bullet produce multiple
triples. Existing specs without sub-bullets emit identical output to
0.1.x (backward compatibility is a hard requirement).
"""
from __future__ import annotations
import re, sys, hashlib, argparse

import yaml
from pathlib import Path

NS = "https://w3id.org/specl/ns#"

# Retired in 0.3.0. Every specification now declares its own base. The constant
# survives only so specl-migrate can recognize a graph that predates the change;
# nothing emits it. See NAMESPACE-MIGRATION.md.
LEGACY_SPEC_BASE = "https://w3id.org/specl/spec#"

# The graph contract a consumer can pin against. See
# docs/decisions/0004-graph-contract-version.md and docs/contracts/1.md.
CONTRACT = "https://w3id.org/specl/contract/2"


def header(base: str) -> str:
    return f"""@prefix specl: <{NS}> .
@prefix spec: <{base}> .
@prefix prov: <http://www.w3.org/ns/prov#> .
@prefix dct:  <http://purl.org/dc/terms/> .
@prefix xsd:  <http://www.w3.org/2001/XMLSchema#> .
@prefix rdf:  <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix skos: <http://www.w3.org/2004/02/skos/core#> .

"""


class SpecError(Exception):
    """A source the translator refuses rather than guesses at."""


SPEC_RELATIONS = ("dependsOn", "upstreamOf", "refines")


def check_sections(value, warnings):
    """Headings a project maps onto an existing class, from front matter."""
    if value is None:
        return []
    if not isinstance(value, dict):
        warnings.append("sections: must be a mapping of heading to class; ignored")
        return []
    out = []
    for heading, cls in value.items():
        if cls not in MAPPABLE_CLASSES:
            warnings.append(
                f"sections: {heading!r} maps to {cls!r}, which is not a class specl "
                f"declares; choose one of {sorted(MAPPABLE_CLASSES)}"
            )
            continue
        out.append((str(heading), str(cls), MAPPABLE_CLASSES[cls]))
    return out


def check_vocabularies(value, warnings) -> dict:
    """External vocabularies whose terms this specification governs.

    Separate from `references:` because the two answer different questions. A
    peer specification has items this one may point at and a layering
    relationship; a vocabulary has terms and no layering. Conflating them would
    make `specl-validate layering` try to read an ontology as a specification.
    """
    if value is None:
        return {}
    if not isinstance(value, dict):
        warnings.append("vocabularies: must be a mapping of prefix to base and path; ignored")
        return {}
    out = {}
    for prefix, entry in value.items():
        if isinstance(entry, str):
            entry = {"base": entry}
        if not isinstance(entry, dict) or "base" not in entry:
            warnings.append(f"vocabularies: {prefix!r} declares no base; ignored")
            continue
        base = str(entry["base"])
        if not base.endswith(("#", "/")):
            warnings.append(
                f"vocabularies: {prefix!r} base {base!r} ends in neither '#' nor "
                "'/', so a term concatenated onto it would run into the last "
                "path segment; ignored"
            )
            continue
        out[str(prefix)] = {"base": base, "path": entry.get("path")}
    return out


def check_references(value, warnings) -> dict:
    """The two-level `references:` mapping committed under UR15.

    Each entry names a foreign prefix, the base its items resolve under, and a
    local path to the peer. The base goes through the same grammar as
    `spec_base`: a foreign base becomes part of an IRI this specification emits,
    so it is held to the same standard as its own.
    """
    if value is None:
        return {}
    if not isinstance(value, dict):
        warnings.append("references: must be a mapping of prefix to base and path; ignored")
        return {}
    out = {}
    for prefix, entry in value.items():
        if not isinstance(entry, dict) or "base" not in entry:
            warnings.append(f"references: {prefix!r} declares no base; ignored")
            continue
        try:
            base = check_base(entry["base"])
        except SpecError as exc:
            warnings.append(f"references: {prefix!r} {exc}; ignored")
            continue
        out[str(prefix)] = {"base": base, "path": entry.get("path")}
    return out


def check_item_prefix(value, warnings) -> str | None:
    """A project's own item prefix, accepted in place of the reserved one.

    A register whose clauses are numbered in one sequence across requirements
    and decisions needs its own prefix; the reserved single letters cannot carry
    that. Two characters minimum, so the single-letter space stays reserved, and
    never one of the reserved prefixes itself.
    """
    if not value:
        return None
    if not ITEM_PREFIX_RE.match(value):
        warnings.append(
            f"item_prefix {value!r} must be two or more uppercase ASCII letters; ignored"
        )
        return None
    if value in RESERVED_PREFIXES:
        warnings.append(
            f"item_prefix {value!r} is reserved by specl and cannot be redeclared; ignored"
        )
        return None
    return value


def check_base(value: str | None) -> str:
    """The `spec_base` grammar from docs/DOWNSTREAM-COMMITMENTS.md.

    Every rejection here is a value that would otherwise become a permanent
    identifier. Silently repairing one is the wrong default, so nothing is
    appended, trimmed, or normalized.
    """
    if not value:
        raise SpecError(
            "spec_base is required. It is the namespace this specification's "
            "items are identified under, and it must be one the project "
            "controls, for example https://example.com/specs/thing#. See "
            "https://github.com/zwelz3/specl/blob/main/docs/SYNTAX.md."
        )
    if value.endswith("/"):
        raise SpecError(
            f"spec_base {value!r} is slash terminated. Slash bases are "
            "unsupported until a post-1.0 extension; use a hash base."
        )
    if not value.endswith("#"):
        raise SpecError(
            f"spec_base {value!r} does not end in '#'. The terminator is not "
            "appended for you, because the result becomes a permanent identifier."
        )
    if value.count("#") > 1:
        raise SpecError(
            f"spec_base {value!r} carries a fragment beyond the terminating '#'."
        )
    scheme, sep, rest = value.partition("://")
    if not sep or "/" not in rest.rstrip("#"):
        raise SpecError(
            f"spec_base {value!r} is a bare authority with no path segment. "
            "A path segment keeps a project's specifications distinguishable "
            "from each other and from anything else on the same host."
        )
    return value

# The grammar published in docs/DOWNSTREAM-COMMITMENTS.md: one or more uppercase
# ASCII letters, one or more digits, then zero or more dot-separated digit
# groups. Case sensitive, no normalization. The earlier pattern enumerated four
# prefixes and allowed a single dot group, so R1.2.3, US1.2, and D1.1 were legal
# to anyone reading the register and were dropped by the translator in silence.
BULLET_RE = re.compile(r"^-\s+([A-Z]+\d+(?:\.\d+)*)\.?\s+(.*)")

# A top-level bullet that opens with something identifier-shaped but does not
# parse. Warned rather than dropped: silence is what made P16 invisible.
ITEMISH_RE = re.compile(r"^-\s+([A-Za-z]+[\w.-]*)[.:]?\s")

# Reserved by the commitments register and closed until 0.6.0. A project prefix
# must be at least two characters, which keeps the single-letter space free.
RESERVED_PREFIXES = ("R", "US", "OQ", "D", "DN", "C", "P", "Q", "AG")
ITEM_PREFIX_RE = re.compile(r"^[A-Z]{2,}$")
PREFIX_RE = re.compile(r"^([A-Z]+)(\d+)")
# `status` is context sensitive and maps to two properties depending on the
# item class, so it is not in PROP_MAP and is listed here.
CONTEXTUAL_KEYS = ("status", "decisionStatus", "resolutionStatus")
MULTI_KEYS = {"constrains", "affects", "gates", "governs"}  # comma-split; prose keys use multiple sub-bullets

# An indented bullet that names a known annotation key is an annotation at any
# depth, which keeps every specification authored against "two or more spaces"
# working. A bullet that names no known key is a typo at annotation depth and
# nested content below it. The split is at four columns because that is the
# second markdown nesting level: the author who indents that far has already
# said the line is a child of the annotation level rather than a member of it.
NEST_COLUMNS = 4
# Sentence boundary for the title fallback: a period or semicolon followed by
# whitespace. A dotted identifier such as R1.2 is unaffected, since the dot is
# followed by a digit.
SENTENCE_RE = re.compile(r"[.;]\s")
TITLE_MAX = 80
# The register says "append an ellipsis" without naming a character. One
# codepoint, so a truncated title can never be confused with a sentence that
# happens to end in a period.
ELLIPSIS = "\u2026"

# Keys whose values name something rather than describing it. core.ttl declares
# all three as owl:ObjectProperty, and emitting them as literals is P1: the
# graph contradicts its own ontology and traceability becomes string matching,
# which is what the RDF was meant to replace.
REFERENCE_KEYS = {
    "affects": None,
    "constrains": "Component",
    "verifiedBy": "Test",
    # Item to item only. An external artifact cannot supersede a requirement,
    # so there is no class to mint a node under and a non-identifier value
    # warns rather than becoming a typed node.
    "supersededBy": None,
    # A query gates requirements. Item references only: a query that gates
    # something outside the specification is a layering question, not a node to
    # mint.
    "gates": None,
    # A term in a vocabulary this project does not own. Resolved through
    # `vocabularies:` rather than `references:`, because an ontology has terms
    # rather than items and is not a peer specification.
    "governs": "vocabulary",
    # An identifier, never a name. A persona is declared once and referenced,
    # so two stories about the same person share a node rather than sharing a
    # spelling. The same holds for an accountable agent.
    "role": None,
    "owner": None,
}

# A CURIE, not merely a value containing a colon. A pytest node id such as
# tests/test_x.py::test_y carries colons and is an external artifact path, not a
# reference to another specification.
CURIE_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_-]*:[A-Za-z][A-Za-z0-9_.-]*$")

# An external artifact's IRI is derived from its value: readable when the value
# is safe as a local name, hashed when it is not. Either way it is deterministic
# and it is an IRI, because a blank node's label is regenerated on every parse.
SAFE_LOCAL_RE = re.compile(r"^[A-Za-z0-9_-]+$")

PROP_MAP = {
    "title": "dct:title",
    "priority": "priority", "acceptance": "acceptanceCriterion",
    "verifiedBy": "verifiedBy", "constrains": "constrains",
    "role": "role", "capability": "capability", "benefit": "benefit",
    "altLabel": "skos:altLabel", "prefLabel": "skos:prefLabel",
    "owner": "owner",
    "recommendation": "recommendation", "rationale": "rationale",
    "affects": "affects", "supersededBy": "supersededBy", "gates": "gates",
    "governs": "governs",
    "itemStatus": "itemStatus", "implementation": "implementationStatus",
}

# `status` is context sensitive and maps to two properties depending on the
# item class, so it is not in PROP_MAP and is listed here.
CONTEXTUAL_KEYS = ("status", "decisionStatus", "resolutionStatus")

# Derived, not restated. This list and PROP_MAP were two hardcoded copies of one
# key set, and adding `title` to one and not the other made a valid annotation
# parse as an unknown key. Deriving the pattern makes that drift impossible
# rather than merely detectable.
SUB_RE = re.compile(
    r"^(?:\s{2,}|\t)-\s+("
    + "|".join(sorted(set(PROP_MAP) | set(CONTEXTUAL_KEYS), key=len, reverse=True))
    + r")\s*:\s*(.*)$",
    re.IGNORECASE,
)

FM_COMMENT_RE = re.compile(r"<!--specl\s*(.*?)-->", re.DOTALL)

SECTION_MAP = [
    ("Requirements", "Requirement", ("R",)),
    ("User Stories", "UserStory", ("US",)),
    ("Open Questions and Gaps (flag for follow-up)", "OpenIssue", ("OQ",)),
    # specl_tool heads its own open questions this way, and the section was
    # dropped in silence. Adding the alias is not P7: warning on any unmapped
    # H1 and making the map extensible is 0.6.0.
    ("Open Questions and Gaps", "OpenIssue", ("OQ",)),
    ("Open Questions", "OpenIssue", ("OQ",)),
    ("Open Issues", "OpenIssue", ("OQ",)),
    ("Decisions", "DecisionRecord", ("D",)),
    ("Design Considerations", "DesignNote", ("DN",)),
    ("Comments", "Comment", ("C",)),
    ("Acceptance Queries", "AcceptanceQuery", ("Q",)),
    ("Personas", "Persona", ("P",)),
    ("Agents", "Agent", ("AG",)),
]

# Sections the translator consumes without producing items.
PROSE_SECTIONS = ("Intent", "Purpose")

# Classes a project may map a custom heading onto. Extending the map is not the
# same as inventing a class: an item still has to be something the vocabulary
# declares and the shapes evaluate.
MAPPABLE_CLASSES = {
    "Requirement": ("R",), "UserStory": ("US",), "OpenIssue": ("OQ",),
    "DecisionRecord": ("D",), "AcceptanceQuery": ("Q",),
    "DesignNote": ("DN",), "Comment": ("C",),
}

# A heading deliberately parked because no class models it yet. UR10's
# pre-adoption path: author the content now under a marker, and adoption becomes
# deleting the marker rather than rewriting the section.
# Detected against the raw source, before comment stripping: the document-level
# <!--specl ... --> block would otherwise consume it, and one marker namespace is
# better than two.
PARKED_RE = re.compile(
    r"^#\s+(?P<heading>.+?)\s*$\s*^<!--\s*specl:\s*parked\b[^>]*-->",
    re.I | re.M,
)

# Declares that prose under an item heading is deliberate. Same shape as the
# parked marker, and needed for the same reason: the alternative to a marker is
# a warning nobody can clear.
PROSE_RE = re.compile(
    r"^#\s+(?P<heading>.+?)\s*$\s*^<!--\s*specl:\s*prose\b[^>]*-->",
    re.I | re.M,
)


def derive_title(description: str) -> str:
    """The fallback specified in docs/DOWNSTREAM-COMMITMENTS.md.

    Materialized into the graph rather than computed at validation time,
    because a Violation-severity shape requires the property and a consumer
    reading the graph has to see what the validator saw.
    """
    text = description.strip()
    m = SENTENCE_RE.search(text)
    if m:
        text = text[: m.start()]
    text = text.rstrip().rstrip(".;:").rstrip()
    if len(text) > TITLE_MAX:
        cut = text[:TITLE_MAX].rsplit(" ", 1)[0].rstrip().rstrip(".;:,").rstrip()
        text = (cut or text[:TITLE_MAX].rstrip()) + ELLIPSIS
    return text


def esc(s: str) -> str:
    return s.replace("\\", "\\\\").replace('"', '\\"')


def slug(s: str) -> str:
    return hashlib.sha1(s.encode()).hexdigest()[:8]


def parse(md: str):
    warnings: list[str] = []
    parked = {m.group("heading").strip() for m in PARKED_RE.finditer(md)}
    prose_ok = {m.group("heading").strip() for m in PROSE_RE.finditer(md)}
    front: dict = {}
    if md.startswith("---"):
        end = md.find("---", 3)
        if end > 0:
            # P10. The previous parser assigned every colon-bearing line into
            # one flat dict regardless of indentation, so the committed
            # two-level `references:` mapping parsed to two empty strings and a
            # colliding top-level `base`. It also stripped brackets off values,
            # implying list parsing that never happened.
            try:
                loaded = yaml.safe_load(md[3:end]) or {}
            except yaml.YAMLError as exc:
                raise SpecError(f"front matter is not valid YAML: {exc}") from exc
            if not isinstance(loaded, dict):
                raise SpecError("front matter must be a mapping")
            front = loaded
            consumed = md[: end + 3]
            md = "\n" * consumed.count("\n") + md[end + 3:]
        else:
            warnings.append("YAML front-matter opened with --- but never closed")

    fm_comments: dict[str, str] = {}
    for m in FM_COMMENT_RE.finditer(md):
        for line in m.group(1).strip().splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                fm_comments[k.strip()] = v.strip()
    md = FM_COMMENT_RE.sub(lambda m: "\n" * m.group(0).count("\n"), md)

    sections: dict[str, list[str]] = {}
    starts: dict[str, int] = {}
    cur = None
    for n, line in enumerate(md.splitlines(), start=1):
        if line.startswith("# "):
            cur = line[2:].strip()
            sections[cur] = []
            starts[cur] = n
        elif cur is not None:
            sections[cur].append(line)
    return front, sections, fm_comments, warnings, parked, starts, prose_ok


def parse_bullets(lines, warnings, section_name="", start=0):
    """Items, each carrying the line it was authored on.

    The line indexes the file as authored, which is why parse blanks the front
    matter and comment blocks rather than slicing them out: a source reference
    that points at the wrong line is worse than none.
    """
    items = []
    current = None
    for offset, raw in enumerate(lines, start=start + 1):
        if raw.startswith("- "):
            bm = BULLET_RE.match(raw)
            if bm:
                if current:
                    items.append(current)
                current = (bm.group(1), bm.group(2).strip(), {}, [], offset)
                continue
            if ITEMISH_RE.match(raw):
                where = f" in '{section_name}'" if section_name else ""
                warnings.append(
                    f"bullet{where} looks like an item and does not match the "
                    f"identifier grammar, so it was dropped: {raw.strip()[:70]!r}"
                )
                continue
        sm = SUB_RE.match(raw)
        if sm:
            if current is None:
                warnings.append(f"sub-bullet with no parent: {raw.strip()!r}")
                continue
            key = sm.group(1)
            for canon in PROP_MAP:
                if canon.lower() == key.lower():
                    key = canon
                    break
            val = sm.group(2).strip()
            if key in MULTI_KEYS:
                vals = [v.strip() for v in val.split(",") if v.strip()]
            else:
                vals = [val] if val else []
            current[2].setdefault(key, []).extend(vals)
            continue
        stripped = raw.strip()
        if stripped.startswith("- ") and current and raw[:1] in (" ", "\t"):
            expanded = raw.expandtabs(4)
            columns = len(expanded) - len(expanded.lstrip())
            if columns >= NEST_COLUMNS:
                current[3].append(stripped[2:].strip())
            else:
                warnings.append(
                    f"sub-bullet did not match known annotation key: {stripped!r}"
                )
    if current:
        items.append(current)
    return items


def resolve_reference(key, value, known_ids, warnings, context, references=None,
                      vocabularies=None):
    """Turn one reference-valued annotation into a Turtle object term.

    Three outcomes, in the order the commitments register specifies them.

    A token matching the identifier grammar resolves against the specification's
    own base by concatenation, and warns if nothing in the specification carries
    that identifier. A dangling reference is the check this exists for: it
    catches a decision pointing at a renumbered or deleted requirement.

    A prefixed token such as `SBL:D14` is illegal until cross-specification
    references arrive in 0.5.0. There is no prefix map before then, so accepting
    the syntax early would mint a wrong IRI.

    Anything else names something outside the specification, a component or a
    test. It becomes a typed node rather than a literal, so the property keeps
    its declared range. The node's IRI is derived from the value, not a blank
    node: blank node labels are regenerated on every parse.
    """
    token = value.strip()

    # A governed term is a vocabulary term, never an item, so it resolves
    # against the vocabulary map alone. Falling through to the identifier
    # grammar would silently turn `governs: Holon` into a reference to a
    # requirement that happens to be called Holon.
    if REFERENCE_KEYS.get(key) == "vocabulary":
        prefix, sep, local = token.partition(":")
        entry = (vocabularies or {}).get(prefix) if sep else None
        if entry:
            return f"<{entry['base']}{local}>", None
        if token.startswith(("http://", "https://")):
            return f"<{token}>", None
        warnings.append(
            f"{context}: {key} value {token!r} names no declared vocabulary. "
            "Declare the prefix under vocabularies: in front matter, or give an "
            "absolute IRI; emitted as a literal rather than a guessed one"
        )
        return f'"{esc(token)}"', None

    # An absolute IRI is already unambiguous, so it is used as written. It fell
    # through to node minting before, which hashed it into a local
    # `component-<digest>` and discarded the identity the author had supplied.
    #
    # This is what gives a specification family one node per shared component
    # without a name-to-IRI map: three specifications naming the same IRI name
    # the same node. The map deferred to 2.0 is an abbreviation of this, and
    # because these IRIs are the project's own, adopting it later moves nothing.
    if token.startswith(("http://", "https://")):
        return f"<{token}>", None

    if BULLET_RE.match(f"- {token} x"):
        if known_ids is not None and token not in known_ids:
            warnings.append(
                f"{context}: {key} references {token!r}, which no item in this "
                "specification declares"
            )
        return f"spec:{token}", None
    if CURIE_RE.match(token):
        prefix, _, local = token.partition(":")
        if prefix in (vocabularies or {}):
            warnings.append(
                f"{context}: {key} value {token!r} names a term in the "
                f"vocabulary {prefix!r}, not a peer specification. Use "
                "'governs:' for a vocabulary term; 'constrains:' names a "
                "software component and keeps specl:Component as its range"
            )
            return f'"{esc(token)}"', None
        entry = (references or {}).get(prefix)
        if entry:
            # UR15: references resolve to IRIs always. Whether the peer actually
            # declares the item is a layering question, checked against the peer
            # rather than guessed at here.
            #
            # A prefix declared here names a peer specification. Using one for a
            # shared component namespace resolves, and then pins
            # specl-validate layering to inconclusive forever, because layering
            # tries to read the peer as a specification. Absolute IRIs are the
            # sanctioned way to share a component across specifications.
            if key in ("constrains", "verifiedBy") and not entry.get("path"):
                warnings.append(
                    f"{context}: {key} resolves {token!r} against the "
                    f"specification reference {prefix!r}, which declares no "
                    "path. If this names a shared component rather than an item "
                    "in a peer specification, write the absolute IRI instead: a "
                    "reference prefix makes layering inconclusive"
                )
            return f"<{entry['base']}{local}>", None
        warnings.append(
            f"{context}: {key} value {token!r} uses prefix {prefix!r}, which this "
            "specification does not declare under references:; emitted as a "
            "literal rather than a guessed IRI"
        )
        return f'"{esc(token)}"', None
    cls = REFERENCE_KEYS.get(key)
    if cls is None:
        warnings.append(
            f"{context}: {key} value {token!r} does not match the identifier "
            "grammar and names no external artifact type; emitted as a literal"
        )
        return f'"{esc(token)}"', None
    local = token if SAFE_LOCAL_RE.match(token) else slug(token)
    iri = f"spec:{cls.lower()}-{local}"
    node = f'{iri} a specl:{cls} ;\n    dct:identifier "{esc(token)}" .\n'
    return iri, node


def _warn_on_mixed_padding(items, section_name, warnings):
    """`D1` and `D01` are distinct identifiers and the register says so.

    No normalization, because normalizing silently merges two items. Mixing the
    two forms under one prefix is almost always a typo, so it warns.
    """
    seen: dict[str, set[bool]] = {}
    for item_id, *_ in items:
        m = PREFIX_RE.match(item_id)
        if m:
            seen.setdefault(m.group(1), set()).add(
                len(m.group(2)) > 1 and m.group(2).startswith("0")
            )
    for prefix, forms in sorted(seen.items()):
        if len(forms) > 1:
            warnings.append(
                f"'{section_name}' mixes padded and unpadded ordinals under "
                f"prefix {prefix!r}; these are distinct identifiers and are not merged"
            )


def _emit_item(iri, cls, description, annotations, spec_iri, details=(),
               known_ids=None, warnings=None, externals=None, references=None,
               source=None, line=None, vocabularies=None):
    supplied = annotations.pop("title", None)
    title = supplied[0] if supplied else derive_title(description)
    body = [f"{iri} a specl:{cls} ;",
            f"    specl:partOf {spec_iri} ;",
            f'    dct:title "{esc(title)}" ;',
            f'    dct:description "{esc(description)}"']
    triples = []
    cells = []
    if source and line:
        # P9. The prov: prefix was bound and never used. A source reference the
        # reader can act on is a document and a line, not a document alone.
        triples.append(f"    prov:wasDerivedFrom {source}")
        triples.append(f'    specl:sourceLine "{line}"^^xsd:integer')
    if details:
        # An rdf:List, with the cons cells given derived IRIs rather than blank
        # nodes. Blank node labels are regenerated on every parse, which would
        # make specl-validate diff report every item carrying detail as
        # modified against itself.
        triples.append(f"    specl:detail {iri}-detail-1")
        for n, line in enumerate(details, start=1):
            rest = f"{iri}-detail-{n + 1}" if n < len(details) else "rdf:nil"
            cells.append(
                f"{iri}-detail-{n}\n"
                f'    rdf:first "{esc(line)}" ;\n'
                f"    rdf:rest  {rest} .\n"
            )
    for key, values in annotations.items():
        if key in CONTEXTUAL_KEYS:
            # P11. `status:` remains accepted and still resolves by class, but
            # the explicit keys say which property they mean, so a bullet moved
            # between sections does not silently change what it asserts.
            if key in ("decisionStatus", "resolutionStatus"):
                prop = key
            else:
                prop = "decisionStatus" if cls == "DecisionRecord" else "resolutionStatus"
        else:
            prop = PROP_MAP.get(key)
        if not prop:
            continue
        for v in values:
            qualified = prop if ":" in prop else f"specl:{prop}"
            if key in REFERENCE_KEYS:
                term, node = resolve_reference(
                    key, v, known_ids, warnings if warnings is not None else [],
                    iri.lstrip("<").rstrip(">"), references, vocabularies,
                )
                if node and externals is not None:
                    externals[node.split("\n")[0].split(" ")[0]] = node
                triples.append(f"    {qualified} {term}")
            else:
                triples.append(f'    {qualified} "{esc(v)}"')
    if triples:
        body[-1] = body[-1] + " ;"
        for i, t in enumerate(triples):
            body.append(t + (" ." if i == len(triples) - 1 else " ;"))
    else:
        body[-1] = body[-1] + " ."
    return "\n".join(body) + "\n\n" + "\n".join(cells) + ("\n" if cells else "")


def load_documents(root: Path, warnings):
    """The root specification and its companions, in declared order.

    A companion carries sections and no front matter of its own: one
    specification has one identity, and a second `spec_base` in a companion
    would be a second answer to a settled question. Each document is identified
    by its path relative to the root, so two files named `spec.md` in different
    directories do not collide and no identifier depends on the working
    directory.
    """
    documents = []
    front, sections, fm, warnings_root, parked, starts, prose_ok = parse(
        root.read_text(encoding="utf-8")
    )
    warnings.extend(warnings_root)
    documents.append((root.name, sections, starts, parked, prose_ok))

    declared = front.get("companion_files") or []
    if isinstance(declared, str):
        declared = [declared]
    for rel in declared:
        path = (root.parent / str(rel)).resolve()
        if not path.exists():
            raise SpecError(
                f"companion_files names {rel!r}, which does not exist relative to "
                f"{root.name}. A specification missing part of itself is not a "
                "specification with a warning; it is a different specification."
            )
        c_front, c_sections, c_fm, c_warnings, c_parked, c_starts, c_prose = parse(
            path.read_text(encoding="utf-8")
        )
        warnings.extend(f"{rel}: {w}" for w in c_warnings)
        for key in ("spec_base", "spec_id", "prefix", "item_prefix", "companion_files"):
            if key in c_front:
                warnings.append(
                    f"{rel}: companion declares {key!r} in front matter, which is "
                    "ignored. One specification has one identity, declared in the "
                    "root file."
                )
        fm.update(c_fm)
        documents.append((str(rel), c_sections, c_starts, c_parked, c_prose))
    return front, documents, fm


def emit(front, sections, fm_comments, warnings, parked=(), starts=None, source=None,
         generated_at=None, documents=None):
    base = check_base(front.get("spec_base"))
    out = [header(base)]

    # The Specification is the base without its terminator, and its items are
    # fragments under it. This is the hash-namespace pattern OWL uses for an
    # ontology IRI, and it is what core.ttl already does for the vocabulary.
    # See docs/decisions/0004-graph-contract-version.md.
    spec_iri = f"<{base[:-1]}>"

    identifier = front.get("spec_id")

    # `prefix` is how another specification refers to this one. `item_prefix` is
    # the prefix this specification's own item identifiers carry, in place of
    # the reserved one its section would otherwise require. Two different jobs,
    # and confusing them mints the wrong IRI.
    prefix = front.get("prefix")
    item_prefix = check_item_prefix(front.get("item_prefix"), warnings)
    references = check_references(front.get("references"), warnings)
    vocabularies = check_vocabularies(front.get("vocabularies"), warnings)
    for shared in sorted(set(references) & set(vocabularies)):
        warnings.append(
            f"prefix {shared!r} is declared as both a specification reference "
            "and a vocabulary; the vocabulary declaration is ignored"
        )
        vocabularies.pop(shared)
    section_map = SECTION_MAP + check_sections(front.get("sections"), warnings)

    # P7. A heading nothing recognizes used to drop its content in silence.
    # One source node per document. 0.7.0 emitted one because there was one
    # file; the shape did not have to change to hold several.
    docs = documents if documents is not None else [
        (source, sections, starts or {}, set(parked), set())
    ]
    source_nodes = {
        name: f"spec:source-{slug(name)}" for name, *_ in docs if name
    }
    source_block = "".join(
        f"{node} a specl:SourceDocument ;\n"
        f'    dct:identifier "{esc(name)}" .\n\n'
        for name, node in sorted(source_nodes.items())
    )

    known = {name for name, *_ in section_map} | set(PROSE_SECTIONS)
    # Prose under a heading that models items is consumed and produces nothing.
    # Two warnings already cover the adjacent cases, a bullet that looks like an
    # item and does not parse, and an unrecognized heading, and neither fires
    # here because the heading is recognized and the content is not a bullet.
    #
    # A downstream migration lost three paragraphs this way with zero parser
    # warnings, so `--fail-on-warning` passed over silent content loss. Under
    # 0.2.0 those paragraphs became content-hash design notes, which makes it a
    # regression across a version boundary that `specl-validate diff` could not
    # see either, because the namespace changed in the same step.
    item_sections = {name: cls for name, cls, prefixes in section_map if prefixes}
    for doc_name, doc_sections, doc_starts, _, doc_prose in docs:
        for name, lines in doc_sections.items():
            if name not in item_sections or name in doc_prose:
                continue
            # A subheading organises a long section into groups and is not
            # lost content. specl's own specifications use them heavily, and
            # flagging them would have made this warning noise on the first run.
            orphan = next(
                (line.strip() for line in lines
                 if line.strip()
                 and not line.lstrip().startswith(("-", "*", "#"))),
                None,
            )
            if orphan is None:
                continue
            where = f"{doc_name}: " if doc_name else ""
            warnings.append(
                f"{where}section '{name}' contains prose that produced no "
                f"{item_sections[name]}, starting {orphan[:60]!r}. Make it a "
                "bullet with an identifier, or mark the section "
                "<!--specl: prose--> if the text is deliberate"
            )

    for doc_name, doc_sections, _, doc_parked, _prose in docs:
        for name in doc_sections:
            if name in known or name in doc_parked:
                continue
            where = f"{doc_name}: " if doc_name else ""
            warnings.append(
                f"{where}section '{name}' is not a recognized heading and its "
                "content was dropped. Map it with a sections: entry in front "
                "matter, or mark it <!--specl: parked--> if no class models it yet"
            )
    if prefix and len(prefix) < 2:
        warnings.append(
            f"prefix {prefix!r} is shorter than two characters; the "
            "single-character space is reserved for item prefixes"
        )
    # Emitted only when the specification supplies it. Stamping translation time
    # made output differ across days, which no golden file survives, and the
    # value was wrong on its face: it recorded when the translator ran rather
    # than anything about the specification.
    created = fm_comments.get("created")
    # Prose sections concatenate across documents in declared order, so a
    # specification split into parts reads as one.
    def prose(name):
        return " ".join(
            line for _, doc_sections, _, _, _ in docs
            for line in doc_sections.get(name, [])
        ).strip()

    intent = prose("Intent")
    purpose = prose("Purpose")
    optional = ""
    if identifier:
        optional += f'    dct:identifier "{esc(identifier)}" ;\n'
    if prefix:
        optional += f'    specl:prefix "{esc(prefix)}" ;\n'
    if item_prefix:
        optional += f'    specl:itemPrefix "{esc(item_prefix)}" ;\n'
    if created:
        optional += f'    dct:created "{created}"^^xsd:date ;\n'

    relations = ""
    reference_nodes = []
    for prefix, entry in sorted(vocabularies.items()):
        node = f"spec:vocabulary-{prefix}"
        reference_nodes.append(
            f"{node} a specl:Vocabulary ;\n"
            f'    specl:prefix "{esc(prefix)}" ;\n'
            f'    specl:referenceBase "{esc(entry["base"])}"'
            + (f' ;\n    specl:referencePath "{esc(entry["path"])}"' if entry.get("path") else "")
            + " .\n"
        )
        relations += f"    specl:declaresVocabulary {node} ;\n"
    for prefix, entry in sorted(references.items()):
        node = f"spec:reference-{prefix}"
        reference_nodes.append(
            f"{node} a specl:SpecificationReference ;\n"
            f'    specl:prefix "{esc(prefix)}" ;\n'
            f'    specl:referenceBase "{esc(entry["base"])}"'
            + (f' ;\n    specl:referencePath "{esc(entry["path"])}"' if entry.get("path") else "")
            + " .\n"
        )
        relations += f"    specl:declares {node} ;\n"
    for relation in SPEC_RELATIONS:
        declared = front.get(relation)
        if not declared:
            continue
        for peer in (declared if isinstance(declared, list) else [declared]):
            entry = references.get(str(peer))
            if not entry:
                warnings.append(
                    f"{relation}: {peer!r} is not declared under references:; ignored"
                )
                continue
            relations += f"    specl:{relation} <{entry['base'][:-1]}> ;\n"

    out.append(f"{spec_iri} a specl:Specification ;\n" + relations + f"""    dct:conformsTo <{CONTRACT}> ;
    dct:title "{esc(front.get('title', 'Untitled'))}" ;
    dct:hasVersion "{front.get('version', '0.1.0')}" ;
    specl:status "{front.get('status', 'draft')}" ;
{optional}    specl:intent \"\"\"{esc(intent)}\"\"\" ;
    specl:purpose \"\"\"{esc(purpose)}\"\"\" .

""")
    if generated_at:
        # A translation activity, not a property of the specification. The
        # timestamp is supplied rather than read from the clock: exit criterion
        # 6 for 0.3.0 is that the same source produces byte-identical output,
        # and a translator that reads the clock breaks that and every golden
        # file with it. Recording when a graph was produced is a deliberate act
        # by the caller, which is the same reason a code fingerprint cannot be
        # computed at translation time either.
        out.append(
            f"{spec_iri} prov:wasGeneratedBy spec:translation .\n\n"
            f"spec:translation a prov:Activity ;\n"
            f'    prov:generatedAtTime "{esc(generated_at)}"^^xsd:dateTime .\n\n'
        )
    if source_block:
        out.append(source_block)
    out.extend(reference_nodes)
    if reference_nodes:
        out.append("\n")
    parsed_sections = []
    known_ids = set()
    for section_name, cls, prefixes in section_map:
        if prefixes is None:
            continue
        for doc_name, doc_sections, doc_starts, _, _ in docs:
            lines = doc_sections.get(section_name)
            if not lines:
                continue
            parsed = parse_bullets(
                lines, warnings, section_name, doc_starts.get(section_name, 0)
            )
            _warn_on_mixed_padding(parsed, section_name, warnings)
            known_ids.update(item_id for item_id, *_ in parsed)
            parsed_sections.append((section_name, cls, prefixes, parsed, doc_name))

    externals: dict[str, str] = {}
    for section_name, cls, prefixes in section_map:
        if prefixes is None:
            for doc_name, doc_sections, doc_starts, _, _ in docs:
                lines = doc_sections.get(section_name)
                if not lines:
                    continue
                node = source_nodes.get(doc_name)
                base_line = doc_starts.get(section_name, 0)
                for offset, line in enumerate(lines, start=base_line + 1):
                    t = line.strip().lstrip("-0123456789. ").strip()
                    if not t:
                        continue
                    iri = f"spec:{cls.lower()}-{slug(t)}"
                    out.append(
                        _emit_item(iri, cls, t, {}, spec_iri, (), None, warnings,
                                   None, None, node, offset)
                    )
            continue
        for entry in [p for p in parsed_sections if p[0] == section_name]:
            _, _, _, parsed, doc_name = entry
            source_node = source_nodes.get(doc_name)
            for item_id, desc, annotations, details, line in parsed:
                allowed = prefixes + ((item_prefix,) if item_prefix else ())
                if not any(item_id.startswith(p) for p in allowed):
                    warnings.append(
                        f"{item_id} in '{section_name}' does not match prefix {allowed}"
                    )
                out.append(
                    _emit_item(
                        f"spec:{item_id}", cls, desc, annotations, spec_iri, details,
                        known_ids, warnings, externals, references, source_node,
                        line, vocabularies,
                    )
                )

    # Component and Test nodes, once each however many items reference them.
    for node in sorted(externals.values()):
        out.append(node + "\n")
    return "".join(out)


def main():
    ap = argparse.ArgumentParser(prog="specl-translate")
    ap.add_argument("src")
    ap.add_argument("dst")
    ap.add_argument("--strict", action="store_true",
                    help="accepted for compatibility; warnings now print by default")
    ap.add_argument("--fail-on-warning", action="store_true",
                    help="exit non-zero if the parser produced any warning")
    ap.add_argument("--generated-at", metavar="ISO8601",
                    help="record a translation activity with this timestamp. "
                         "Supplied rather than read from the clock, so that "
                         "translation stays a pure function of its source and "
                         "output remains byte-identical across runs.")
    args = ap.parse_args()
    warnings: list[str] = []
    try:
        # Documents are identified by path relative to the root, not by the
        # path given on the command line: a graph must not differ because it was
        # translated from a different working directory.
        front, documents, fm = load_documents(Path(args.src), warnings)
        turtle = emit(front, None, fm, warnings, generated_at=args.generated_at,
                      documents=documents)
    except SpecError as exc:
        # A rejected source produces no output at all. A warning describes
        # something the parser dropped; this describes a value that would have
        # become a permanent identifier, and writing a graph from it would put
        # the wrong IRI somewhere before anyone read the message.
        print(f"error: {args.src}: {exc}", file=sys.stderr)
        return 2

    # The output is written either way. A warning describes something the parser
    # dropped or could not interpret, and reading the emitted graph is how you
    # see what that cost.
    Path(args.dst).write_text(turtle, encoding="utf-8")
    print(f"wrote {args.dst} ({len(warnings)} parser warning(s))")

    if not warnings:
        return 0

    # Warnings print unconditionally. A warning that only appears behind a flag
    # is one nobody reads.
    for w in warnings:
        print(f"warning: {w}", file=sys.stderr)
    count = f"{len(warnings)} parser warning(s) in {args.src}"
    if args.fail_on_warning:
        print(f"{count}: failing because --fail-on-warning is set", file=sys.stderr)
        return 1
    print(f"{count}: not gating (pass --fail-on-warning to make these an error)",
          file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
