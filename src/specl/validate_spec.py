"""validate_spec.py — validate, diff, score, and badge the SPECL spec.

Usage:
  python validate_spec.py validate spec.ttl shapes.ttl [--explain] [--json out.json]
  python validate_spec.py diff old.ttl new.ttl
  python validate_spec.py score spec.ttl shapes.ttl
  python validate_spec.py badge spec.ttl shapes.ttl --out badge.svg

Severity gate is driven by specl:status in the data graph:
  draft|prototype -> fail only on Violations
  review          -> report Warnings, do not fail
  production      -> fail on Warnings too
"""
from __future__ import annotations
import datetime as _dt
from importlib.resources import files
import re
import sys, json, argparse
from pathlib import Path
from rdflib.collection import Collection
from rdflib import Graph, Literal, Namespace, RDF, RDFS
from pyshacl import validate

SPECL = Namespace("https://w3id.org/specl/ns#")
PROV = Namespace("http://www.w3.org/ns/prov#")
SH = Namespace("http://www.w3.org/ns/shacl#")

def load(p): g = Graph(); g.parse(p, format="turtle"); return g


def bundled_shapes() -> str:
    """The shapes that ship with the package.

    OQ2 in specl's own specification, recommended for 0.3.0 and never
    implemented. It surfaced in a fresh-install walkthrough: `specl-validate
    validate spec.ttl` was the first command an adopter runs and it failed,
    because the shapes path was required and nothing tells someone who pip
    installed the package where the bundled file lives.
    """
    return str(files("specl") / "shapes.ttl")

def spec_status(g):
    for s in g.subjects(RDF.type, SPECL.Specification):
        v = g.value(s, SPECL.status)
        if v: return str(v).lower()
    return "draft"

# A SPARQL-based target that must fire. If the processor applies SHACL Advanced
# Features it reports one violation; if it does not, it reports nothing and says
# so about a graph that plainly fails.
_AF_PROBE_DATA = """@prefix ex: <http://specl.invalid/probe#> . ex:a ex:p 1 ."""
_AF_PROBE_SHAPES = """
@prefix sh: <http://www.w3.org/ns/shacl#> .
@prefix ex: <http://specl.invalid/probe#> .
ex:ProbeShape a sh:NodeShape ;
    sh:target [ a sh:SPARQLTarget ;
        sh:select "SELECT ?this WHERE { ?this <http://specl.invalid/probe#p> ?o }" ] ;
    sh:property [ sh:path ex:absent ; sh:minCount 1 ; sh:severity sh:Violation ] .
"""
_advanced_features_checked = None


def assert_advanced_features():
    """Refuse to validate with a processor that would silently under-report.

    SHACL makes SPARQL-based targets and constraints optional, and these shapes
    lean on them: a processor without them reports none of the findings and
    calls the graph conforming. That failure is silent by construction, so it is
    turned into a loud one here rather than left for a consumer to discover by
    trusting a clean result.

    Costs about thirty milliseconds, once per process.
    """
    global _advanced_features_checked
    if _advanced_features_checked is None:
        conforms, _, _ = validate(
            Graph().parse(data=_AF_PROBE_DATA, format="turtle"),
            shacl_graph=Graph().parse(data=_AF_PROBE_SHAPES, format="turtle"),
            inference="none", advanced=True,
        )
        _advanced_features_checked = not conforms
    if not _advanced_features_checked:
        raise SystemExit(
            "error: this SHACL processor does not apply SHACL Advanced "
            "Features. specl's shapes use SPARQL-based targets and "
            "constraints, so validation would report almost nothing and call "
            "the result clean. Refusing to validate rather than report a "
            "misleading pass. Run 'specl-validate conformance' for detail."
        )


def run_shacl(data_g, shapes_g):
    """Validate, with the vocabulary available to the shapes.

    A shape that consults the class hierarchy runs its SPARQL against the data
    graph, so the vocabulary has to be there: the disjointness check silently
    found nothing until `core.ttl` was mixed in. `ont_graph` is how pyshacl does
    that, and `shapes.ttl` declares the same dependency as `owl:imports` for
    processors that resolve it themselves.

    `advanced=True` is not optional here. These shapes use SPARQL-based targets
    and constraints, which SHACL makes an optional feature: without it, nineteen
    of the twenty findings on specl's own specification disappear rather than
    erroring.
    """
    assert_advanced_features()
    conforms, report_g, _ = validate(data_g, shacl_graph=shapes_g,
                                     ont_graph=Graph().parse(files("specl") / "core.ttl"),
                                     inference="none", advanced=True)
    results = []
    for r in report_g.subjects(RDF.type, SH.ValidationResult):
        results.append({
            "severity": str(report_g.value(r, SH.resultSeverity)).split("#")[-1],
            "focus": str(report_g.value(r, SH.focusNode)),
            "path": str(report_g.value(r, SH.resultPath) or ""),
            "message": str(report_g.value(r, SH.resultMessage) or ""),
        })
    return conforms, results, report_g

