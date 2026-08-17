"""Item IRIs from different specifications must not collide.

Exit criterion 1 for 0.3.0. Today every specification shares one namespace, so
the assertion is inverted and marked xfail: the fixtures collide by construction
and P3 is what turns this green.
"""
from __future__ import annotations

import itertools

import pytest

rdflib = pytest.importorskip("rdflib")
from rdflib import Graph, Namespace  # noqa: E402

from conftest import PUBLISHED, spec_path, translate  # noqa: E402

SPECL = Namespace("https://w3id.org/specl/ns#")
PAIRS = list(itertools.combinations(PUBLISHED + ["excel_service", "pptx_templater"], 2))


def items(name, tmp_path) -> set[str]:
    target = tmp_path / f"{name}.ttl"
    assert translate(spec_path(name), target).returncode == 0
    graph = Graph().parse(target)
    return {str(s) for s in graph.subjects(SPECL.partOf, None)}


@pytest.mark.parametrize("a,b", PAIRS, ids=[f"{a}+{b}" for a, b in PAIRS])
def test_no_shared_item_iris(a, b, tmp_path):
    shared = items(a, tmp_path) & items(b, tmp_path)
    assert not shared, f"{len(shared)} shared IRIs, first: {sorted(shared)[:3]}"


def test_identifiers_that_used_to_collide_no_longer_do(tmp_path):
    """The pair NAMESPACE-MIGRATION.md cites shared 11 item IRIs before 0.3.0.
    They still share 11 identifier tokens; those tokens now resolve under
    different bases."""
    a, b = items("excel_service", tmp_path), items("pptx_templater", tmp_path)
    assert not a & b
    tokens = {i.split("#")[-1] for i in a} & {i.split("#")[-1] for i in b}
    assert len(tokens) == 11
