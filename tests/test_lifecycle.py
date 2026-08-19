"""Item lifecycle and supersession.

P6, 0.4.0. `decisionStatus` accepted `superseded` with nothing recording what
superseded the decision, and requirements had no status at all, so retiring one
meant deleting it. Deleting an identifier is what append-only discipline exists
to prevent: the reader is left with a gap and no way to find the replacement.
"""
from __future__ import annotations

import pytest

from conftest import SHAPES, subprocess_env, translate

pytest.importorskip("pyshacl")
from rdflib import Graph, Literal, Namespace, URIRef  # noqa: E402

from specl.validate_spec import load, run_shacl  # noqa: E402

SPECL = Namespace("https://w3id.org/specl/ns#")
BASE = "https://example.org/specs/t#"
HEAD = (
    f"---\ntitle: T\nspec_base: {BASE}\nspec_id: t-001\n"
    "version: 0.1.0\nstatus: draft\n---\n\n"
)


def build(tmp_path, body):
    source = tmp_path / "s.md"
    source.write_text(HEAD + body, encoding="utf-8")
    target = tmp_path / "s.ttl"
    result = translate(source, target)
    return result, Graph().parse(target)


def warnings_for(graph):
    _, results, _ = run_shacl(graph, load(SHAPES))
    return [r for r in results if r["severity"] == "Warning"]


def test_supersededby_resolves_to_an_iri(tmp_path):
    """Item to item, so it goes through reference resolution rather than
    becoming a literal."""
    result, graph = build(
        tmp_path,
        "# Requirements\n\n- R1 Retired.\n  - itemStatus: superseded\n"
        "  - supersededBy: R2\n- R2 Replacement.\n",
    )
    assert result.returncode == 0, result.stderr
    assert graph.value(URIRef(BASE + "R1"), SPECL.supersededBy) == URIRef(BASE + "R2")


def test_a_retired_item_keeps_its_identifier(tmp_path):
    _, graph = build(
        tmp_path,
        "# Requirements\n\n- R1 Retired.\n  - itemStatus: superseded\n"
        "  - supersededBy: R2\n- R2 Replacement.\n",
    )
    assert (URIRef(BASE + "R1"), SPECL.itemStatus, Literal("superseded")) in graph
    assert graph.value(URIRef(BASE + "R1"), SPECL.partOf) is not None


def test_superseded_without_a_replacement_warns(tmp_path):
    _, graph = build(
        tmp_path, "# Requirements\n\n- R1 Retired, orphaned.\n  - itemStatus: superseded\n"
    )
    messages = [w["message"] for w in warnings_for(graph)]
    assert any("should name the item that replaces it" in m for m in messages)


def test_an_active_item_does_not_warn_about_supersession(tmp_path):
    _, graph = build(
        tmp_path, "# Requirements\n\n- R1 Current.\n  - itemStatus: active\n"
    )
    messages = [w["message"] for w in warnings_for(graph)]
    assert not any("replaces it" in m for m in messages)


def test_an_unrecognized_lifecycle_value_warns(tmp_path):
    _, graph = build(
        tmp_path, "# Requirements\n\n- R1 Odd.\n  - itemStatus: retired\n"
    )
    messages = [w["message"] for w in warnings_for(graph)]
    assert any("active, superseded, or withdrawn" in m for m in messages)


def test_a_supersession_pointing_nowhere_warns(tmp_path):
    """The dangling-reference check applies here too, which is the point of
    routing supersededBy through reference resolution."""
    result, _ = build(
        tmp_path,
        "# Requirements\n\n- R1 Retired.\n  - itemStatus: superseded\n"
        "  - supersededBy: R99\n",
    )
    assert "no item in this specification declares" in result.stderr


def test_the_chain_is_queryable(tmp_path):
    """Exit criterion for 0.4.0: a query returns the supersession chain for any
    retired item, including through more than one hop."""
    _, graph = build(
        tmp_path,
        "# Requirements\n\n- R1 First.\n  - itemStatus: superseded\n  - supersededBy: R2\n"
        "- R2 Second.\n  - itemStatus: superseded\n  - supersededBy: R3\n- R3 Current.\n",
    )
    rows = list(graph.query(
        "PREFIX specl: <https://w3id.org/specl/ns#> "
        "SELECT ?retired ?current WHERE { ?retired specl:supersededBy+ ?current . "
        "FILTER NOT EXISTS { ?current specl:supersededBy ?later } }"
    ))
    pairs = {(str(a).split("#")[-1], str(b).split("#")[-1]) for a, b in rows}
    assert pairs == {("R1", "R3"), ("R2", "R3")}


# The committed semantics in docs/DOWNSTREAM-COMMITMENTS.md go further than
# marking an item retired. A first pass implemented the status and the successor
# link and stopped there, which under-delivered against a published commitment.