def gate(status, results):
    v = [r for r in results if r["severity"] == "Violation"]
    w = [r for r in results if r["severity"] == "Warning"]
    fail = bool(v) or (status == "production" and bool(w))
    return fail, v, w

def cmd_validate(args):
    g, s = load(args.data), load(args.shapes)
    status = spec_status(g)
    _, results, _ = run_shacl(g, s)
    fail, v, w = gate(status, results)
    print(f"Spec status: {status}")
    print(f"Violations: {len(v)}   Warnings: {len(w)}")
    if args.explain:
        for r in v + w:
            print(f"  [{r['severity']}] {r['focus']} {r['path']}")
            print(f"      -> {r['message']}")
    if args.json:
        with open(args.json, "w", encoding="utf-8") as fp:
            json.dump({"status": status, "results": results}, fp, indent=2)
    sys.exit(1 if fail else 0)

def _flatten(g, o):
    """Compare list contents rather than the node that heads the list.

    A list head is a node, and comparing nodes compares identity. Two graphs
    carrying the same detail lines under different head IRIs are the same
    specification, and a graph reparsed from blank-node syntax gets fresh
    labels every time. Either would report as modified against itself.
    """
    if (o, RDF.first, None) in g:
        return " | ".join(str(x) for x in Collection(g, o))
    return str(o)


def spec_base(g):
    """The base a graph's items sit under: the Specification IRI plus '#'."""
    for s in g.subjects(RDF.type, SPECL.Specification):
        return str(s) + "#"
    return None


def _req_map(g, ignore_base=False):
    """Requirements keyed by IRI, or by identifier token when bases differ.

    0.3.0 moved every item onto a per-specification base, so diffing a
    pre-migration graph against a post-migration one reports every requirement
    as removed and re-added when the content is identical. --ignore-base keys by
    the token instead, which is what the reader is comparing.
    """
    base = spec_base(g) if ignore_base else None
    out = {}
    for r in g.subjects(RDF.type, SPECL.Requirement):
        key = str(r)
        if base and key.startswith(base):
            key = key[len(base):]
        elif ignore_base:
            key = key.split("#")[-1]
        out[key] = {
            str(p).split("#")[-1]: _flatten(g, o) for p, o in g.predicate_objects(r)
        }
    return out

def _withdrawn(g, ignore_base=False):
    base = spec_base(g) if ignore_base else None
    out = set()
    for item in g.subjects(SPECL.itemStatus, None):
        if str(g.value(item, SPECL.itemStatus)) != "withdrawn":
            continue
        key = str(item)
        if base and key.startswith(base):
            key = key[len(base):]
        elif ignore_base:
            key = key.split("#")[-1]
        out.add(key)
    return out


def cmd_diff(args):
    ignore = getattr(args, "ignore_base", False)
    old, new = _req_map(load(args.old), ignore), _req_map(load(args.new), ignore)
    added = sorted(set(new) - set(old))
    removed = sorted(set(old) - set(new))
    changed = []
    for k in set(old) & set(new):
        if old[k] != new[k]:
            kind = "tightened" if "priority" in new[k] and "priority" not in old[k] else "changed"
            changed.append((k, kind))
    print(f"+ added:    {len(added)}")
    for k in added: print(f"    + {k}")
    print(f"- removed:  {len(removed)}")
    for k in removed: print(f"    - {k}")
    print(f"~ modified: {len(changed)}")
    for k, kind in changed: print(f"    ~ {k}  [{kind}]")

    # A withdrawn identifier is permanently reserved. Reuse is a violation
    # rather than a warning, and it is only visible across two graphs: a single
    # graph cannot see that an identifier used to mean something else.
    revived = sorted(
        k for k in _withdrawn(load(args.old), ignore)
        if k in new and new[k].get("itemStatus") != "withdrawn"
    )
    if revived:
        print(f"! reused:   {len(revived)}")
        for k in revived:
            print(f"    ! {k}  [withdrawn identifier reused]")
    # P12. Writing was unconditional and went to the working directory, so
    # read-only inspection left a file behind and running twice duplicated the
    # entry. Opt-in, and the path is the caller's choice.
    if getattr(args, "changelog", None):
        with open(args.changelog, "a", encoding="utf-8") as fp:
            fp.write(f"\n## diff {args.old} -> {args.new}\n")
            for k in added: fp.write(f"- added {k}\n")
            for k in removed: fp.write(f"- removed {k}\n")
            for k, kind in changed: fp.write(f"- {kind} {k}\n")
            for k in revived: fp.write(f"- REUSED withdrawn identifier {k}\n")
        print(f"appended to {args.changelog}")
    if revived:
        sys.exit(1)

