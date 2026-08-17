"""Nested content under an item, and the line between content and a typo.

R1.8 in `specs/specl_tool/spec.md`. An indented bullet naming a known
annotation key stays an annotation at any depth, which is what keeps
specifications authored against "two or more spaces" working. Everything else
splits on column: content at four or more, probable typo below.
"""
from __future__ import annotations

import pytest

from conftest import translate

BASE = "spec_base: https://example.org/specs/t#\n"
HEAD = "---\ntitle: T\n" + BASE + "spec_id: t-001\nversion: 0.1.0\nstatus: draft\n---\n\n"


def run(tmp_path, body):
    source = tmp_path / "s.md"
    source.write_text(f"{HEAD}# Requirements\n\n{body}", encoding="utf-8")
    target = tmp_path / "s.ttl"
    result = translate(source, target)
    return result, target.read_text(encoding="utf-8")


def test_nested_content_becomes_detail(tmp_path):
    result, out = run(
        tmp_path,
        "- R1 Fields render in order:\n"
        "    - Requirement: description, priority\n"
        "    - UserStory: description, as a\n",
    )
    assert result.returncode == 0
    assert "0 parser warning(s)" in result.stdout
    assert "specl:detail" in out
    assert out.index("Requirement: description") < out.index("UserStory: description")


def test_detail_is_a_real_rdf_list_with_named_cells(tmp_path):
    """Standard list tooling must work, and no blank node may appear."""
    rdflib = pytest.importorskip("rdflib")
    from rdflib import Graph, Namespace, BNode
    from rdflib.collection import Collection

    _, _ = run(tmp_path, "- R1 In order:\n    - alpha\n    - beta\n    - gamma\n")
    graph = Graph().parse(tmp_path / "s.ttl")
    specl = Namespace("https://w3id.org/specl/ns#")
    head = next(graph.objects(None, specl.detail))
    assert [str(x) for x in Collection(graph, head)] == ["alpha", "beta", "gamma"]
    assert not any(isinstance(n, BNode) for n in graph.all_nodes())


def test_property_path_traversal_returns_every_line(tmp_path):
    rdflib = pytest.importorskip("rdflib")
    from rdflib import Graph

    run(tmp_path, "- R1 In order:\n    - alpha\n    - beta\n")
    graph = Graph().parse(tmp_path / "s.ttl")
    rows = list(graph.query(
        "PREFIX specl: <https://w3id.org/specl/ns#> "
        "SELECT ?line WHERE { ?r specl:detail/rdf:rest*/rdf:first ?line }"
    ))
    assert sorted(str(r[0]) for r in rows) == ["alpha", "beta"]


def test_diff_does_not_report_a_list_as_changed_against_itself(tmp_path):
    """The reason the cells have IRIs. Blank node labels are regenerated on
    every parse, so a list-bearing requirement would always look modified."""
    rdflib = pytest.importorskip("rdflib")
    from rdflib import Graph
    from specl.validate_spec import _req_map

    run(tmp_path, "- R1 In order:\n    - alpha\n    - beta\n")
    target = tmp_path / "s.ttl"
    assert _req_map(Graph().parse(target)) == _req_map(Graph().parse(target))


def test_two_column_unknown_key_still_warns(tmp_path):
    result, _ = run(tmp_path, "- R1 A requirement.\n  - priorty: MUST\n")
    assert "annotation key" in result.stderr


def test_known_key_at_four_columns_is_still_an_annotation(tmp_path):
    """SYNTAX.md permits two or more spaces, so deep annotations must keep
    working rather than silently becoming content."""
    result, out = run(tmp_path, "- R1 A requirement.\n    - priority: MUST\n")
    assert result.returncode == 0
    assert "specl:priority" in out and "specl:detail" not in out


def test_nested_content_preserves_order_and_does_not_touch_description(tmp_path):
    _, out = run(
        tmp_path,
        "- R1 A requirement.\n    - alpha\n    - beta\n    - gamma\n",
    )
    assert 'dct:description "A requirement."' in out
    assert out.index("alpha") < out.index("beta") < out.index("gamma")
