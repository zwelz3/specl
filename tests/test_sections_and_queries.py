"""Open sections and acceptance queries.

P7 and the acceptance query class. An unrecognized heading used to drop its
content in silence, which is how three open questions and a nested field
ordering vanished from specl's own specifications. A query set is arguably the
only part of a specification that can falsify the rest, which is what earns it a
class rather than a home outside the graph.
"""
from __future__ import annotations

import pytest

from conftest import specl_warnings, translate

rdflib = pytest.importorskip("rdflib")
from rdflib import Graph, Namespace, URIRef  # noqa: E402

SPECL = Namespace("https://w3id.org/specl/ns#")
BASE = "https://example.org/specs/t#"


def build(tmp_path, body, front=""):
    source = tmp_path / "s.md"
    source.write_text(
        f"---\ntitle: T\nspec_base: {BASE}\nspec_id: t-001\n{front}---\n\n{body}"
    , encoding="utf-8")
    target = tmp_path / "s.ttl"
    result = translate(source, target)
    return result, Graph().parse(target)


def test_an_unrecognized_heading_warns_rather_than_vanishing(tmp_path):
    result, _ = build(tmp_path, "# Scratch\n\nContent nobody will ever see.\n")
    assert "is not a recognized heading" in result.stderr
    assert "Scratch" in result.stderr


def test_a_parked_heading_does_not_warn(tmp_path):
    """UR10's pre-adoption path: author the content now under a marker, and
    adoption becomes deleting the marker rather than rewriting the section."""
    result, _ = build(
        tmp_path,
        "# Verification Notes\n<!--specl: parked, no class models this yet-->\n\nProse.\n",
    )
    assert result.returncode == 0 and not specl_warnings(result.stderr)


def test_a_heading_mapped_in_front_matter_produces_items(tmp_path):
    result, graph = build(
        tmp_path,
        "# Constraints\n\n- R9 A requirement under a project heading.\n",
        front="sections:\n  Constraints: Requirement\n",
    )
    assert result.returncode == 0, result.stderr
    assert (URIRef(BASE + "R9"), rdflib.RDF.type, SPECL.Requirement) in graph


def test_mapping_onto_a_class_specl_does_not_declare_warns(tmp_path):
    """Extending the map is not inventing a class. An item still has to be
    something the vocabulary declares and the shapes evaluate."""
    result, _ = build(
        tmp_path, "# Constraints\n\n- R9 A.\n", front="sections:\n  Constraints: Widget\n"
    )
    assert "is not a class specl declares" in result.stderr


def test_a_query_gates_requirements_by_iri(tmp_path):
    result, graph = build(
        tmp_path,
        "# Requirements\n\n- R8 Persist durably.\n\n"
        "# Acceptance Queries\n\n- Q001 Every record survives a restart.\n  - gates: R8\n",
    )
    assert result.returncode == 0, result.stderr
    query = URIRef(BASE + "Q001")
    assert (query, rdflib.RDF.type, SPECL.AcceptanceQuery) in graph
    assert graph.value(query, SPECL.gates) == URIRef(BASE + "R8")


def test_a_requirement_is_reachable_from_the_query_that_gates_it(tmp_path):
    """The 0.6.0 exit criterion, and the reason queries are in the graph."""
    _, graph = build(
        tmp_path,
        "# Requirements\n\n- R8 A.\n- R9 B.\n\n"
        "# Acceptance Queries\n\n- Q001 Both hold.\n  - gates: R8, R9\n",
    )
    rows = list(graph.query(
        "PREFIX specl: <https://w3id.org/specl/ns#> "
        "SELECT ?req WHERE { ?q a specl:AcceptanceQuery ; specl:gates ?req }"
    ))
    assert {str(r[0]).split("#")[-1] for r in rows} == {"R8", "R9"}


def test_a_query_gating_a_missing_requirement_warns(tmp_path):
    result, _ = build(
        tmp_path, "# Acceptance Queries\n\n- Q001 Nothing to gate.\n  - gates: R99\n"
    )
    assert "no item in this specification declares" in result.stderr


def test_the_consumers_padded_identifier_form_works(tmp_path):
    """The consumer restructured its query set as `Q001` bullets on this answer,
    so the padded form has to parse."""
    _, graph = build(tmp_path, "# Acceptance Queries\n\n- Q001 A query.\n")
    assert (URIRef(BASE + "Q001"), rdflib.RDF.type, SPECL.AcceptanceQuery) in graph