def item_classes():
    """Read from the vocabulary rather than restated here.

    This was a hardcoded tuple, and it was already wrong: AcceptanceQuery
    arrived in 0.6.0 and Persona in 0.11.0, and neither was added, so neither
    counted toward maturity. A list of classes maintained beside the vocabulary
    is one more pair that can disagree, and this one did.
    """
    core = Graph().parse(files("specl") / "core.ttl")
    return tuple(sorted(
        core.subjects(RDFS.subClassOf, SPECL.Item), key=str
    ))


ITEM_CLASSES = item_classes()


RETIRED = ("superseded", "withdrawn")


def items(g, include_retired=False):
    """The items a measurement is computed over.

    Retired items are excluded. The shapes stop evaluating them, so leaving them
    in the population counted every one as clean and retiring a requirement
    raised the maturity score: found by adding a withdrawn requirement to a
    trial specification and watching it go from 90% to 91%. A metric that
    rewards striking things out measures the wrong thing.
    """
    found = {s for cls in ITEM_CLASSES for s in g.subjects(RDF.type, cls)}
    if include_retired:
        return found
    return {
        i for i in found
        if str(g.value(i, SPECL.itemStatus) or "active") not in RETIRED
    }


# A clean MUST and a clean COULD do not contribute equally, and an unclean MUST
# costs more than an unclean WONT. Deferred since 0.2.0.
PRIORITY_WEIGHT = {"MUST": 4, "SHOULD": 3, "COULD": 2, "WONT": 1}
DEFAULT_WEIGHT = 2

# How much of an item is built. Ordered, so progress is a mean of positions
# rather than a count of one state.
IMPLEMENTATION_SCALE = ["not-started", "in-progress", "implemented", "verified"]


def _weight(g, item):
    priority = g.value(item, SPECL.priority)
    return PRIORITY_WEIGHT.get(str(priority).upper(), DEFAULT_WEIGHT) if priority else DEFAULT_WEIGHT


# An open issue is settled when someone has decided something about it. Both of
# these are decisions: `resolved` answers the question, `deferred` decides not to
# answer it yet. Treating a deferral as unanswered penalised recording a known
# unknown, so a specification that never asked the question scored higher than
# one that asked and deliberately postponed. That is the same perverse incentive
# as the retired-item bug, where striking something out raised the score.
#
# A deferral still has to be a real decision. The shapes want an owner and a
# recommendation on an open issue, so a `deferred` item carrying neither is
# flagged there and counts unclean anyway; nothing extra is needed here.
SETTLED_ISSUE_STATUSES = ("resolved", "deferred")

# `open` and `in-review` are the unsettled half of the same enum. Named rather
# than inferred, so the two halves stay checkable against `shapes.ttl`, which
# had been permitting values this function rejected and rejecting one it
# permitted.
UNSETTLED_ISSUE_STATUSES = ("open", "in-review")


def _unresolved_issue(g, item):
    """An open issue nobody has decided anything about is never clean.

    A specification cannot be fully mature while carrying unanswered questions,
    and the previous metric could not see this at all: it counted requirements
    only, so a specification with no open issues and one with a dozen
    unanswered ones scored identically.
    """
    if (item, RDF.type, SPECL.OpenIssue) not in g:
        return False
    status = g.value(item, SPECL.resolutionStatus)
    return status is None or str(status).lower() not in SETTLED_ISSUE_STATUSES


# Progress is asked only of what gets built. A decision record, a persona, or an
# open question has no implementation, and counting them as not-started made a
# specification look less built the more thinking it recorded.
IMPLEMENTABLE = ("Requirement", "UserStory")


