"""Reference-valued annotations resolve to IRIs, not literals.

P1. `core.ttl` declares `specl:affects`, `specl:constrains`, and
`specl:verifiedBy` as object properties, two with a declared range. Emitting
them as strings made the graph contradict its own ontology and reduced
traceability to string matching, which is what the RDF was meant to replace.
"""
from __future__ import annotations

import pytest

from conftest import PUBLISHED, FIXTURE_SPECS, spec_path, translate

rdflib = pytest.importorskip("rdflib")
from rdflib import Graph, Literal, Namespace, URIRef  # noqa: E402

SPECL = Namespace("https://w3id.org/specl/ns#")
HEAD = (
    "---\ntitle: T\nspec_base: https://example.org/specs/t#\n"
    "spec_id: t-001\nversion: 0.1.0\nstatus: draft\n---\n\n"
)


def build(tmp_path, body):
    source = tmp_path / "s.md"
    source.write_text(HEAD + body, encoding="utf-8")
    target = tmp_path / "s.ttl"
    result = translate(source, target)
    return result, Graph().parse(target)


def test_an_item_reference_resolves_against_the_base(tmp_path):
    result, graph = build(
        tmp_path,
        "# Requirements\n\n- R1 Exists.\n\n# Decisions\n\n- D1 Points at it.\n  - affects: R1\n",
    )
    assert result.returncode == 0, result.stderr
    obj = graph.value(URIRef("https://example.org/specs/t#D1"), SPECL.affects)
    assert obj == URIRef("https://example.org/specs/t#R1")


def test_a_dangling_reference_warns_and_still_resolves(tmp_path):
    """The practical payoff: a decision pointing at a renumbered or deleted
    requirement. The IRI is still emitted, so the reference is visible in the
    graph rather than silently absent."""
    result, graph = build(
        tmp_path,
        "# Requirements\n\n- R1 Exists.\n\n# Decisions\n\n- D1 Points nowhere.\n  - affects: R99\n",
    )
    assert "no item in this specification declares" in result.stderr
    assert graph.value(URIRef("https://example.org/specs/t#D1"), SPECL.affects) == URIRef(
        "https://example.org/specs/t#R99"
    )


def test_an_undeclared_prefix_warns_and_stays_a_literal(tmp_path):
    """UR18. Before 0.5.0 no prefix could be declared, so every CURIE warned.
    Now the rule is narrower and better: a prefix the specification does not
    declare still warns, because guessing a base mints a wrong IRI."""
    result, graph = build(
        tmp_path, "# Decisions\n\n- D1 Cross-spec.\n  - affects: SBL:D14\n"
    )
    assert "does not declare under references:" in result.stderr
    assert graph.value(URIRef("https://example.org/specs/t#D1"), SPECL.affects) == Literal(
        "SBL:D14"
    )


def test_a_pytest_node_id_is_not_read_as_a_prefixed_token(tmp_path):
    """It carries colons and is an external artifact path, not a CURIE."""
    result, graph = build(
        tmp_path,
        "# Requirements\n\n- R1 Verified.\n  - verifiedBy: tests/test_a.py::test_b\n",
    )
    assert result.returncode == 0 and result.stderr == ""
    node = graph.value(URIRef("https://example.org/specs/t#R1"), SPECL.verifiedBy)
    assert isinstance(node, URIRef)
    assert (node, rdflib.RDF.type, SPECL.Test) in graph


def test_external_artifacts_become_typed_nodes_with_readable_iris(tmp_path):
    _, graph = build(
        tmp_path, "# Requirements\n\n- R1 Bound.\n  - constrains: spec_to_rdf\n"
    )
    node = graph.value(URIRef("https://example.org/specs/t#R1"), SPECL.constrains)
    assert node == URIRef("https://example.org/specs/t#component-spec_to_rdf")
    assert (node, rdflib.RDF.type, SPECL.Component) in graph


def test_one_node_per_artifact_however_many_items_reference_it(tmp_path):
    _, graph = build(
        tmp_path,
        "# Requirements\n\n- R1 A.\n  - constrains: shared\n- R2 B.\n  - constrains: shared\n",
    )
    nodes = set(graph.objects(None, SPECL.constrains))
    assert len(nodes) == 1
    assert len(list(graph.triples((next(iter(nodes)), rdflib.RDF.type, None)))) == 1


@pytest.mark.parametrize("name", PUBLISHED + FIXTURE_SPECS)
def test_no_object_property_carries_a_literal(name, tmp_path):
    """Invariant 7. The check that makes P1 unable to return."""
    target = tmp_path / f"{name}.ttl"
    translate(spec_path(name), target)
    graph = Graph().parse(target)
    offenders = [
        (str(s).split("#")[-1], str(p).split("#")[-1], str(o))
        for p in (SPECL.affects, SPECL.constrains, SPECL.verifiedBy, SPECL.partOf)
        for s, o in graph.subject_objects(p)
        if isinstance(o, Literal)
    ]
    assert not offenders


