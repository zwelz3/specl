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
import sys, json, argparse
from rdflib import Graph, Namespace, RDF
from pyshacl import validate

SPECL = Namespace("https://w3id.org/specl/ns#")
SH = Namespace("http://www.w3.org/ns/shacl#")

def load(p): g = Graph(); g.parse(p, format="turtle"); return g

def spec_status(g):
    for s in g.subjects(RDF.type, SPECL.Specification):
        v = g.value(s, SPECL.status)
        if v: return str(v).lower()
    return "draft"

def run_shacl(data_g, shapes_g):
    conforms, report_g, _ = validate(data_g, shacl_graph=shapes_g,
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
        with open(args.json, "w") as fp:
            json.dump({"status": status, "results": results}, fp, indent=2)
    sys.exit(1 if fail else 0)

def _req_map(g):
    out = {}
    for r in g.subjects(RDF.type, SPECL.Requirement):
        out[str(r)] = {str(p).split("#")[-1]: str(o) for p, o in g.predicate_objects(r)}
    return out

def cmd_diff(args):
    old, new = _req_map(load(args.old)), _req_map(load(args.new))
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
    # Auto-append changelog stub
    with open("CHANGELOG.spec.md", "a") as fp:
        fp.write(f"\n## diff {args.old} -> {args.new}\n")
        for k in added: fp.write(f"- added {k}\n")
        for k in removed: fp.write(f"- removed {k}\n")
        for k, kind in changed: fp.write(f"- {kind} {k}\n")

def cmd_score(args):
    g, s = load(args.data), load(args.shapes)
    _, results, _ = run_shacl(g, s)
    reqs = list(g.subjects(RDF.type, SPECL.Requirement))
    n = len(reqs) or 1
    bad = {r["focus"] for r in results}
    good = sum(1 for r in reqs if str(r) not in bad)
    score = round(100 * good / n)
    print(f"Maturity: {score}%  ({good}/{n} requirements clean)")
    return score

def cmd_badge(args):
    score = cmd_score(args)
    color = "red" if score < 50 else "yellow" if score < 85 else "brightgreen"
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="140" height="20">
<rect width="80" height="20" fill="#555"/><rect x="80" width="60" height="20" fill="{color}"/>
<text x="40" y="14" fill="#fff" font-family="Verdana" font-size="11" text-anchor="middle">spec maturity</text>
<text x="110" y="14" fill="#fff" font-family="Verdana" font-size="11" text-anchor="middle">{score}%</text>
</svg>'''
    open(args.out, "w").write(svg)
    print(f"wrote {args.out}")

def main():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)
    v = sub.add_parser("validate"); v.add_argument("data"); v.add_argument("shapes")
    v.add_argument("--explain", action="store_true"); v.add_argument("--json")
    v.set_defaults(func=cmd_validate)
    d = sub.add_parser("diff"); d.add_argument("old"); d.add_argument("new")
    d.set_defaults(func=cmd_diff)
    s = sub.add_parser("score"); s.add_argument("data"); s.add_argument("shapes")
    s.set_defaults(func=cmd_score)
    b = sub.add_parser("badge"); b.add_argument("data"); b.add_argument("shapes")
    b.add_argument("--out", default="spec-badge.svg"); b.set_defaults(func=cmd_badge)
    args = p.parse_args(); args.func(args)

if __name__ == "__main__":
    main()