def progress_graph(g):
    """How much is built, rolled up from items rather than declared."""
    implementable = {SPECL[c] for c in IMPLEMENTABLE}
    scored = []
    for item in items(g):
        if not (set(g.objects(item, RDF.type)) & implementable):
            continue
        declared = g.value(item, SPECL.implementationStatus)
        name = str(declared) if declared else "not-started"
        if name in IMPLEMENTATION_SCALE:
            scored.append(IMPLEMENTATION_SCALE.index(name))
    if not scored:
        return None
    top = len(IMPLEMENTATION_SCALE) - 1
    return round(100 * sum(scored) / (len(scored) * top))


def score_graph(g, shapes_g):
    """Maturity, and whether reporting it is meaningful.

    Two disagreements used to be possible at once. A specification carrying a
    Violation could score 100% and render a green badge while the gate failed
    it, and warnings against non-requirement items were discarded so a spec
    could read 100% while its decisions were malformed. The population is now
    every item, and a graph that fails its gate reports no percentage at all,
    because a maturity number for a specification that does not validate
    describes nothing.
    """
    status = spec_status(g)
    _, results, _ = run_shacl(g, shapes_g)
    fail, violations, warnings = gate(status, results)
    population = items(g)
    flagged = {r["focus"] for r in results}

    def is_clean(item):
        return str(item) not in flagged and not _unresolved_issue(g, item)

    clean_weight = sum(_weight(g, i) for i in population if is_clean(i))
    total_weight = sum(_weight(g, i) for i in population) or 1

    subscores = {}
    for cls in ITEM_CLASSES:
        # The same population as the headline number. A breakdown computed over
        # a different set does not explain the figure above it.
        members = [m for m in g.subjects(RDF.type, cls) if m in population]
        if members:
            subscores[str(cls).split("#")[-1]] = (
                sum(1 for m in members if is_clean(m)), len(members)
            )

    return {
        "gate_failed": fail,
        "status": status,
        "violations": len(violations),
        "warnings": len(warnings),
        "clean": sum(1 for i in population if is_clean(i)),
        "total": len(population),
        "subscores": subscores,
        "progress": progress_graph(g),
        "score": None if fail else round(100 * clean_weight / total_weight),
    }


# Exit codes for layering. Inconclusive is distinct from both, because a peer
# nobody could read must never silently become a pass.
LAYERING_OK, LAYERING_FAIL, LAYERING_INCONCLUSIVE = 0, 1, 3


def _declared_peers(g):
    """Foreign prefixes this specification declares, and the peers they name."""
    peers = {}
    for ref in g.subjects(RDF.type, SPECL.SpecificationReference):
        prefix = g.value(ref, SPECL.prefix)
        base = g.value(ref, SPECL.referenceBase)
        if prefix and base:
            peers[str(prefix)] = {
                "base": str(base),
                "path": str(g.value(ref, SPECL.referencePath) or "") or None,
            }
    return peers


EXPORT_README = """# Checking a SHACL processor against specl's shapes

specl's own `specl-validate` needs nothing from you: it bundles a processor and
refuses to run if that processor lacks the features these shapes require. This
bundle is for the other case, where a team validates specl graphs inside an
existing pipeline with a different SHACL engine.

## What to run

Validate `fixture.ttl` against `shapes.ttl`, with `ns.ttl` supplied to the
processor as an ontology or merged into the data graph. Shapes here consult the
class hierarchy, and their SPARQL runs against the data graph, so without the
vocabulary some checks find nothing rather than failing.

## What to compare

`expected.json` lists the seven findings a conforming processor produces, by
severity, focus node, and property path. Compare all three.

## What a mismatch means

Missing findings almost always mean the processor does not implement SHACL
Advanced Features, which the specification makes optional and these shapes
require. That failure is silent: the processor does not error, it reports
nothing and calls the graph conforming. A processor without them reports none of
the seven.

Two findings in the fixture exist specifically to catch this. `R1` is retired
and must produce **no** findings, because the shapes stop evaluating retired
items using a SPARQL-based target. `R3` is retired with no successor named and
must produce one, from a SPARQL-based constraint. A processor that reports
findings against `R1`, or none against `R3`, is not applying the shapes as
intended.
"""


