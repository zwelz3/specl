"""Emit the specl grammar as one JSON document, for the explorer's syntax
reference (R13.1, R13.2) and its readiness estimate (R5.6).

This is the generator UP-3 asks specl to own. Until it does, it lives here
and reads the installed specl directly: the translator's tables and the
bundled shapes. Run from a checkout with specl installed:

    python3 build/grammar.py > build/grammar.json

Nothing in the explorer imports this; the build reads the JSON.
"""
import datetime
import importlib.metadata
import json
import re
import sys
from importlib.resources import files

from rdflib import Graph, Namespace, RDF, RDFS

from specl import spec_to_rdf as T

SH = Namespace("http://www.w3.org/ns/shacl#")
SPECL = Namespace("https://w3id.org/specl/ns#")
DCT = Namespace("http://purl.org/dc/terms/")
SKOS = Namespace("http://www.w3.org/2004/02/skos/core#")

PREFIX_NS = {"specl": str(SPECL), "dct": str(DCT), "skos": str(SKOS)}


def qualify(prop):
    """PROP_MAP values are either bare (specl) or prefixed (dct:, skos:)."""
    if ":" in prop:
        p, l = prop.split(":", 1)
        return PREFIX_NS[p] + l
    return str(SPECL) + prop


def local(iri):
    s = str(iri)
    return s.split("#")[-1].split("/")[-1]


def shapes_expectations():
    g = Graph().parse(files("specl") / "shapes.ttl")
    out = {}
    for ns in g.subjects(RDF.type, SH.NodeShape):
        # Target class: sh:targetClass, or the class named in a SPARQL target.
        cls = None
        tc = g.value(ns, SH.targetClass)
        if tc is not None:
            cls = local(tc)
        else:
            for t in g.objects(ns, SH.target):
                sel = str(g.value(t, SH.select) or "")
                m = re.search(r"\?this a <https://w3id\.org/specl/ns#(\w+)>", sel)
                if m:
                    cls = m.group(1)
        status_only = cls is None and any('itemStatus> "' in str(g.value(t, SH.select) or "") for t in g.objects(ns, SH.target))
        if not cls and not status_only:
            continue
        targets = [cls] if cls else item_classes()
        # Conditions expressed in the SPARQL target that a consumer can reproduce.
        condition = None
        for t in g.objects(ns, SH.target):
            sel = str(g.value(t, SH.select) or "")
            # FILTER EXISTS { ?any a <X> } or FILTER EXISTS { ?any a ?vc . FILTER(?vc IN (<X>, <Y>)) }
            m = re.search(r"FILTER EXISTS \{\s*\?any a (?:<https://w3id\.org/specl/ns#(\w+)>|\?vc \.\s*FILTER\(\?vc IN \(([^)]*)\)\))", sel, re.S)
            if m:
                names = [m.group(1)] if m.group(1) else re.findall(r"ns#(\w+)>", m.group(2))
                condition = {"graphHasAny": names}
            m2 = re.search(r'itemStatus> "(\w+)" \}', sel)
            if m2:
                condition = {"itemStatus": m2.group(1)}
        for ps in g.objects(ns, SH.property):
            path = g.value(ps, SH.path)
            if path is None:
                continue
            sev = g.value(ps, SH.severity)
            entry = {
                "property": str(path), "key": local(path),
                "severity": local(sev) if sev is not None else "Violation",
                "message": str(g.value(ps, SH.message) or ""),
            }
            mn = g.value(ps, SH.minCount)
            if mn is not None:
                entry["minCount"] = int(mn)
            mx = g.value(ps, SH.maxCount)
            if mx is not None:
                entry["maxCount"] = int(mx)
            ml = g.value(ps, SH.minLength)
            if ml is not None:
                entry["minLength"] = int(ml)
            inn = g.value(ps, SH["in"])
            if inn is not None:
                entry["in"] = [str(x) for x in g.items(inn)]
            if condition:
                entry["condition"] = condition
            for c_ in targets:
                out.setdefault(c_, []).append(dict(entry))
        for sq in g.objects(ns, SH.sparql):
            for c_ in targets:
                out.setdefault(c_, []).append({
                    "sparql": True, "severity": local(g.value(sq, SH.severity) or SH.Violation),
                    "message": str(g.value(sq, SH.message) or ""), "shape": local(ns),
                })
    return out


def item_classes():
    core = Graph().parse(files("specl") / "core.ttl")
    return sorted(local(s) for s in core.subjects(RDFS.subClassOf, SPECL.Item))


def main():
    keys = []
    for key, prop in T.PROP_MAP.items():
        entry = {"key": key, "property": qualify(prop)}
        if key in T.REFERENCE_KEYS:
            entry["reference"] = True
            rng = T.REFERENCE_KEYS[key]
            if rng:
                entry["range"] = str(SPECL) + rng
        keys.append(entry)
    for key in T.CONTEXTUAL_KEYS:
        if key == "status":
            keys.append({"key": key, "contextual": True,
                         "resolvesTo": {"DecisionRecord": str(SPECL) + "decisionStatus", "*": str(SPECL) + "resolutionStatus"}})
        else:
            keys.append({"key": key, "property": str(SPECL) + key, "contextual": True})

    sections = [{"heading": h, "class": c, "prefixes": list(p)} for h, c, p in T.SECTION_MAP]
    grammar = {
        "specl": importlib.metadata.version("specl"),
        "contract": T.CONTRACT,
        "generated": datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0).isoformat(),
        "generator": "explorer/build/grammar.py (interim; see UP-3)",
        "frontMatter": {
            "required": ["spec_base"],
            "recognised": ["spec_base", "prefix", "spec_id", "title", "version", "status", "item_prefix",
                            "references", "vocabularies", "sections", "companion_files"] + list(T.SPEC_RELATIONS),
            "statusValues": ["draft", "prototype", "review", "production"],
        },
        "documentComment": "<!--specl created: YYYY-MM-DD -->",
        "sections": sections,
        "proseSections": list(T.PROSE_SECTIONS),
        "mappableClasses": {c: list(p) for c, p in T.MAPPABLE_CLASSES.items()},
        "markers": {"parked": "<!--specl: parked-->", "prose": "<!--specl: prose-->"},
        "itemForm": "- <PREFIX><n>[.<n>] <description>\n  - <key>: <value>\n    - <detail line>",
        "keys": keys,
        "itemClasses": item_classes(),
        "expectations": shapes_expectations(),
        "score": {
            "population": "items of every item class, excluding itemStatus superseded or withdrawn",
            "clean": "the item is the focus of no validation result at any severity, and an OpenIssue is not clean unless resolutionStatus is resolved or deferred",
            "weights": {"MUST": 4, "SHOULD": 3, "COULD": 2, "WONT": 1, "default": 2},
            "figure": "round(100 * sum(weight of clean items) / sum(weight of all items)); none when the gate fails",
            "gate": "any Violation fails; at status production, any Warning fails too",
            "source": "specl.validate_spec.score_graph, read from the installed version; not yet published by specl (UP-2)",
        },
    }
    json.dump(grammar, sys.stdout, indent=1)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
