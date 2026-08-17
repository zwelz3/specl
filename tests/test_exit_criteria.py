"""The 0.3.0 exit criteria, as executable checks.

`docs/ROADMAP.md` lists nine. Eight are properties of the code and are asserted
here, so "did 0.3.0 ship" is answerable by running the suite rather than by
reading the roadmap and trusting it. The ninth is the upstream w3id pull
request, which is not a property of this repository.
"""
from __future__ import annotations

import itertools

import pytest

from conftest import PUBLISHED, FIXTURE_SPECS, ROOT, SHAPES, spec_path, translate

pytest.importorskip("pyshacl")
from rdflib import Graph, Literal, Namespace, URIRef  # noqa: E402

from specl.validate_spec import load, run_shacl, score_graph  # noqa: E402

SPECL = Namespace("https://w3id.org/specl/ns#")
ALL = PUBLISHED + FIXTURE_SPECS


def graph(name, tmp_path):
    target = tmp_path / f"{name}.ttl"
    assert translate(spec_path(name), target).returncode == 0
    return Graph().parse(target)


@pytest.mark.parametrize("a,b", list(itertools.combinations(ALL, 2)),
                         ids=[f"{a}+{b}" for a, b in itertools.combinations(ALL, 2)])
def test_criterion_1_merging_any_two_yields_no_shared_item_iri(a, b, tmp_path):
    ga, gb = graph(a, tmp_path), graph(b, tmp_path)
    ia = {str(s) for s in ga.subjects(SPECL.partOf, None)}
    ib = {str(s) for s in gb.subjects(SPECL.partOf, None)}
    assert not ia & ib


def test_criterion_2_a_missing_base_fails_with_an_actionable_message(tmp_path):
    source = tmp_path / "s.md"
    source.write_text("---\ntitle: T\nspec_id: t-001\n---\n\n# Requirements\n\n- R1 A.\n", encoding="utf-8")
    result = translate(source, tmp_path / "s.ttl")
    assert result.returncode == 2
    assert "spec_base is required" in result.stderr and "SYNTAX.md" in result.stderr


def test_criterion_3_a_decisions_section_validates(tmp_path):
    source = tmp_path / "s.md"
    source.write_text(
        "---\ntitle: T\nspec_base: https://example.org/specs/t#\nspec_id: t-001\n---\n\n"
        "# Decisions\n\n- D1 Use SQLite.\n  - status: accepted\n  - rationale: One file.\n"
    , encoding="utf-8")
    target = tmp_path / "s.ttl"
    translate(source, target)
    _, results, _ = run_shacl(Graph().parse(target), load(SHAPES))
    assert not [r for r in results if r["severity"] == "Violation"]


def test_criterion_4_affects_is_traversable(tmp_path):
    source = tmp_path / "s.md"
    source.write_text(
        "---\ntitle: T\nspec_base: https://example.org/specs/t#\nspec_id: t-001\n---\n\n"
        "# Requirements\n\n- R8 Persist durably.\n\n"
        "# Decisions\n\n- D1 Use SQLite.\n  - affects: R8\n"
    , encoding="utf-8")
    target = tmp_path / "s.ttl"
    translate(source, target)
    rows = list(Graph().parse(target).query(
        "PREFIX specl: <https://w3id.org/specl/ns#> "
        "PREFIX dct: <http://purl.org/dc/terms/> "
        "SELECT ?d WHERE { ?d specl:affects ?r . ?r a specl:Requirement }"
    ))
    assert len(rows) == 1


@pytest.mark.parametrize("name", ALL)
def test_criterion_6_translation_is_byte_identical(name, tmp_path):
    a, b = tmp_path / "a.ttl", tmp_path / "b.ttl"
    translate(spec_path(name), a)
    translate(spec_path(name), b)
    assert a.read_text(encoding="utf-8") == b.read_text(encoding="utf-8")


@pytest.mark.parametrize("name", ALL)
def test_criterion_8_score_and_gate_agree(name, tmp_path):
    report = score_graph(graph(name, tmp_path), load(SHAPES))
    assert (report["score"] is None) == report["gate_failed"]


@pytest.mark.parametrize("name", PUBLISHED)
def test_no_published_spec_carries_a_literal_where_an_iri_belongs(name, tmp_path):
    g = graph(name, tmp_path)
    for prop in (SPECL.affects, SPECL.constrains, SPECL.verifiedBy, SPECL.partOf):
        assert not [o for o in g.objects(None, prop) if isinstance(o, Literal)]


def test_criterion_3_every_section_and_annotation_key_is_exercised():
    """1.0 criterion 3. Coverage of the format, not of the code: a key nothing
    in the corpus uses is a key no golden file would notice breaking."""
    from specl.spec_to_rdf import SECTION_MAP, PROP_MAP, CONTEXTUAL_KEYS
    from pathlib import Path as _P

    corpus = "\n".join(p.read_text(encoding="utf-8") for p in _P(str(ROOT)).glob("**/spec.md"))
    unused_sections = [n for n, *_ in SECTION_MAP if f"# {n}" not in corpus]
    unused_keys = [
        k for k in list(PROP_MAP) + list(CONTEXTUAL_KEYS) if f"- {k}:" not in corpus
    ]
    assert not unused_sections, f"section types never exercised: {unused_sections}"
    assert not unused_keys, f"annotation keys never exercised: {unused_keys}"