def cmd_conformance(args):
    """Check that a SHACL processor applies these shapes as intended.

    The shapes use SPARQL-based targets and constraints, which SHACL makes an
    optional feature. A processor without them does not error: it silently
    applies almost nothing, so a specification full of defects validates clean
    and nobody learns otherwise. This runs a fixture with one defect of each
    kind and compares against the findings a conforming processor produces.

    `--export DIR` writes the fixture and the expected findings out, so a team
    using a different processor can run the same check against it.
    """
    root = files("specl") / "conformance"
    expected = json.loads((root / "expected.json").read_text(encoding="utf-8"))

    if args.export:
        out = Path(args.export)
        out.mkdir(parents=True, exist_ok=True)
        for name in ("fixture.ttl", "expected.json"):
            (out / name).write_text((root / name).read_text(encoding="utf-8"), encoding="utf-8")
        (out / "shapes.ttl").write_text(
            (files("specl") / "shapes.ttl").read_text(encoding="utf-8"), encoding="utf-8")
        (out / "ns.ttl").write_text(
            (files("specl") / "core.ttl").read_text(encoding="utf-8"), encoding="utf-8")
        (out / "README.md").write_text(EXPORT_README, encoding="utf-8")
        print(f"wrote fixture.ttl, shapes.ttl, ns.ttl, expected.json, README.md to {out}")
        print("Read README.md there; it says what to run and what to compare.")
        return 0

    _, results, _ = run_shacl(load(str(root / "fixture.ttl")),
                              load(str(files("specl") / "shapes.ttl")))
    got = sorted(
        (r["severity"], r["focus"].rsplit("#", 1)[-1],
         r["path"].rsplit("#", 1)[-1].rsplit("/", 1)[-1])
        for r in results
    )
    want = sorted(
        (f["severity"], f["focus"], f["path"]) for f in expected["findings"]
    )
    missing, extra = [f for f in want if f not in got], [f for f in got if f not in want]

    print(f"Conformance: {len(got)} finding(s), {len(want)} expected")
    for f in missing:
        print(f"  missing   {f[0]:<9} {f[1]} {f[2]}")
    for f in extra:
        print(f"  unexpected {f[0]:<9} {f[1]} {f[2]}")
    if missing or extra:
        print(
            "\nThis processor does not apply the shapes as intended. Missing "
            "findings usually mean SHACL Advanced Features are unavailable, in "
            "which case validation passes specifications it should not."
        )
        return 1
    print("Result: this processor applies the shapes as intended.")
    return 0


def cmd_layering(args):
    """A specification must not reference an item in a specification declared
    downstream of it.

    UR13: this never touches the network. A peer is read from the local path or
    it is not read at all, and an unreadable peer reports inconclusive rather
    than passing, so an unavailable peer cannot become a silent pass.
    """
    g = load(args.data)
    peers = _declared_peers(g)
    downstream = {str(o) for o in g.objects(None, SPECL.upstreamOf)}

    violations, unresolved, checked = [], [], 0
    for prop in (SPECL.affects, SPECL.constrains, SPECL.verifiedBy, SPECL.supersededBy):
        for subject, obj in g.subject_objects(prop):
            target = str(obj)
            for prefix, peer in peers.items():
                if not target.startswith(peer["base"]):
                    continue
                checked += 1
                if peer["base"][:-1] in downstream:
                    violations.append(
                        f"{subject} references {target}, but {prefix} is declared "
                        "downstream of this specification"
                    )
                    continue
                path = Path(peer["path"]) if peer["path"] else None
                if path is None or not path.exists():
                    unresolved.append(
                        f"{prefix}: peer not readable at {peer['path'] or '<no path declared>'}"
                    )
                elif target not in _peer_items(path):
                    unresolved.append(
                        f"{subject} references {target}, which {prefix} does not declare"
                    )

    # Governed terms, checked the same way and against the same rule: read from
    # disk or not at all. A vocabulary is where a typo hides most easily,
    # because a misspelled class name is a valid IRI.
    vocab = {}
    for node in g.subjects(RDF.type, SPECL.Vocabulary):
        base = g.value(node, SPECL.referenceBase)
        path = g.value(node, SPECL.referencePath)
        if base:
            vocab[str(base)] = (str(g.value(node, SPECL.prefix) or "?"),
                                str(path) if path else None)

    for subject, obj in g.subject_objects(SPECL.governs):
        target = str(obj)
        for base, (prefix, path) in vocab.items():
            if not target.startswith(base):
                continue
            checked += 1
            if path is None:
                continue
            location = Path(path)
            if not location.exists():
                unresolved.append(
                    f"{prefix}: vocabulary not readable at {path}"
                )
            elif target not in _vocabulary_terms(location):
                unresolved.append(
                    f"{subject} governs {target}, which {prefix} does not define"
                )

    # A CURIE-shaped literal in a reference-valued field is a cross-specification
    # reference the author attempted and the parser could not resolve. It warned
    # at translation and was invisible here, so layering reported zero
    # references checked and passed over a specification that plainly tried to
    # reach another one.
    for prop in (SPECL.affects, SPECL.constrains, SPECL.verifiedBy,
                 SPECL.supersededBy, SPECL.gates, SPECL.role, SPECL.owner):
        for subject, obj in g.subject_objects(prop):
            if not isinstance(obj, Literal):
                continue
            token = str(obj)
            if not re.match(r"^[A-Za-z][\w-]*:[A-Za-z][\w.-]*$", token):
                continue
            checked += 1
            violations.append(
                f"{subject} names {token!r}, whose prefix this specification "
                "does not declare under references: or vocabularies:"
            )

    print(f"Layering: {checked} external reference(s) checked")
    for v in violations:
        print(f"  [violation]    {v}")
    for u in unresolved:
        print(f"  [unresolved]   {u}")

    if violations:
        return LAYERING_FAIL
    if getattr(args, "require_references", False) and checked == 0:
        # Vacuous passes read as coverage while providing none, and the check
        # that does catch the mistake starts looking redundant beside a green
        # one. Opt-in, so the command keeps meaning the same thing by default.
        print(
            "Result: fail. --require-references was given and this "
            "specification declares none, so nothing was checked."
        )
        return 1

    if unresolved:
        print("Result: inconclusive. A peer that could not be read is never a pass.")
        return LAYERING_INCONCLUSIVE
    print("Result: pass")
    return LAYERING_OK


