"""Governing terms in a vocabulary this project does not own.

Found in the first real consumer specification, which writes
`constrains: HolonicDataset, cga:Holon` in one list: a Python class and an RDF
class under one key. Those are different claims. A requirement constraining a
component says the code must behave a certain way; one governing a vocabulary
term says what the term means. Widening `constrains` to cover both would have
discarded the range that makes the first claim checkable.
"""
from __future__ import annotations

import subprocess
import sys

import pytest

from conftest import ROOT, SRC, translate

rdflib = pytest.importorskip("rdflib")
from rdflib import Graph, Literal, Namespace, URIRef  # noqa: E402

SPECL = Namespace("https://w3id.org/specl/ns#")
CGA = "https://w3id.org/cagel/ns#"
BASE = "https://example.org/specs/t#"

VOCAB = """@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix cga: <https://w3id.org/cagel/ns#> .
cga:Holon a owl:Class .
cga:LayerRole a owl:Class .
"""


def build(tmp_path, body, front="vocabularies:\n  cga:\n    base: https://w3id.org/cagel/ns#\n"):
    source = tmp_path / "s.md"
    source.write_text(
        f"---\ntitle: T\nspec_base: {BASE}\nspec_id: t-001\n{front}---\n\n{body}"
    , encoding="utf-8")
    target = tmp_path / "s.ttl"
    result = translate(source, target)
    return result, Graph().parse(target), target


def test_a_governed_term_resolves_against_the_declared_vocabulary(tmp_path):
    result, graph, _ = build(
        tmp_path,
        "# Requirements\n\n- R1 Each holon must thread through four layers.\n"
        "  - governs: cga:Holon, cga:LayerRole\n",
    )
    assert result.returncode == 0, result.stderr
    assert set(graph.objects(URIRef(BASE + "R1"), SPECL.governs)) == {
        URIRef(CGA + "Holon"), URIRef(CGA + "LayerRole")
    }


def test_an_absolute_iri_needs_no_declaration(tmp_path):
    _, graph, _ = build(
        tmp_path,
        f"# Requirements\n\n- R1 A requirement.\n  - governs: {CGA}Holon\n",
        front="",
    )
    assert graph.value(URIRef(BASE + "R1"), SPECL.governs) == URIRef(CGA + "Holon")


def test_an_undeclared_prefix_warns_rather_than_guessing(tmp_path):
    result, _, _ = build(
        tmp_path, "# Requirements\n\n- R1 A requirement.\n  - governs: ghost:Thing\n",
        front="",
    )
    assert "names no declared vocabulary" in result.stderr


def test_governs_never_falls_through_to_the_identifier_grammar(tmp_path):
    """`governs: Holon` must not become a reference to a requirement that
    happens to be called Holon."""
    result, graph, _ = build(
        tmp_path,
        "# Requirements\n\n- R1 A requirement.\n  - governs: R2\n- R2 Another.\n",
    )
    assert "names no declared vocabulary" in result.stderr
    assert graph.value(URIRef(BASE + "R1"), SPECL.governs) == Literal("R2")


def test_constrains_pointing_at_a_vocabulary_term_is_redirected(tmp_path):
    """What the consumer actually wrote. The warning names the right key rather
    than saying the prefix is undeclared, which it is not."""
    result, _, _ = build(
        tmp_path, "# Requirements\n\n- R1 A requirement.\n  - constrains: cga:Holon\n"
    )
    assert "Use 'governs:'" in result.stderr
    assert "specl:Component as its range" in result.stderr


def test_a_prefix_declared_as_both_is_reported(tmp_path):
    result, _, _ = build(
        tmp_path,
        "# Requirements\n\n- R1 A requirement.\n",
        front=(
            "vocabularies:\n  cga:\n    base: https://w3id.org/cagel/ns#\n"
            "references:\n  cga:\n    base: https://example.org/specs/cga#\n"
        ),
    )
    assert "declared as both" in result.stderr


def test_a_base_that_would_run_into_a_path_segment_is_refused(tmp_path):
    result, _, _ = build(
        tmp_path,
        "# Requirements\n\n- R1 A requirement.\n",
        front="vocabularies:\n  cga:\n    base: https://w3id.org/cagel/ns\n",
    )
    assert "ends in neither" in result.stderr


def test_a_governed_term_the_vocabulary_does_not_define_is_reported(tmp_path):
    """The payoff. A misspelled class name is a perfectly valid IRI, so nothing
    else would notice it."""
    (tmp_path / "cga.ttl").write_text(VOCAB, encoding="utf-8")
    _, _, target = build(
        tmp_path,
        "# Requirements\n\n- R1 A requirement.\n  - governs: cga:Holn\n",
        front=(
            "vocabularies:\n  cga:\n    base: https://w3id.org/cagel/ns#\n"
            f"    path: {tmp_path / 'cga.ttl'}\n"
        ),
    )
    result = subprocess.run(
        [sys.executable, "-m", "specl.validate_spec", "layering", str(target)],
        cwd=ROOT, env={"PYTHONPATH": str(SRC), "PATH": "/usr/bin:/bin"},
        capture_output=True, text=True,
    )
    assert result.returncode == 3
    assert "which cga does not define" in result.stdout


def test_a_term_the_vocabulary_defines_passes(tmp_path):
    (tmp_path / "cga.ttl").write_text(VOCAB, encoding="utf-8")
    _, _, target = build(
        tmp_path,
        "# Requirements\n\n- R1 A requirement.\n  - governs: cga:Holon\n",
        front=(
            "vocabularies:\n  cga:\n    base: https://w3id.org/cagel/ns#\n"
            f"    path: {tmp_path / 'cga.ttl'}\n"
        ),
    )
    result = subprocess.run(
        [sys.executable, "-m", "specl.validate_spec", "layering", str(target)],
        cwd=ROOT, env={"PYTHONPATH": str(SRC), "PATH": "/usr/bin:/bin"},
        capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stdout
