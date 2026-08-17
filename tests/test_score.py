"""Maturity, and the two disagreements it used to allow.

P13. A specification carrying a Violation could score 100% and render a green
badge while the gate failed it. Separately, findings against decisions and open
issues were collected and then discarded, because the population was
requirements only, so a specification could read clean while its decisions were
malformed.
"""
from __future__ import annotations

import pytest

from conftest import PUBLISHED, SHAPES, spec_path, translate

pytest.importorskip("pyshacl")
from rdflib import Graph, URIRef  # noqa: E402

from specl.validate_spec import items, load, score_graph  # noqa: E402

DCT_TITLE = URIRef("http://purl.org/dc/terms/title")
HEAD = (
    "---\ntitle: T\nspec_base: https://example.org/specs/t#\n"
    "spec_id: t-001\nversion: 0.1.0\nstatus: draft\n---\n\n"
)


def graph_for(tmp_path, body, name="s"):
    source = tmp_path / f"{name}.md"
    source.write_text(HEAD + body, encoding="utf-8")
    target = tmp_path / f"{name}.ttl"
    translate(source, target)
    return Graph().parse(target)


CLEAN_REQUIREMENT = (
    "# Requirements\n\n- R1 A requirement that is fully annotated.\n"
    "  - priority: MUST\n  - acceptance: Given X when Y then Z\n"
    "  - verifiedBy: tests/test_a.py::test_b\n  - constrains: engine\n"
)


def test_the_population_is_every_item_not_only_requirements(tmp_path):
    g = graph_for(
        tmp_path,
        "# Requirements\n\n- R1 A.\n\n# User Stories\n\n- US1 B.\n\n"
        "# Decisions\n\n- D1 C.\n\n# Open Questions\n\n- OQ1 D.\n",
    )
    assert len(items(g)) == 4


def test_a_failing_gate_reports_no_percentage(tmp_path):
    """A maturity number for a specification that does not validate describes
    nothing, and a green badge over a failing gate is a false public claim."""
    g = graph_for(tmp_path, "# Requirements\n\n- R1 A requirement.\n")
    g.remove((URIRef("https://example.org/specs/t"), DCT_TITLE, None))
    report = score_graph(g, load(SHAPES))
    assert report["gate_failed"] and report["violations"] == 1
    assert report["score"] is None


def test_a_passing_gate_reports_a_percentage(tmp_path):
    g = graph_for(tmp_path, "# Requirements\n\n- R1 A requirement.\n")
    report = score_graph(g, load(SHAPES))
    assert not report["gate_failed"]
    assert isinstance(report["score"], int)


def test_a_malformed_decision_lowers_the_score(tmp_path):
    """It used to be invisible: the finding matched no requirement and was
    discarded."""
    clean = graph_for(tmp_path, CLEAN_REQUIREMENT, name="clean")
    dirty = graph_for(
        tmp_path,
        CLEAN_REQUIREMENT + "\n# Decisions\n\n- D1 A decision with no status.\n",
        name="dirty",
    )
    a = score_graph(clean, load(SHAPES))
    b = score_graph(dirty, load(SHAPES))
    assert a["score"] == 100, a
    assert b["score"] < 100, b


@pytest.mark.parametrize("name", PUBLISHED)
def test_score_and_gate_never_disagree_in_sign(name, tmp_path):
    """Exit criterion 8 for 0.3.0."""
    target = tmp_path / f"{name}.ttl"
    translate(spec_path(name), target)
    report = score_graph(Graph().parse(target), load(SHAPES))
    assert (report["score"] is None) == report["gate_failed"]
