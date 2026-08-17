"""Source provenance per item, and the timestamp that must not be automatic.

P9. `prov:` was bound in the header and no code path emitted a `prov:` triple.
The interesting part is not the derivation link but the constraint around the
timestamp: exit criterion 6 for 0.3.0 is that the same source produces
byte-identical output, so a translator that reads the clock breaks that and every
golden file with it.
"""
from __future__ import annotations

import pytest

from conftest import PUBLISHED, FIXTURE_SPECS, spec_path, translate

rdflib = pytest.importorskip("rdflib")
from rdflib import Graph, Literal, Namespace, URIRef  # noqa: E402

SPECL = Namespace("https://w3id.org/specl/ns#")
PROV = Namespace("http://www.w3.org/ns/prov#")
BASE = "https://example.org/specs/t#"
HEAD = f"---\ntitle: T\nspec_base: {BASE}\nspec_id: t-001\n---\n\n"


def build(tmp_path, body, *flags):
    source = tmp_path / "s.md"
    source.write_text(HEAD + body, encoding="utf-8")
    target = tmp_path / "s.ttl"
    result = translate(source, target, *flags)
    return result, Graph().parse(target)


def test_the_recorded_line_indexes_the_file_as_authored(tmp_path):
    """Front matter and comment blocks are blanked rather than removed, because
    a source reference pointing at the wrong line is worse than none."""
    source = tmp_path / "s.md"
    source.write_text(HEAD + "# Requirements\n\n- R1 First.\n- R2 Second.\n", encoding="utf-8")
    target = tmp_path / "s.ttl"
    translate(source, target)
    graph = Graph().parse(target)
    lines = source.read_text(encoding="utf-8").splitlines()
    for item, text in [("R1", "- R1 First."), ("R2", "- R2 Second.")]:
        recorded = int(graph.value(URIRef(BASE + item), SPECL.sourceLine))
        assert lines[recorded - 1] == text


def test_each_item_points_at_a_source_document(tmp_path):
    _, graph = build(tmp_path, "# Requirements\n\n- R1 A.\n")
    doc = graph.value(URIRef(BASE + "R1"), PROV.wasDerivedFrom)
    assert isinstance(doc, URIRef)
    assert (doc, rdflib.RDF.type, SPECL.SourceDocument) in graph
    assert graph.value(doc, URIRef("http://purl.org/dc/terms/identifier")) == Literal("s.md")


def test_the_source_is_the_file_name_not_the_path_given(tmp_path):
    """A graph must not differ because it was translated from a different
    working directory."""
    nested = tmp_path / "deep" / "deeper"
    nested.mkdir(parents=True)
    source = nested / "s.md"
    source.write_text(HEAD + "# Requirements\n\n- R1 A.\n", encoding="utf-8")
    flat = tmp_path / "s.md"
    flat.write_text(source.read_text(encoding="utf-8"))
    a, b = tmp_path / "a.ttl", tmp_path / "b.ttl"
    translate(source, a)
    translate(flat, b)
    assert a.read_text(encoding="utf-8") == b.read_text(encoding="utf-8")


def test_no_timestamp_is_emitted_by_default(tmp_path):
    _, graph = build(tmp_path, "# Requirements\n\n- R1 A.\n")
    assert not list(graph.objects(None, PROV.generatedAtTime))


def test_a_supplied_timestamp_records_a_translation_activity(tmp_path):
    _, graph = build(
        tmp_path, "# Requirements\n\n- R1 A.\n", "--generated-at", "2026-08-16T12:00:00Z"
    )
    activity = graph.value(URIRef(BASE[:-1]), PROV.wasGeneratedBy)
    assert (activity, rdflib.RDF.type, PROV.Activity) in graph
    assert graph.value(activity, PROV.generatedAtTime) == Literal(
        "2026-08-16T12:00:00Z", datatype=URIRef("http://www.w3.org/2001/XMLSchema#dateTime")
    )


@pytest.mark.parametrize("name", PUBLISHED + FIXTURE_SPECS)
def test_provenance_does_not_break_determinism(name, tmp_path):
    a, b = tmp_path / "a.ttl", tmp_path / "b.ttl"
    translate(spec_path(name), a)
    translate(spec_path(name), b)
    assert a.read_text(encoding="utf-8") == b.read_text(encoding="utf-8")


@pytest.mark.parametrize("name", PUBLISHED)
def test_every_item_carries_a_resolvable_source_reference(name, tmp_path):
    """The 0.7.0 exit criterion."""
    target = tmp_path / f"{name}.ttl"
    translate(spec_path(name), target)
    graph = Graph().parse(target)
    items = set(graph.subjects(SPECL.partOf, None))
    assert items
    for item in items:
        assert graph.value(item, PROV.wasDerivedFrom) is not None
        assert graph.value(item, SPECL.sourceLine) is not None


def test_a_query_answers_which_line_produced_an_item(tmp_path):
    """The other half of the exit criterion."""
    _, graph = build(tmp_path, "# Requirements\n\n- R1 A.\n- R2 B.\n")
    rows = list(graph.query(
        "PREFIX specl: <https://w3id.org/specl/ns#> "
        "PREFIX prov: <http://www.w3.org/ns/prov#> "
        "PREFIX dct: <http://purl.org/dc/terms/> "
        "SELECT ?item ?file ?line WHERE { "
        "  ?item prov:wasDerivedFrom ?doc ; specl:sourceLine ?line . "
        "  ?doc dct:identifier ?file }"
    ))
    assert {(str(i).split("#")[-1], str(f)) for i, f, _ in rows} == {
        ("R1", "s.md"), ("R2", "s.md")
    }