def _vocabulary_terms(path: Path) -> set[str]:
    """Every subject a vocabulary defines. Read from disk, never fetched."""
    try:
        vocab = Graph().parse(path)
    except Exception:
        return set()
    return {str(s) for s in vocab.subjects()}


def _peer_items(path: Path) -> set[str]:
    """Item IRIs a peer declares, read from disk. Never fetched."""
    try:
        peer = Graph().parse(path)
    except Exception:
        return set()
    return {str(s) for s in peer.subjects(SPECL.partOf, None)}


def _assessment_turtle(g, report, at):
    """One assessment, as a prov:Activity with an IRI derived from its time.

    Recorded rather than printed and discarded. A percentage with no history
    answers nothing about whether a specification is converging, and one with no
    breakdown cannot be attributed.
    """
    spec = next(iter(g.subjects(RDF.type, SPECL.Specification)), None)
    if spec is None:
        return None
    base = str(spec) + "#"
    slug = re.sub(r"[^0-9A-Za-z]", "", at)
    node = f"<{base}assessment-{slug}>"
    lines = [
        f"{node} a specl:MaturityAssessment ;",
        f"    prov:generatedAtTime \"{at}\"^^xsd:dateTime ;",
        f"    specl:assessed <{spec}> ;",
    ]
    if report["score"] is not None:
        lines.append(f"    specl:maturityScore {report['score']} ;")
    if report["progress"] is not None:
        lines.append(f"    specl:progressScore {report['progress']} ;")
    subs = []
    for cls, (clean, total) in sorted(report["subscores"].items()):
        sub = f"<{base}assessment-{slug}-{cls.lower()}>"
        lines.append(f"    specl:subscore {sub} ;")
        subs.append(
            f"{sub} a specl:ClassSubscore ;\n"
            f'    specl:itemClass "{cls}" ;\n'
            f"    specl:cleanCount {clean} ;\n"
            f"    specl:totalCount {total} .\n"
        )
    lines[-1] = lines[-1].rstrip(" ;") + " ."
    return "\n".join(lines) + "\n\n" + "\n".join(subs)


HISTORY_HEADER = """@prefix specl: <https://w3id.org/specl/ns#> .
@prefix prov: <http://www.w3.org/ns/prov#> .
@prefix xsd:  <http://www.w3.org/2001/XMLSchema#> .

"""


