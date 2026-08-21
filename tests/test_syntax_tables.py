"""The two reference tables in `docs/SYNTAX.md` against the maps they restate.

`docs/decisions/0006-artifact-agreement-strategy.md` left this pair unassigned
and named the shape of the check: parse the markdown table, compare to the map.
Both tables had drifted by 1.0. The section table was missing three item classes
the translator accepts, gave `DN` and `C` as auto-hash, and omitted two
`Open Questions` aliases. The annotation table was missing `gates`, `governs`,
`implementation`, `decisionStatus`, and `resolutionStatus`, each documented in
prose elsewhere in the same file and absent from the reference a reader consults.

The assertion is derived from the maps rather than from a restated list, so a
key added to `PROP_MAP` or a section added to `SECTION_MAP` is covered the
moment it exists. Extraction failure is a test failure rather than an empty
comparison that passes: an anchored table that stops matching means the document
was restructured, and a check that quietly finds nothing is the drift it was
written to prevent.
"""
from __future__ import annotations

import re

import pytest

from conftest import ROOT
from specl.spec_to_rdf import (
    CONTEXTUAL_KEYS,
    PROP_MAP,
    PROSE_SECTIONS,
    SECTION_MAP,
)

# The set `SUB_RE` is built from, which is what the parser actually accepts.
RECOGNISED_KEYS = set(PROP_MAP) | set(CONTEXTUAL_KEYS)

SYNTAX = ROOT / "docs" / "SYNTAX.md"

ROW = re.compile(r"^\|(.+)\|\s*$")
SEPARATOR = re.compile(r"^\|[\s:|-]+\|\s*$")


def read_table(heading_pattern: str, first_column: str) -> list[list[str]]:
    """Rows of the first markdown table under a heading matching the pattern.

    Both arguments are asserted rather than trusted. A table that moved, was
    renamed, or lost its shape fails here instead of yielding nothing.
    """
    text = SYNTAX.read_text(encoding="utf-8")
    anchor = re.search(heading_pattern, text, re.M)
    assert anchor, f"no heading matching {heading_pattern!r} in {SYNTAX.name}"

    rows: list[list[str]] = []
    started = False
    for line in text[anchor.end():].splitlines():
        if SEPARATOR.match(line):
            continue
        match = ROW.match(line)
        if not match:
            if started:
                break
            continue
        cells = [c.strip() for c in match.group(1).split("|")]
        if not started:
            assert cells[0] == first_column, (
                f"first table under {heading_pattern!r} starts with "
                f"{cells[0]!r}, expected {first_column!r}"
            )
            started = True
            continue
        rows.append(cells)

    assert rows, f"no rows found in the table under {heading_pattern!r}"
    return rows


def unticked(cell: str) -> str:
    return cell.replace("`", "").strip()


# --- the section table ------------------------------------------------------


def documented_sections() -> dict[str, str]:
    """Section name to documented ID prefix, aliases split out."""
    documented: dict[str, str] = {}
    for section, _cls, prefix in (
        (name, cls, prefix) for name, cls, prefix in section_rows()
    ):
        for alias in section.split("/"):
            alias = unticked(alias).lstrip("#").strip()
            if alias:
                documented[alias] = prefix
    return documented


def section_rows() -> list[tuple[str, str, str]]:
    return [
        (cells[0], unticked(cells[1]), unticked(cells[2]))
        for cells in read_table(r"^## Sections$", "Section")
    ]


def test_every_section_the_translator_maps_is_documented():
    implemented = {name for name, _cls, _prefix in SECTION_MAP} | set(PROSE_SECTIONS)
    missing = sorted(implemented - set(documented_sections()))
    assert not missing, (
        "the section table in docs/SYNTAX.md does not document sections the "
        f"translator accepts: {missing}"
    )


def test_every_documented_section_is_one_the_translator_maps():
    implemented = {name for name, _cls, _prefix in SECTION_MAP} | set(PROSE_SECTIONS)
    invented = sorted(set(documented_sections()) - implemented)
    assert not invented, (
        "the section table in docs/SYNTAX.md documents sections the translator "
        f"does not map: {invented}"
    )


def test_documented_id_prefixes_match_the_translator():
    prefixes = {
        name: prefix for name, _cls, prefix in SECTION_MAP if prefix
    }
    documented = documented_sections()
    wrong = []
    for name, expected in prefixes.items():
        if name not in documented:
            continue  # the coverage tests above own that failure
        stated = documented[name]
        if stated in {"—", "-", ""}:
            wrong.append((name, stated, expected[0]))
        elif stated not in expected:
            wrong.append((name, stated, expected[0]))
    assert not wrong, (
        "the section table states an ID prefix the translator does not use "
        f"(section, documented, actual): {wrong}"
    )


# --- the annotation key table -----------------------------------------------


def documented_keys() -> set[str]:
    rows = read_table(r"^## Annotation key reference$", "Key")
    return {unticked(cells[0]) for cells in rows if unticked(cells[0])}


def test_every_annotation_key_the_translator_reads_is_documented():
    missing = sorted(RECOGNISED_KEYS - documented_keys())
    assert not missing, (
        "the annotation key reference in docs/SYNTAX.md does not document keys "
        f"the translator reads: {missing}"
    )


def test_every_documented_annotation_key_is_one_the_translator_reads():
    invented = sorted(documented_keys() - RECOGNISED_KEYS)
    assert not invented, (
        "the annotation key reference documents keys the translator does not "
        f"read: {invented}"
    )


# --- the extraction itself --------------------------------------------------


def test_a_moved_table_fails_rather_than_comparing_nothing():
    with pytest.raises(AssertionError, match="no heading matching"):
        read_table(r"^## A heading that is not there$", "Key")
