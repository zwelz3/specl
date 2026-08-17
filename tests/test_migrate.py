"""`specl-migrate iris`, for a consumer holding only Turtle.

A project with the markdown regenerates instead, and gets titles, IRI-valued
references, and the contract declaration along with the new base. This tool
moves identifiers and nothing else, which is why it says so on the way out.
"""
from __future__ import annotations

import subprocess
import sys

import pytest

from conftest import FIXTURES, ROOT, SRC

rdflib = pytest.importorskip("rdflib")
from rdflib import Graph, Literal, Namespace, URIRef  # noqa: E402

SPECL = Namespace("https://w3id.org/specl/ns#")
LEGACY = FIXTURES / "legacy" / "pre-0.3.0.ttl"
BASE = "https://example.org/specs/excel_service#"


def run(*args):
    return subprocess.run(
        [sys.executable, "-m", "specl.migrate", *args],
        cwd=ROOT,
        env={"PYTHONPATH": str(SRC), "PATH": "/usr/bin:/bin"},
        capture_output=True,
        text=True,
    )


@pytest.fixture
def migrated(tmp_path):
    target = tmp_path / "out.ttl"
    result = run("iris", str(LEGACY), str(target), "--spec-base", BASE)
    assert result.returncode == 0, result.stderr
    return Graph().parse(target), result


def test_items_move_by_concatenation(migrated):
    graph, _ = migrated
    assert (URIRef(BASE + "R1.1"), rdflib.RDF.type, SPECL.Requirement) in graph
    assert (URIRef(BASE + "US1"), rdflib.RDF.type, SPECL.UserStory) in graph


def test_the_specification_drops_its_identifier_from_the_iri(migrated):
    """The second mapping rule. An item is a prefix substitution; the
    Specification becomes the base without its terminator, losing spec_id."""
    graph, _ = migrated
    assert (URIRef(BASE[:-1]), rdflib.RDF.type, SPECL.Specification) in graph
    assert (URIRef(BASE + "xlsvc-001"), rdflib.RDF.type, SPECL.Specification) not in graph


def test_nothing_remains_under_the_retired_namespace(migrated):
    graph, _ = migrated
    assert not [
        n for n in graph.all_nodes()
        if isinstance(n, URIRef) and str(n).startswith("https://w3id.org/specl/spec#")
    ]


DCT = "http://purl.org/dc/terms/"


def test_authored_content_is_untouched(migrated):
    graph, _ = migrated
    assert graph.value(URIRef(BASE[:-1]), URIRef(DCT + "title")) == Literal("Excel Service")
    assert graph.value(URIRef(BASE + "R1.1"), SPECL.priority) == Literal("MUST")


def test_reference_properties_become_iris(migrated):
    """The roadmap specifies conversion, not only rebasing. A migrated graph
    should match what regenerating from the markdown would have produced."""
    graph, _ = migrated
    assert graph.value(URIRef(BASE + "D1"), SPECL.affects) == URIRef(BASE + "R1.1")
    component = graph.value(URIRef(BASE + "R1.1"), SPECL.constrains)
    assert component == URIRef(BASE + "component-api_layer")
    assert (component, rdflib.RDF.type, SPECL.Component) in graph


def test_titles_are_derived_for_items_that_lack_them(migrated):
    """The derivation is deterministic and specified, so applying it here
    produces the values regenerating would rather than inventing any."""
    graph, result = migrated
    assert graph.value(URIRef(BASE + "R1.1"), URIRef(DCT + "title")) == Literal(
        "The service must expose an HTTP POST endpoint"
    )
    assert "3 titles derived" in result.stdout


def test_the_old_spec_id_survives_as_an_identifier(migrated):
    """It was the local name of the old Specification IRI, and 0.3.0 keeps it
    as dct:identifier, so it is recoverable rather than lost."""
    graph, _ = migrated
    assert graph.value(URIRef(BASE[:-1]), URIRef(DCT + "identifier")) == Literal("xlsvc-001")


def test_the_result_declares_the_contract(migrated):
    graph, _ = migrated
    assert graph.value(URIRef(BASE[:-1]), URIRef(DCT + "conformsTo")) == URIRef(
        "https://w3id.org/specl/contract/2"
    )


def test_what_cannot_be_recovered_is_stated(migrated):
    _, result = migrated
    assert "cannot be recovered from" in result.stderr


def test_a_merged_legacy_graph_is_refused(tmp_path):
    """The collision is not recoverable. Which specification an item belonged to
    is exactly the information the shared namespace destroyed."""
    merged = tmp_path / "merged.ttl"
    merged.write_text(
        LEGACY.read_text(encoding="utf-8")
        + '\nspec:pptxgen-001 a specl:Specification ; dct:title "PPTX" .\n'
    )
    result = run("iris", str(merged), str(tmp_path / "o.ttl"), "--spec-base", BASE)
    assert result.returncode == 2
    assert "no longer recoverable" in result.stderr


def test_the_base_grammar_applies(tmp_path):
    result = run("iris", str(LEGACY), str(tmp_path / "o.ttl"),
                 "--spec-base", "https://example.org/specs/x")
    assert result.returncode == 2 and "does not end in '#'" in result.stderr


def test_a_migrated_graph_is_left_alone(tmp_path):
    once, twice = tmp_path / "a.ttl", tmp_path / "b.ttl"
    run("iris", str(LEGACY), str(once), "--spec-base", BASE)
    result = run("iris", str(once), str(twice), "--spec-base", BASE)
    assert result.returncode == 0 and "nothing to migrate" in result.stdout


def test_it_refuses_to_overwrite_its_input(tmp_path):
    target = tmp_path / "a.ttl"
    target.write_text(LEGACY.read_text(encoding="utf-8"))
    result = run("iris", str(target), str(target), "--spec-base", BASE)
    assert result.returncode == 2 and "refusing to overwrite" in result.stderr


def test_dry_run_reports_without_writing(tmp_path):
    target = tmp_path / "o.ttl"
    result = run("iris", str(LEGACY), str(target), "--spec-base", BASE, "--dry-run")
    assert result.returncode == 0
    assert not target.exists()
    assert "IRIs would move" in result.stdout


def test_diff_ignore_base_sees_a_rebased_graph_as_the_same_items(tmp_path):
    """Without the flag, a migration reads as every requirement removed and
    re-added. The reader is comparing identifiers, not IRIs."""
    from specl.validate_spec import _req_map, load as load_graph

    target = tmp_path / "new.ttl"
    run("iris", str(LEGACY), str(target), "--spec-base", BASE)
    old, new = load_graph(LEGACY), load_graph(target)

    by_iri = set(_req_map(old)) ^ set(_req_map(new))
    assert by_iri, "keying by IRI, nothing lines up"

    by_token = set(_req_map(old, ignore_base=True)) ^ set(
        _req_map(new, ignore_base=True)
    )
    assert not by_token
