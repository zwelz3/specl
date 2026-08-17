"""The title key and the fallback derivation.

Specified in `docs/DOWNSTREAM-COMMITMENTS.md`. The fallback is materialized into
the graph rather than computed at validation time, because a Violation-severity
shape requires the property and a consumer has to see what the validator saw.
"""
from __future__ import annotations

import pytest

from conftest import PUBLISHED, FIXTURE_SPECS, spec_path, translate

derive = pytest.importorskip("specl.spec_to_rdf").derive_title

BASE = "spec_base: https://example.org/specs/t#\n"
HEAD = "---\ntitle: T\n" + BASE + "spec_id: t-001\nversion: 0.1.0\nstatus: draft\n---\n\n"


@pytest.mark.parametrize(
    "description,expected",
    [
        ("Short.", "Short"),
        ("Type-specific fields must render in a sensible order:",
         "Type-specific fields must render in a sensible order"),
        ("The system MUST expose an endpoint. It returns JSON.",
         "The system MUST expose an endpoint"),
        ("Use SQLite as the store; it is a single file.", "Use SQLite as the store"),
        ("Handles R1.2 inline without splitting there. Second.",
         "Handles R1.2 inline without splitting there"),
    ],
)
def test_derivation_cases(description, expected):
    assert derive(description) == expected


def test_a_dotted_identifier_is_not_a_sentence_boundary():
    """The boundary is a period or semicolon followed by whitespace, chosen so
    that dotted identifiers survive."""
    assert derive("See R1.2 and R3.4.5 for detail.") == "See R1.2 and R3.4.5 for detail"


def test_long_descriptions_break_on_a_word_boundary():
    long = "The translator must reject a spec_base value that does not end in a terminating hash character"
    title = derive(long)
    assert title.endswith("\u2026")
    assert len(title) <= 81
    assert not title[:-1].endswith(" ")
    assert long.startswith(title[:-1])


def test_supplied_title_wins_over_derivation(tmp_path):
    source = tmp_path / "s.md"
    source.write_text(
        f"{HEAD}# Requirements\n\n- R1 A long description that would derive something else.\n"
        "  - title: Chosen by hand\n"
    , encoding="utf-8")
    target = tmp_path / "s.ttl"
    translate(source, target)
    out = target.read_text(encoding="utf-8")
    assert 'dct:title "Chosen by hand"' in out
    assert "specl:title" not in out, "title maps to dct:, not the specl namespace"


@pytest.mark.parametrize("name", PUBLISHED + FIXTURE_SPECS)
def test_every_item_carries_a_title(name, tmp_path):
    """P2. Two shapes require dct:title at Violation severity, so an item
    without one fails the gate."""
    target = tmp_path / f"{name}.ttl"
    translate(spec_path(name), target)
    blocks = [b for b in target.read_text(encoding="utf-8").split("\n\n") if "specl:partOf" in b]
    assert blocks
    assert all("dct:title" in b for b in blocks)
