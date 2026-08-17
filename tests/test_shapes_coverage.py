"""The shapes graph may not require a property the translator cannot emit.

P2 was exactly this. `SpecificationShape` and `DecisionRecordShape` require
`dct:title` at Violation severity, and the translator has never emitted a title
on any item, so every specification carrying a `# Decisions` section failed the
gate unconditionally. Nothing compared the two artifacts, so nothing caught it.

The check runs against real output rather than against a list of properties
maintained by hand: translate the maximal fixture, collect what each class
actually carries, and compare that to what the shapes demand of it.
"""
from __future__ import annotations

import pytest

rdflib = pytest.importorskip("rdflib")
from rdflib import Graph, RDF, SH, URIRef  # noqa: E402

from conftest import SHAPES, spec_path, translate  # noqa: E402

SPECL = rdflib.Namespace("https://w3id.org/specl/ns#")


def required_paths(shapes: Graph) -> dict[URIRef, set[URIRef]]:
    """Property paths each targeted class must carry, at Violation severity."""
    out: dict[URIRef, set[URIRef]] = {}
    for shape in shapes.subjects(RDF.type, SH.NodeShape):
        for cls in shapes.objects(shape, SH.targetClass):
            for prop in shapes.objects(shape, SH.property):
                severity = shapes.value(prop, SH.severity)
                min_count = shapes.value(prop, SH.minCount)
                path = shapes.value(prop, SH.path)
                if severity == SH.Violation and min_count and int(min_count) > 0:
                    out.setdefault(cls, set()).add(path)
    return out


def emitted_paths(graph: Graph) -> dict[URIRef, set[URIRef]]:
    out: dict[URIRef, set[URIRef]] = {}
    for node, _, cls in graph.triples((None, RDF.type, None)):
        out.setdefault(cls, set()).update(p for p in graph.predicates(node, None))
    return out


@pytest.fixture(scope="module")
def coverage(tmp_path_factory):
    target = tmp_path_factory.mktemp("cov") / "maximal.ttl"
    result = translate(spec_path("maximal"), target)
    assert result.returncode == 0, result.stderr
    return required_paths(Graph().parse(SHAPES)), emitted_paths(Graph().parse(target))


def test_violation_paths_are_producible(coverage):
    required, emitted = coverage
    gaps = {
        str(cls).split("#")[-1]: sorted(str(p).split("#")[-1].split("/")[-1] for p in miss)
        for cls, paths in required.items()
        if (miss := paths - emitted.get(cls, set()))
        if cls in emitted
    }
    assert not gaps, (
        "the shapes require properties the translator cannot emit, so every "
        f"specification carrying one of these classes fails the gate: {gaps}"
    )


def test_every_targeted_class_is_reachable(coverage):
    """A shape targeting a class no section produces is dead configuration."""
    required, emitted = coverage
    unreachable = sorted(
        str(cls).split("#")[-1] for cls in required if cls not in emitted
    )
    assert not unreachable, (
        "shapes target classes the maximal fixture does not produce; either the "
        f"fixture is incomplete or the shapes are dead: {unreachable}"
    )
