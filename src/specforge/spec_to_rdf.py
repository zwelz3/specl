"""spec_to_rdf.py — translate the EKGA markdown spec to Turtle.

Usage: python spec_to_rdf.py enterprise-kg-app-spec.md spec.ttl

Parses the markdown structure (YAML frontmatter + H1/H2 sections + bullets
with IDs like R1.1, US3) and emits nested Turtle. Zero deps beyond stdlib
plus PyYAML (optional; falls back to a tiny parser).
"""
from __future__ import annotations
import re, sys, hashlib, datetime as dt
from pathlib import Path

NS = "https://example.org/ekga/ns#"
SPEC = "https://example.org/ekga/spec/"

HEADER = f"""@prefix ekga: <{NS}> .
@prefix spec: <{SPEC}> .
@prefix prov: <http://www.w3.org/ns/prov#> .
@prefix dct:  <http://purl.org/dc/terms/> .
@prefix xsd:  <http://www.w3.org/2001/XMLSchema#> .

"""

ID_RE = re.compile(r"^-\s+(R\d+(?:\.\d+)?|US\d+)\.?\s+(.*)")

def esc(s: str) -> str:
    return s.replace("\\", "\\\\").replace('"', '\\"')

def slug(s: str) -> str:
    return hashlib.sha1(s.encode()).hexdigest()[:8]

def parse(md: str):
    front = {}
    if md.startswith("---"):
        end = md.find("---", 3)
        for line in md[3:end].strip().splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                front[k.strip()] = v.strip().strip("[]")
        md = md[end+3:]
    sections, cur = {}, None
    for line in md.splitlines():
        if line.startswith("# "):
            cur = line[2:].strip(); sections[cur] = []
        elif cur is not None:
            sections[cur].append(line)
    return front, sections

def emit(front, sections) -> str:
    out = [HEADER]
    spec_iri = f"spec:{front.get('spec_id','ekga-001')}"
    out.append(f"""{spec_iri} a ekga:Specification ;
    dct:title "{esc(front.get('title','EKGA'))}" ;
    dct:hasVersion "{front.get('version','0.1.0')}" ;
    ekga:status "{front.get('status','draft')}" ;
    dct:created "{dt.date.today().isoformat()}"^^xsd:date ;
    ekga:intent \"\"\"{esc(' '.join(sections.get('Intent',[])).strip())}\"\"\" ;
    ekga:purpose \"\"\"{esc(' '.join(sections.get('Purpose',[])).strip())}\"\"\" .

""")
    for sec, kind in [("Requirements","Requirement"),("User Stories","UserStory")]:
        for line in sections.get(sec, []):
            m = ID_RE.match(line.strip())
            if not m: continue
            rid, text = m.groups()
            out.append(f'spec:{rid} a ekga:{kind} ; ekga:partOf {spec_iri} ; dct:description "{esc(text)}" .\n')
    for sec, cls in [("Design Considerations","DesignNote"),("Comments","Comment"),
                     ("Open Questions and Gaps (flag for follow-up)","OpenIssue")]:
        for line in sections.get(sec, []):
            t = line.strip().lstrip("-0123456789. ").strip()
            if not t: continue
            out.append(f'spec:{cls.lower()}-{slug(t)} a ekga:{cls} ; ekga:partOf {spec_iri} ; dct:description "{esc(t)}" .\n')
    return "".join(out)

def main():
    if len(sys.argv) != 3:
        print("usage: specforge-translate <spec.md> <spec.ttl>", file=sys.stderr)
        sys.exit(2)
    src = Path(sys.argv[1]); dst = Path(sys.argv[2])
    front, sections = parse(src.read_text(encoding="utf-8"))
    dst.write_text(emit(front, sections), encoding="utf-8")
    print(f"wrote {dst}")

if __name__ == "__main__":
    main()
