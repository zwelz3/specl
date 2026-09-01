"""The explorer's field map against the vocabulary.

A hand-maintained restatement of what a graph can contain, in a file nothing
imports and no test exercised. It drifted three ways at once: it still rendered
`asA`, `iWant`, and `soThat` after contract 2 renamed them, it had no
`AcceptanceQuery` class from 0.6.0, and it showed none of the lifecycle or
implementation properties added in 0.4.0 and 0.8.0. A reader would have seen
blank fields and concluded the data was missing.

Found in a fresh-install walkthrough rather than by any check, which is why
there is now a check.
"""
from __future__ import annotations

import re

import pytest

from conftest import SRC

rdflib = pytest.importorskip("rdflib")
from rdflib import Graph, Namespace, URIRef  # noqa: E402

SPECL = Namespace("https://w3id.org/specl/ns#")
EXPLORER = SRC / "specl" / "explorer.html"
CORE = SRC / "specl" / "core.ttl"

# Emitted but not worth a row in a reader's detail panel.
NOT_DISPLAYED = {
    "partOf", "sourceLine", "prefix", "itemPrefix", "detail", "declares",
    "referenceBase", "referencePath", "intent", "purpose", "status",
    "maturityScore", "progressScore", "subscore", "itemClass", "cleanCount",
    "totalCount", "assessed", "gates", "dependsOn", "upstreamOf", "refines",
}


def field_map() -> dict[str, list[str]]:
    """The explorer's per-class display order, read out of its FIELDS table.

    The rewritten explorer derives what an item is *expected* to carry from the
    grammar in its slot, so this table now fixes display order alone. It is
    still the only place the file names a property, so it is still what these
    checks compare against the vocabulary.
    """
    text = EXPLORER.read_text(encoding="utf-8")
    start = text.index("var FIELDS = {")
    block = text[start:text.index("\n};", start)]
    return {
        cls: re.findall(r"'(\w+)'", props)
        for cls, props in re.findall(r"(\w+): \[([^\]]*)\]", block)
    }


def field_names() -> set[str]:
    return {prop for props in field_map().values() for prop in props}


def test_every_field_the_explorer_renders_is_actually_emitted(tmp_path):
    """A field nothing emits renders blank forever.

    Compared against real output rather than against `core.ttl`, because specl
    deliberately reuses `skos:`, `dct:`, and `prov:` terms it does not declare.
    Checking the declaration would have called `skos:prefLabel` unbacked while
    the graph carries it.
    """
    from conftest import PUBLISHED, spec_path, translate

    emitted = Graph()
    for name in PUBLISHED + ["maximal"]:
        target = tmp_path / f"{name}.ttl"
        translate(spec_path(name), target)
        emitted.parse(target)
    produced = {str(p).split("#")[-1].split("/")[-1] for p in set(emitted.predicates())}
    unknown = sorted(f for f in field_names() if f not in produced)
    assert not unknown, f"explorer renders properties nothing emits: {unknown}"


def test_every_item_class_has_a_field_map():
    """A class with no entry is invisible in the explorer."""
    core = Graph().parse(CORE)
    rdfs = rdflib.RDFS
    # Asked of the vocabulary rather than subtracted from a hand-kept list of
    # exclusions, which would need editing every time a class is added.
    item_classes = {
        str(c).split("#")[-1]
        for c in core.subjects(rdfs.subClassOf, SPECL.Item)
    }
    mapped = set(field_map())
    missing = sorted(c for c in item_classes if c not in mapped)
    assert not missing, f"classes the explorer cannot display: {missing}"


def test_no_retired_property_names_remain():
    text = EXPLORER.read_text(encoding="utf-8")
    for retired in ("'asA'", "'iWant'", "'soThat'"):
        assert retired not in text, f"{retired} was renamed in contract 2"


def test_the_explorer_is_one_self_contained_file():
    """specl_tool R4.1.

    The requirement is that the explorer carries everything it needs: droppable
    into a page or opened from disk, which a build step or an external asset
    would defeat. It was written as a 30 KB bound while the file was 14 KB, and
    the bound stood in for the property rather than stating it. The rewritten
    file embeds its own example graph and is an order of magnitude larger
    without being any less self-contained, so the bytes are not asserted and
    the dependencies are.
    """
    html = EXPLORER.read_text(encoding="utf-8")
    for external in ("<script src=", "<link rel=\"stylesheet\"", "@import"):
        assert external not in html, f"explorer.html loads {external!r} from outside itself"
