"""spec_to_rdf.py — translate a specl markdown spec to Turtle.

Usage: specl-translate <spec.md> <spec.ttl> [--strict]

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
import re, sys, hashlib, datetime as dt, argparse
from pathlib import Path

NS = "https://example.org/ekga/ns#"
SPEC = "https://example.org/ekga/spec/"

HEADER = f"""@prefix ekga: <{NS}> .
@prefix spec: <{SPEC}> .
@prefix prov: <http://www.w3.org/ns/prov#> .
@prefix dct:  <http://purl.org/dc/terms/> .
@prefix xsd:  <http://www.w3.org/2001/XMLSchema#> .

"""

BULLET_RE = re.compile(r"^-\s+(R\d+(?:\.\d+)?|US\d+|OQ\d+|D\d+)\.?\s+(.*)")
SUB_RE = re.compile(
    r"^(?:\s{2,}|\t)-\s+"
    r"(priority|acceptance|verifiedBy|constrains|asA|soThat|"
    r"owner|recommendation|status|rationale|affects)\s*:\s*(.*)$",
    re.IGNORECASE,
)
MULTI_KEYS = {"constrains", "affects"}  # comma-split; prose keys use multiple sub-bullets
PROP_MAP = {
    "priority": "priority", "acceptance": "acceptanceCriterion",
    "verifiedBy": "verifiedBy", "constrains": "constrains",
    "asA": "asA", "soThat": "soThat", "owner": "owner",
    "recommendation": "recommendation", "rationale": "rationale",
    "affects": "affects",
}
FM_COMMENT_RE = re.compile(r"<!--specl\s*(.*?)-->", re.DOTALL)

SECTION_MAP = [
    ("Requirements", "Requirement", ("R",)),
    ("User Stories", "UserStory", ("US",)),
    ("Open Questions and Gaps (flag for follow-up)", "OpenIssue", ("OQ",)),
    ("Open Questions", "OpenIssue", ("OQ",)),
    ("Open Issues", "OpenIssue", ("OQ",)),
    ("Decisions", "DecisionRecord", ("D",)),
    ("Design Considerations", "DesignNote", None),
    ("Comments", "Comment", None),
]


def esc(s: str) -> str:
    return s.replace("\\", "\\\\").replace('"', '\\"')


def slug(s: str) -> str:
    return hashlib.sha1(s.encode()).hexdigest()[:8]


def parse(md: str):
    warnings: list[str] = []
    front: dict[str, str] = {}
    if md.startswith("---"):
        end = md.find("---", 3)
        if end > 0:
            for line in md[3:end].strip().splitlines():
                if ":" in line and not line.startswith("#"):
                    k, v = line.split(":", 1)
                    front[k.strip()] = v.strip().strip("[]")
            md = md[end + 3:]
        else:
            warnings.append("YAML front-matter opened with --- but never closed")

    fm_comments: dict[str, str] = {}
    for m in FM_COMMENT_RE.finditer(md):
        for line in m.group(1).strip().splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                fm_comments[k.strip()] = v.strip()
    md = FM_COMMENT_RE.sub("", md)

    sections: dict[str, list[str]] = {}
    cur = None
    for line in md.splitlines():
        if line.startswith("# "):
            cur = line[2:].strip()
            sections[cur] = []
        elif cur is not None:
            sections[cur].append(line)
    return front, sections, fm_comments, warnings


def parse_bullets(lines, warnings):
    items = []
    current = None
    for raw in lines:
        if raw.startswith("- "):
            bm = BULLET_RE.match(raw)
            if bm:
                if current:
                    items.append(current)
                current = (bm.group(1), bm.group(2).strip(), {})
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
        if stripped.startswith("- ") and current and raw.startswith(" ") and not SUB_RE.match(raw):
            warnings.append(f"sub-bullet did not match known annotation key: {stripped!r}")
    if current:
        items.append(current)
    return items


def _emit_item(iri, cls, description, annotations, spec_iri):
    body = [f"{iri} a ekga:{cls} ;",
            f"    ekga:partOf {spec_iri} ;",
            f'    dct:description "{esc(description)}"']
    triples = []
    for key, values in annotations.items():
        if key == "status":
            prop = "decisionStatus" if cls == "DecisionRecord" else "resolutionStatus"
        else:
            prop = PROP_MAP.get(key)
        if not prop:
            continue
        for v in values:
            triples.append(f'    ekga:{prop} "{esc(v)}"')
    if triples:
        body[-1] = body[-1] + " ;"
        for i, t in enumerate(triples):
            body.append(t + (" ." if i == len(triples) - 1 else " ;"))
    else:
        body[-1] = body[-1] + " ."
    return "\n".join(body) + "\n\n"


def emit(front, sections, fm_comments, warnings):
    out = [HEADER]
    spec_iri = f"spec:{front.get('spec_id', 'spec-001')}"
    created = fm_comments.get("created", dt.date.today().isoformat())
    intent = " ".join(sections.get("Intent", [])).strip()
    purpose = " ".join(sections.get("Purpose", [])).strip()
    out.append(f"""{spec_iri} a ekga:Specification ;
    dct:title "{esc(front.get('title', 'Untitled'))}" ;
    dct:hasVersion "{front.get('version', '0.1.0')}" ;
    ekga:status "{front.get('status', 'draft')}" ;
    dct:created "{created}"^^xsd:date ;
    ekga:intent \"\"\"{esc(intent)}\"\"\" ;
    ekga:purpose \"\"\"{esc(purpose)}\"\"\" .

""")
    for section_name, cls, prefixes in SECTION_MAP:
        lines = sections.get(section_name)
        if not lines:
            continue
        if prefixes is None:
            for line in lines:
                t = line.strip().lstrip("-0123456789. ").strip()
                if not t:
                    continue
                iri = f"spec:{cls.lower()}-{slug(t)}"
                out.append(_emit_item(iri, cls, t, {}, spec_iri))
        else:
            for item_id, desc, annotations in parse_bullets(lines, warnings):
                if not any(item_id.startswith(p) for p in prefixes):
                    warnings.append(
                        f"{item_id} in '{section_name}' does not match prefix {prefixes}"
                    )
                out.append(_emit_item(f"spec:{item_id}", cls, desc, annotations, spec_iri))
    return "".join(out)


def main():
    ap = argparse.ArgumentParser(prog="specl-translate")
    ap.add_argument("src")
    ap.add_argument("dst")
    ap.add_argument("--strict", action="store_true",
                    help="print parser warnings to stderr")
    args = ap.parse_args()
    front, sections, fm, warnings = parse(Path(args.src).read_text(encoding="utf-8"))
    Path(args.dst).write_text(emit(front, sections, fm, warnings), encoding="utf-8")
    if args.strict and warnings:
        for w in warnings:
            print(f"warning: {w}", file=sys.stderr)
    print(f"wrote {args.dst} ({len(warnings)} parser warning(s))")


if __name__ == "__main__":
    main()
