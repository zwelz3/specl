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


def test_a_component_free_specification_can_reach_production(tmp_path):
    """UR25, and the accepted half of UR8.

    `docs/proposals/0002-downstream-request-disposition.md` declined a per-item
    suppression facility a second party asked for, on the grounds that making
    these two warnings conditional would clear them without one. The refusal was
    accepted on those terms and the shapes never changed, so a specification
    declaring no components carried one warning of each kind per requirement,
    and every warning blocks at `production`. No `verifiedBy` bound the accepted
    half, so nothing in CI could notice for eight releases.
    """
    pytest.importorskip("pyshacl")
    from specl.validate_spec import gate, load, run_shacl

    source = tmp_path / "s.md"
    source.write_text(
        "---\ntitle: T\nspec_base: https://example.org/specs/t#\nspec_id: t-001\n"
        "status: production\nversion: 1.0.0\n---\n\n"
        "# Intent\nA specification that names no components.\n\n"
        "# Purpose\nTo reach production without them.\n\n"
        "# Requirements\n\n- R1 The library must expose a stable public interface.\n"
        "  - priority: MUST\n"
        "  - acceptance: Given the package when imported then the interface is present\n",
        encoding="utf-8",
    )
    target = tmp_path / "s.ttl"
    translate(source, target)
    graph = Graph().parse(target)
    _, results, _ = run_shacl(graph, load(SHAPES))

    for prop in ("constrains", "verifiedBy"):
        assert not [r for r in results if r["path"].endswith(prop)], (
            f"{prop} warns in a specification that declares none"
        )


def test_the_conditions_activate_once_the_graph_declares_them(tmp_path):
    """The other half. A specification that declares components and omits them
    on a requirement is failing to link, and should still be told."""
    pytest.importorskip("pyshacl")
    from specl.validate_spec import load, run_shacl

    source = tmp_path / "s.md"
    source.write_text(
        "---\ntitle: T\nspec_base: https://example.org/specs/t#\nspec_id: t-001\n---\n\n"
        "# Requirements\n\n- R1 A requirement naming a component and a test.\n"
        "  - constrains: engine\n  - verifiedBy: tests/t.py::t\n"
        "- R2 A requirement naming neither.\n",
        encoding="utf-8",
    )
    target = tmp_path / "s.ttl"
    translate(source, target)
    _, results, _ = run_shacl(Graph().parse(target), load(SHAPES))
    flagged = {r["path"].rsplit("#", 1)[-1] for r in results if r["focus"].endswith("R2")}
    assert {"constrains", "verifiedBy"} <= flagged
