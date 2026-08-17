"""Specifications split across files.

The `companion_files` key, deferred twice. It depends on 0.7.0: without per-item
source provenance, splitting a specification loses the answer to where an item
came from, which is the first thing anyone asks of a file they did not write.
"""
from __future__ import annotations

import pytest

from conftest import translate

rdflib = pytest.importorskip("rdflib")
from rdflib import Graph, Literal, Namespace, URIRef  # noqa: E402
from rdflib.compare import isomorphic  # noqa: E402

SPECL = Namespace("https://w3id.org/specl/ns#")
PROV = Namespace("http://www.w3.org/ns/prov#")
DCT = Namespace("http://purl.org/dc/terms/")
BASE = "https://example.org/specs/split#"

ROOT = """---
title: Split
spec_base: https://example.org/specs/split#
spec_id: split-001
companion_files:
  - requirements.md
  - decisions.md
---

# Intent
A specification split across three files.

# Requirements

- R1 The root file carries the front matter and the first requirement.
"""

REQUIREMENTS = """# Requirements

- R2 The second file carries more requirements.
  - priority: MUST

# User Stories

- US1 As a reader, I want the parts to read as one, so that splitting costs nothing.
"""

DECISIONS = """# Decisions

- D1 Split the specification across three files.
  - status: accepted
  - rationale: The single file had grown past readability.
  - affects: R1, R2
"""

SINGLE = """---
title: Split
spec_base: https://example.org/specs/split#
spec_id: split-001
---

# Intent
A specification split across three files.

# Requirements

- R1 The root file carries the front matter and the first requirement.
- R2 The second file carries more requirements.
  - priority: MUST

# User Stories

- US1 As a reader, I want the parts to read as one, so that splitting costs nothing.

# Decisions

- D1 Split the specification across three files.
  - status: accepted
  - rationale: The single file had grown past readability.
  - affects: R1, R2
"""


def split(tmp_path):
    (tmp_path / "spec.md").write_text(ROOT, encoding="utf-8")
    (tmp_path / "requirements.md").write_text(REQUIREMENTS, encoding="utf-8")
    (tmp_path / "decisions.md").write_text(DECISIONS, encoding="utf-8")
    target = tmp_path / "out.ttl"
    result = translate(tmp_path / "spec.md", target)
    assert result.returncode == 0, result.stderr
    return target, Graph().parse(target)


def without_provenance(graph):
    out = Graph()
    for s, p, o in graph:
        if p in (PROV.wasDerivedFrom, SPECL.sourceLine):
            continue
        if "source-" in str(s):
            continue
        out.add((s, p, o))
    return out


def test_a_split_specification_matches_the_equivalent_single_file(tmp_path):
    """The 0.9.0 exit criterion, stated precisely: the graphs are identical
    apart from provenance, which necessarily differs because the items came
    from different files."""
    _, multi = split(tmp_path)
    single_source = tmp_path / "single.md"
    single_source.write_text(SINGLE, encoding="utf-8")
    single_target = tmp_path / "single.ttl"
    translate(single_source, single_target)
    assert isomorphic(without_provenance(multi), without_provenance(Graph().parse(single_target)))


def test_every_item_names_the_file_it_came_from(tmp_path):
    """The other half of the criterion."""
    _, graph = split(tmp_path)
    expected = {
        "R1": "spec.md", "R2": "requirements.md",
        "US1": "requirements.md", "D1": "decisions.md",
    }
    for item, filename in expected.items():
        doc = graph.value(URIRef(BASE + item), PROV.wasDerivedFrom)
        assert graph.value(doc, DCT.identifier) == Literal(filename), item


def test_line_numbers_are_per_file(tmp_path):
    """A companion's items index that companion, not an offset into a
    concatenation nobody wrote."""
    _, graph = split(tmp_path)
    lines = (tmp_path / "requirements.md").read_text(encoding="utf-8").splitlines()
    recorded = int(graph.value(URIRef(BASE + "R2"), SPECL.sourceLine))
    assert lines[recorded - 1].startswith("- R2 ")


def test_references_resolve_across_files(tmp_path):
    """D1 lives in one file and affects requirements in two others."""
    _, graph = split(tmp_path)
    assert set(graph.objects(URIRef(BASE + "D1"), SPECL.affects)) == {
        URIRef(BASE + "R1"), URIRef(BASE + "R2")
    }


def test_a_missing_companion_is_refused(tmp_path):
    """A specification missing part of itself is a different specification, not
    one with a warning."""
    (tmp_path / "spec.md").write_text(ROOT, encoding="utf-8")
    (tmp_path / "requirements.md").write_text(REQUIREMENTS, encoding="utf-8")
    result = translate(tmp_path / "spec.md", tmp_path / "out.ttl")
    assert result.returncode == 2
    assert "decisions.md" in result.stderr
    assert not (tmp_path / "out.ttl").exists()


def test_a_companion_declaring_its_own_identity_warns(tmp_path):
    """One specification has one identity. A second spec_base in a companion
    would be a second answer to a settled question."""
    (tmp_path / "spec.md").write_text(ROOT, encoding="utf-8")
    (tmp_path / "requirements.md").write_text(
        "---\nspec_base: https://example.org/specs/other#\n---\n\n" + REQUIREMENTS
    , encoding="utf-8")
    (tmp_path / "decisions.md").write_text(DECISIONS, encoding="utf-8")
    result = translate(tmp_path / "spec.md", tmp_path / "out.ttl")
    assert "companion declares 'spec_base'" in result.stderr
    graph = Graph().parse(tmp_path / "out.ttl")
    assert not [s for s in graph.subjects() if "specs/other" in str(s)]


def test_two_files_with_the_same_name_do_not_collide(tmp_path):
    """Identity is the path relative to the root, not the basename."""
    (tmp_path / "parts").mkdir()
    (tmp_path / "spec.md").write_text(
        ROOT.replace("  - requirements.md\n  - decisions.md\n",
                     "  - parts/spec.md\n  - decisions.md\n"),
        encoding="utf-8",
    )
    (tmp_path / "parts" / "spec.md").write_text(REQUIREMENTS, encoding="utf-8")
    (tmp_path / "decisions.md").write_text(DECISIONS, encoding="utf-8")
    target = tmp_path / "out.ttl"
    assert translate(tmp_path / "spec.md", target).returncode == 0
    graph = Graph().parse(target)
    names = {str(o) for o in graph.objects(None, DCT.identifier)}
    assert {"spec.md", "parts/spec.md"} <= names
    assert graph.value(
        graph.value(URIRef(BASE + "R2"), PROV.wasDerivedFrom), DCT.identifier
    ) == Literal("parts/spec.md")
