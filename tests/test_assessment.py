"""Maturity, progress, and assessments as data.

P4. Maturity existed as a transient number and a committed image: not in the
vocabulary, not in the graph, not queryable. So there was no history, no trend,
no attribution, and a metric that counted requirements only while a
specification's unanswered questions sat in classes it could not see.

The four tests named for exit criteria are the 0.8.0 list.
"""
from __future__ import annotations

import subprocess
import sys

import pytest

from conftest import ROOT, SHAPES, SRC, translate

pytest.importorskip("pyshacl")
from rdflib import Graph, Namespace, URIRef  # noqa: E402

from specl.validate_spec import load, score_graph  # noqa: E402

SPECL = Namespace("https://w3id.org/specl/ns#")
PROV = Namespace("http://www.w3.org/ns/prov#")
BASE = "https://example.org/specs/t#"
HEAD = f"---\ntitle: T\nspec_base: {BASE}\nspec_id: t-001\n---\n\n"

CLEAN = (
    "  - priority: {priority}\n  - acceptance: Given X when Y then Z\n"
    "  - verifiedBy: tests/test_a.py::test_b\n  - constrains: engine\n"
)


def graph_for(tmp_path, body, name="s"):
    source = tmp_path / f"{name}.md"
    source.write_text(HEAD + body, encoding="utf-8")
    target = tmp_path / f"{name}.ttl"
    assert translate(source, target).returncode == 0
    return target, Graph().parse(target)


def score(tmp_path, body, name="s"):
    return score_graph(graph_for(tmp_path, body, name)[1], load(SHAPES))


def run_score(target, *extra):
    return subprocess.run(
        [sys.executable, "-m", "specl.validate_spec", "score", str(target), str(SHAPES), *extra],
        cwd=ROOT, env={"PYTHONPATH": str(SRC), "PATH": "/usr/bin:/bin"},
        capture_output=True, text=True,
    )


def test_criterion_1_a_history_graph_answers_the_trend(tmp_path):
    target, _ = graph_for(tmp_path, "# Requirements\n\n- R1 The system must persist records durably across restarts.\n" + CLEAN.format(priority="MUST"))
    history = tmp_path / "history.ttl"
    for at in ("2026-01-01T00:00:00Z", "2026-02-01T00:00:00Z", "2026-03-01T00:00:00Z"):
        assert run_score(target, "--history", str(history), "--at", at).returncode == 0
    rows = list(Graph().parse(history).query(
        "PREFIX specl: <https://w3id.org/specl/ns#> "
        "PREFIX prov: <http://www.w3.org/ns/prov#> "
        "SELECT ?at ?score WHERE { ?a a specl:MaturityAssessment ; "
        "prov:generatedAtTime ?at ; specl:maturityScore ?score } ORDER BY ?at"
    ))
    assert len(rows) == 3
    assert [str(r[0])[:7] for r in rows] == ["2026-01", "2026-02", "2026-03"]


def test_criterion_2_unresolved_open_issues_prevent_a_perfect_score(tmp_path):
    """A metric that cannot see open issues cannot tell a mature specification
    from one that has not asked itself anything."""
    without = score(tmp_path, "# Requirements\n\n- R1 The system must persist records durably across restarts.\n" + CLEAN.format(priority="MUST"), "a")
    withan = score(
        tmp_path,
        "# Requirements\n\n- R1 The system must persist records durably across restarts.\n" + CLEAN.format(priority="MUST")
        + "\n# Open Questions\n\n- OQ1 Whether the store should be embedded or external.\n  - status: open\n",
        "b",
    )
    assert without["score"] == 100
    assert withan["score"] < 100


def test_criterion_3_progress_and_maturity_are_separable(tmp_path):
    """Marking something built changes progress and must not change maturity."""
    body = "# Requirements\n\n- R1 The system must persist records durably across restarts.\n" + CLEAN.format(priority="MUST")
    before = score(tmp_path, body, "a")
    after = score(tmp_path, body + "  - implementation: verified\n", "b")
    assert after["progress"] > before["progress"]
    assert after["score"] == before["score"]