def test_a_declared_prefix_resolves_to_the_peer_base(tmp_path):
    """UR15. References resolve to IRIs always, through the prefix map declared
    in the referencing specification's own front matter."""
    source = tmp_path / "s.md"
    source.write_text(
        "---\ntitle: T\nspec_base: https://example.org/specs/t#\nspec_id: t-001\n"
        "references:\n  UP:\n    base: https://example.org/specs/up#\n"
        "    path: ./up.md\ndependsOn: UP\n---\n\n"
        "# Requirements\n\n- R1 Builds on it.\n  - affects: UP:R1\n"
    , encoding="utf-8")
    target = tmp_path / "s.ttl"
    result = translate(source, target)
    assert result.returncode == 0 and result.stderr == ""
    graph = Graph().parse(target)
    assert graph.value(URIRef("https://example.org/specs/t#R1"), SPECL.affects) == URIRef(
        "https://example.org/specs/up#R1"
    )


def test_a_declared_relation_points_at_the_peer_specification(tmp_path):
    source = tmp_path / "s.md"
    source.write_text(
        "---\ntitle: T\nspec_base: https://example.org/specs/t#\nspec_id: t-001\n"
        "references:\n  UP:\n    base: https://example.org/specs/up#\n"
        "    path: ./up.md\ndependsOn: UP\n---\n\n# Intent\nx\n"
    , encoding="utf-8")
    target = tmp_path / "s.ttl"
    translate(source, target)
    graph = Graph().parse(target)
    assert graph.value(URIRef("https://example.org/specs/t"), SPECL.dependsOn) == URIRef(
        "https://example.org/specs/up"
    )


def test_a_relation_naming_an_undeclared_peer_warns(tmp_path):
    source = tmp_path / "s.md"
    source.write_text(
        "---\ntitle: T\nspec_base: https://example.org/specs/t#\nspec_id: t-001\n"
        "dependsOn: GHOST\n---\n\n# Intent\nx\n"
    , encoding="utf-8")
    result = translate(source, tmp_path / "s.ttl")
    assert "is not declared under references:" in result.stderr


def test_a_foreign_base_is_held_to_the_same_grammar(tmp_path):
    """A foreign base becomes part of an IRI this specification emits."""
    source = tmp_path / "s.md"
    source.write_text(
        "---\ntitle: T\nspec_base: https://example.org/specs/t#\nspec_id: t-001\n"
        "references:\n  UP:\n    base: https://example.org/specs/up\n---\n\n# Intent\nx\n"
    , encoding="utf-8")
    result = translate(source, tmp_path / "s.ttl")
    assert "does not end in '#'" in result.stderr


def test_a_declared_range_is_enforced_not_merely_declared(tmp_path):
    """P1 fixed the literal half. The other half went unnoticed: reference
    resolution tries the identifier grammar first, so `constrains: R1` quietly
    produced a requirement in a position `core.ttl` reserves for a component,
    and nothing compared the emitted object against the declared range."""
    pytest.importorskip("pyshacl")
    from conftest import SHAPES
    from specl.validate_spec import load, run_shacl

    source = tmp_path / "s.md"
    source.write_text(
        "---\ntitle: T\nspec_base: https://example.org/specs/t#\nspec_id: t-001\n---\n\n"
        "# Requirements\n\n- R1 The engine must persist records durably.\n"
        "- R2 A requirement pointing constrains at another requirement.\n"
        "  - constrains: R1\n"
    , encoding="utf-8")
    target = tmp_path / "s.ttl"
    translate(source, target)
    _, results, _ = run_shacl(Graph().parse(target), load(SHAPES))
    assert any("declared range is specl:Component" in r["message"] for r in results)


def test_a_component_reference_does_not_trip_the_range_check(tmp_path):
    pytest.importorskip("pyshacl")
    from conftest import SHAPES
    from specl.validate_spec import load, run_shacl

    source = tmp_path / "s.md"
    source.write_text(
        "---\ntitle: T\nspec_base: https://example.org/specs/t#\nspec_id: t-001\n---\n\n"
        "# Requirements\n\n- R1 The engine must persist records durably.\n"
        "  - constrains: engine\n  - verifiedBy: tests/test_a.py::test_b\n"
    , encoding="utf-8")
    target = tmp_path / "s.ttl"
    translate(source, target)
    _, results, _ = run_shacl(Graph().parse(target), load(SHAPES))
    assert not [r for r in results if "declared range" in r["message"]]