def test_a_retired_item_accumulates_no_other_warnings(tmp_path):
    """"Shapes do not evaluate it, except the shape requiring supersededBy."
    A retired requirement lacking a priority, an acceptance criterion, and
    everything else must not keep reporting them."""
    _, graph = build(
        tmp_path,
        "# Requirements\n\n- R1 Bare and retired.\n  - itemStatus: superseded\n"
        "  - supersededBy: R2\n- R2 Replacement.\n",
    )
    retired = str(URIRef(BASE + "R1"))
    assert not [w for w in warnings_for(graph) if w["focus"] == retired]


def test_a_live_item_with_the_same_gaps_does_warn(tmp_path):
    """The control. Without it, the test above would pass if the shapes had
    simply stopped working."""
    _, graph = build(tmp_path, "# Requirements\n\n- R1 Bare and live.\n")
    live = str(URIRef(BASE + "R1"))
    assert [w for w in warnings_for(graph) if w["focus"] == live]


def test_a_successor_of_a_different_class_warns(tmp_path):
    """"supersededBy requires a successor of the same class." Following the
    chain should not land the reader somewhere answering a different question."""
    _, graph = build(
        tmp_path,
        "# Requirements\n\n- R1 Retired.\n  - itemStatus: superseded\n  - supersededBy: D1\n\n"
        "# Decisions\n\n- D1 A decision.\n",
    )
    messages = [w["message"] for w in warnings_for(graph)]
    assert any("same class" in m for m in messages)


def test_a_withdrawn_item_naming_a_successor_warns(tmp_path):
    """"withdrawn is the no-successor case: struck, not replaced.\""""
    _, graph = build(
        tmp_path,
        "# Requirements\n\n- R1 Struck.\n  - itemStatus: withdrawn\n  - supersededBy: R2\n"
        "- R2 Something else.\n",
    )
    messages = [w["message"] for w in warnings_for(graph)]
    assert any("struck rather than replaced" in m for m in messages)


def test_a_successor_in_another_specification_warns(tmp_path):
    """"supersededBy requires a successor ... in the same specification.\""""
    _, one = build(
        tmp_path,
        "# Requirements\n\n- R1 Retired.\n  - itemStatus: superseded\n  - supersededBy: R2\n",
    )
    other = tmp_path / "other.md"
    other.write_text(
        "---\ntitle: Other\nspec_base: https://example.org/specs/o#\nspec_id: o-001\n---\n\n"
        "# Requirements\n\n- R2 Elsewhere.\n"
    , encoding="utf-8")
    other_ttl = tmp_path / "other.ttl"
    translate(other, other_ttl)
    merged = Graph()
    for triple in one:
        merged.add(triple)
    merged.parse(other_ttl)
    messages = [w["message"] for w in warnings_for(merged)]
    assert any("same specification" in m for m in messages)


def test_reusing_a_withdrawn_identifier_fails_the_diff(tmp_path):
    """"A withdrawn identifier is permanently reserved, and reuse is a violation
    rather than a warning."

    Only visible across two graphs: a single graph cannot see that an identifier
    used to mean something else, so this is a diff check rather than a shape.
    """
    import subprocess, sys as _sys
    from conftest import ROOT, SRC

    def write(name, body):
        path = tmp_path / f"{name}.md"
        path.write_text(HEAD + body, encoding="utf-8")
        out = tmp_path / f"{name}.ttl"
        translate(path, out)
        return out

    old = write("old", "# Requirements\n\n- R1 Struck for good.\n  - itemStatus: withdrawn\n")
    new = write("new", "# Requirements\n\n- R1 Something else entirely.\n  - itemStatus: active\n")
    result = subprocess.run(
        [_sys.executable, "-m", "specl.validate_spec", "diff", str(old), str(new)],
        cwd=tmp_path, env=subprocess_env(),
        capture_output=True, text=True,
    )
    assert result.returncode == 1
    assert "withdrawn identifier reused" in result.stdout


def test_a_withdrawn_identifier_staying_withdrawn_is_not_reuse(tmp_path):
    import subprocess, sys as _sys
    from conftest import SRC

    def write(name, body):
        path = tmp_path / f"{name}.md"
        path.write_text(HEAD + body, encoding="utf-8")
        out = tmp_path / f"{name}.ttl"
        translate(path, out)
        return out

    body = "# Requirements\n\n- R1 Struck for good.\n  - itemStatus: withdrawn\n"
    old, new = write("old", body), write("new", body)
    result = subprocess.run(
        [_sys.executable, "-m", "specl.validate_spec", "diff", str(old), str(new)],
        cwd=tmp_path, env=subprocess_env(),
        capture_output=True, text=True,
    )
    assert result.returncode == 0 and "reused" not in result.stdout