def test_criterion_4_priority_distribution_changes_the_score(tmp_path):
    """Identical finding counts, different priorities. A clean MUST and a clean
    COULD do not contribute equally."""
    dirty_must = score(
        tmp_path,
        "# Requirements\n\n- R1 The system must handle concurrent writes without loss.\n  - priority: MUST\n"
        "- R2 The system must expose a readable status endpoint.\n" + CLEAN.format(priority="WONT"),
        "a",
    )
    dirty_wont = score(
        tmp_path,
        "# Requirements\n\n- R1 The system must handle concurrent writes without loss.\n  - priority: WONT\n"
        "- R2 The system must expose a readable status endpoint.\n" + CLEAN.format(priority="MUST"),
        "b",
    )
    assert dirty_must["score"] != dirty_wont["score"]
    assert dirty_must["score"] < dirty_wont["score"]


def test_subscores_attribute_the_number(tmp_path):
    report = score(
        tmp_path,
        "# Requirements\n\n- R1 The system must persist records durably across restarts.\n\n# User Stories\n\n- US1 As an operator, I want a durable store, so that restarts are safe.\n\n"
        "# Open Questions\n\n- OQ1 Whether the store should be embedded or external.\n",
    )
    assert set(report["subscores"]) == {"Requirement", "UserStory", "OpenIssue"}


def test_scoring_writes_nothing_unless_asked(tmp_path):
    """A CI run that only reports must not accumulate a log."""
    target, _ = graph_for(tmp_path, "# Requirements\n\n- R1 The system must persist records durably across restarts.\n")
    before = set(tmp_path.iterdir())
    assert run_score(target).returncode == 0
    assert set(tmp_path.iterdir()) == before


def test_the_badge_renders_the_latest_recorded_assessment(tmp_path):
    target, _ = graph_for(tmp_path, "# Requirements\n\n- R1 The system must persist records durably across restarts.\n" + CLEAN.format(priority="MUST"))
    history = tmp_path / "history.ttl"
    run_score(target, "--history", str(history), "--at", "2026-01-01T00:00:00Z")
    out = tmp_path / "b.svg"
    result = subprocess.run(
        [sys.executable, "-m", "specl.validate_spec", "badge", str(target), str(SHAPES),
         "--history", str(history), "--out", str(out)],
        cwd=ROOT, env={"PYTHONPATH": str(SRC), "PATH": "/usr/bin:/bin"},
        capture_output=True, text=True,
    )
    assert result.returncode == 0
    assert "latest recorded assessment" in result.stdout
    assert "100%" in out.read_text(encoding="utf-8")


def test_retiring_an_item_does_not_raise_the_score(tmp_path):
    """Found by adding a withdrawn requirement to a trial specification and
    watching maturity go from 90% to 91%.

    Retired items are not evaluated by the shapes, so leaving them in the
    population counted every one as clean. A metric that rewards striking things
    out measures the wrong thing.
    """
    body = "# Requirements\n\n- R1 The service must accept uploads of any size.\n"
    live = score(tmp_path, body, "a")
    with_retired = score(
        tmp_path,
        body + "- R2 The service must accept ZIP archives.\n"
               "  - itemStatus: withdrawn\n",
        "b",
    )
    assert with_retired["score"] == live["score"]
    assert with_retired["total"] == live["total"]


def test_progress_is_asked_only_of_what_gets_built(tmp_path):
    """A decision record has no implementation. Counting one as not-started made
    a specification look less built the more thinking it recorded."""
    body = (
        "# Requirements\n\n- R1 The service must accept uploads of any size.\n"
        "  - implementation: verified\n"
    )
    without = score(tmp_path, body, "a")
    with_decision = score(
        tmp_path,
        body + "\n# Decisions\n\n- D1 Use a queue between upload and extraction.\n",
        "b",
    )
    assert with_decision["progress"] == without["progress"] == 100


def test_the_breakdown_explains_the_headline(tmp_path):
    """Subscores were computed over a different population than the score."""
    report = score(
        tmp_path,
        "# Requirements\n\n- R1 The service must accept uploads of any size.\n"
        "- R2 The service must accept ZIP archives.\n  - itemStatus: withdrawn\n",
    )
    assert sum(total for _, total in report["subscores"].values()) == report["total"]