def cmd_score(args):
    g = load(args.data)
    report = score_graph(g, load(args.shapes))

    history = getattr(args, "history", None)
    if history:
        # Appending is opt-in. Scoring stays side-effect free by default, so a
        # CI run that only reports does not silently accumulate a log.
        at = getattr(args, "at", None) or _dt.datetime.now(_dt.timezone.utc).isoformat(
            timespec="seconds"
        ).replace("+00:00", "Z")
        block = _assessment_turtle(g, report, at)
        if block:
            path = Path(history)
            if not path.exists():
                path.write_text(HISTORY_HEADER, encoding="utf-8")
            with path.open("a", encoding="utf-8") as fh:
                fh.write(block + "\n")
            print(f"appended assessment at {at} to {history}")

    if report["gate_failed"]:
        # Why the gate failed depends on status: a production specification
        # fails on warnings too, and reporting "0 violations" there is a message
        # that describes nothing.
        if report["violations"]:
            reason = f"{report['violations']} violation(s)"
        else:
            reason = (
                f"{report['warnings']} warning(s), which block at status "
                f"{report['status']!r}"
            )
        print(
            f"Maturity: not reported. The gate fails with {reason}; a maturity "
            "percentage for a specification that does not validate describes "
            "nothing."
        )
        return None
    print(
        f"Maturity: {report['score']}%  "
        f"({report['clean']}/{report['total']} items clean, priority weighted)"
    )
    if report["progress"] is not None:
        print(f"Progress: {report['progress']}%  (built, rolled up from items)")
    for cls, (clean, total) in sorted(report["subscores"].items()):
        print(f"  {cls:<18} {clean}/{total}")
    return report["score"]

def _badge_link(graph, override):
    """Where a badge should point.

    At the specification itself, by default. A badge is a claim, and a reader
    who sees one asks what it is a claim about; the answer is the specification,
    not the tool that measured it. The Specification IRI is already a permanent
    identifier that resolves to the source, so nothing new has to be invented or
    configured.
    """
    if override:
        return override
    spec = next(iter(graph.subjects(RDF.type, SPECL.Specification)), None)
    return str(spec) if spec else None


# Muted rather than saturated, and each paired with the text colour that is
# actually legible on it. White on the old yellow measured 1.98:1, well under
# the 4.5:1 WCAG floor for normal text, so a 55% badge was unreadable.
BADGE_LABEL_FILL = "#5b6169"
BADGE_LABEL_TEXT = "#ffffff"
BADGE_COLOURS = {
    "low": "#c98b8b",      # rose
    "mid": "#d9b46a",      # amber
    "high": "#8fb996",     # sage
    "failing": "#b08585",  # deeper rose, so a failing gate reads as failing
}


def _relative_luminance(colour: str) -> float:
    """WCAG relative luminance, so the text colour is derived rather than
    guessed. Picking by eye is how white ended up on yellow."""
    value = colour.lstrip("#")
    if len(value) == 3:
        value = "".join(c * 2 for c in value)
    channels = []
    for index in (0, 2, 4):
        part = int(value[index:index + 2], 16) / 255
        channels.append(part / 12.92 if part <= 0.03928 else ((part + 0.055) / 1.055) ** 2.4)
    red, green, blue = channels
    return 0.2126 * red + 0.7152 * green + 0.0722 * blue


def contrast_ratio(a: str, b: str) -> float:
    high, low = sorted((_relative_luminance(a), _relative_luminance(b)), reverse=True)
    return (high + 0.05) / (low + 0.05)


def readable_text(background: str) -> str:
    """Near-black or white, whichever the background actually supports."""
    dark, light = "#1a1a1a", "#ffffff"
    return dark if contrast_ratio(background, dark) >= contrast_ratio(background, light) else light


def badge_svg(label: str, background: str) -> str:
    width = max(46, 9 + 7 * len(label))
    text = readable_text(background)
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{80 + width}" height="20" '
        f'role="img" aria-label="spec maturity: {label}">\n'
        f'<rect width="80" height="20" rx="3" fill="{BADGE_LABEL_FILL}"/>'
        f'<rect x="80" width="{width}" height="20" rx="3" fill="{background}"/>\n'
        f'<text x="40" y="14" fill="{BADGE_LABEL_TEXT}" font-family="Verdana" '
        f'font-size="11" text-anchor="middle">spec maturity</text>\n'
        f'<text x="{80 + width // 2}" y="14" fill="{text}" font-family="Verdana" '
        f'font-size="11" text-anchor="middle">{label}</text>\n</svg>'
    )


def badge_background(score):
    if score is None:
        return BADGE_COLOURS["failing"]
    return BADGE_COLOURS["low" if score < 50 else "mid" if score < 85 else "high"]


def cmd_badge(args):
    # A rendering of an assessment rather than the only artifact. With a
    # history, the badge shows what was last recorded; without one it scores now.
    history = getattr(args, "history", None)
    if history and Path(history).exists():
        latest = _latest_assessment(load(history))
        if latest is not None:
            score = latest
            print(f"Maturity: {score}%  (latest recorded assessment)")
            return _write_badge(args.out, score)
    score = cmd_score(args)
    # A badge is a public claim, so it says "failing" rather than a number when
    # the gate fails. A green badge over a failing gate is the disagreement this
    # is here to prevent.
    label = "failing" if score is None else f"{score}%"
    svg = badge_svg(label, badge_background(score))
    open(args.out, "w", encoding="utf-8").write(svg)
    print(f"wrote {args.out}")
    _print_markdown(args, load(args.data))


def _print_markdown(args, graph):
    """The link lives in markdown, not in the SVG.

    GitHub sanitizes SVG served through an img tag, so a link inside the image
    is discarded. Printing the snippet is the only way the badge can carry one.
    """
    link = _badge_link(graph, getattr(args, "link", None))
    alt = "spec maturity"
    if link:
        print(f"[![{alt}]({args.out})]({link})")
    else:
        print(f"![{alt}]({args.out})")


def _write_badge(out, score):
    open(out, "w", encoding="utf-8").write(badge_svg(f"{score}%", badge_background(score)))
    print(f"wrote {out}")


def _latest_assessment(history):
    """The most recent recorded score, by generation time."""
    best = None
    for node in history.subjects(RDF.type, SPECL.MaturityAssessment):
        at = history.value(node, PROV.generatedAtTime)
        score = history.value(node, SPECL.maturityScore)
        if at is None or score is None:
            continue
        if best is None or str(at) > best[0]:
            best = (str(at), int(score))
    return best[1] if best else None

def main():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)
    v = sub.add_parser("validate"); v.add_argument("data"); v.add_argument("shapes", nargs="?", default=None,
                       help="SHACL shapes graph; defaults to the shapes bundled with specl")
    v.add_argument("--explain", action="store_true"); v.add_argument("--json")
    v.set_defaults(func=cmd_validate)
    d = sub.add_parser("diff"); d.add_argument("old"); d.add_argument("new")
    d.add_argument("--changelog", metavar="PATH",
                   help="append a changelog stub. Opt-in: read-only inspection "
                        "should not write to the working directory.")
    d.add_argument("--ignore-base", action="store_true",
                   help="key requirements by identifier token rather than IRI, "
                        "so a rebased graph diffs against its original")
    d.set_defaults(func=cmd_diff)
    s = sub.add_parser("score"); s.add_argument("data"); s.add_argument("shapes", nargs="?", default=None,
                       help="SHACL shapes graph; defaults to the shapes bundled with specl")
    s.add_argument("--history", metavar="FILE",
                   help="append this assessment to a history graph. Opt-in, so "
                        "a run that only reports does not accumulate a log.")
    s.add_argument("--at", metavar="ISO8601",
                   help="timestamp for the assessment; defaults to now")
    s.set_defaults(func=cmd_score)
    c = sub.add_parser("conformance", help="check that a SHACL processor applies "
                       "these shapes as intended")
    c.add_argument("--export", metavar="DIR",
                   help="write the fixture, shapes, vocabulary, and expected "
                        "findings out for use with another processor")
    c.set_defaults(func=cmd_conformance)
    l = sub.add_parser("layering", help="check cross-specification references "
                       "against declared upstream and downstream relations")
    l.add_argument("data")
    l.add_argument("--require-references", action="store_true",
                   help="fail when a specification declares no cross-specification "
                        "references, so the check means something in CI rather "
                        "than passing vacuously")
    l.set_defaults(func=cmd_layering)
    b = sub.add_parser("badge"); b.add_argument("data"); b.add_argument("shapes", nargs="?", default=None,
                       help="SHACL shapes graph; defaults to the shapes bundled with specl")
    b.add_argument("--out", default="spec-badge.svg")
    b.add_argument("--history", metavar="FILE",
                   help="render the latest recorded assessment instead of scoring now")
    b.add_argument("--link", metavar="URL",
                   help="where the badge points. Defaults to the Specification "
                        "IRI, which already resolves to the source.")
    b.set_defaults(func=cmd_badge)
    args = p.parse_args()
    if getattr(args, "shapes", None) is None and hasattr(args, "shapes"):
        args.shapes = bundled_shapes()
    result = args.func(args)
    if isinstance(result, int) and args.cmd in ("layering", "conformance"):
        sys.exit(result)

if __name__ == "__main__":
    main()
