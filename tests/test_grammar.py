"""Conformance to the identifier grammar published to consumers.

`docs/DOWNSTREAM-COMMITMENTS.md` publishes a grammar admitting one or more
uppercase letters, one or more digits, then zero or more dot-separated digit
groups, with `R`, `US`, `OQ`, `D`, `DN`, `C`, and `Q` reserved. The translator
implements a narrower one. These tests state the committed grammar, so P16 is
the release that turns them green rather than a change nobody notices.
"""
from __future__ import annotations

import pytest

from conftest import translate

BASE = "spec_base: https://example.org/specs/t#\n"
HEAD = "---\ntitle: T\n" + BASE + "spec_id: t-001\nversion: 0.1.0\nstatus: draft\n---\n\n"


def write(tmp_path, section, bullet):
    source = tmp_path / "g.md"
    source.write_text(f"{HEAD}# {section}\n\n- {bullet} A description of the item.\n", encoding="utf-8")
    return source


def item_count(tmp_path, section, bullet):
    source = write(tmp_path, section, bullet)
    target = tmp_path / "g.ttl"
    result = translate(source, target)
    assert result.returncode == 0, result.stderr
    return target.read_text(encoding="utf-8").count("specl:partOf")


@pytest.mark.parametrize(
    "section,bullet",
    [("Requirements", "R1"), ("Requirements", "R1.1"), ("User Stories", "US1"),
     ("Open Questions", "OQ1"), ("Decisions", "D1")],
)
def test_currently_supported_identifiers_translate(tmp_path, section, bullet):
    assert item_count(tmp_path, section, bullet) == 1


@pytest.mark.parametrize(
    "section,bullet",
    [("Requirements", "R1.2.3"), ("User Stories", "US1.2"), ("Decisions", "D1.1")],
)
def test_committed_grammar_identifiers_translate(tmp_path, section, bullet):
    assert item_count(tmp_path, section, bullet) == 1


def test_unparsed_item_bullet_warns_rather_than_vanishing(tmp_path):
    source = write(tmp_path, "Requirements", "Rx")
    result = translate(source, tmp_path / "g.ttl", "--fail-on-warning")
    assert result.returncode == 1
    assert "does not match the identifier grammar" in result.stderr


def test_an_unidentified_design_note_warns_under_contract_2(tmp_path):
    """P8. Design notes and comments were the last sections whose IRIs were a
    function of prose, so editing wording broke inbound references. They now
    require identifiers like every other item section."""
    source = tmp_path / "g.md"
    source.write_text(f"{HEAD}# Design Considerations\n\n- A plain prose bullet.\n", encoding="utf-8")
    result = translate(source, tmp_path / "g.ttl", "--fail-on-warning")
    assert result.returncode == 1
    assert "does not match the identifier grammar" in result.stderr


def test_mixed_ordinal_padding_warns_without_merging(tmp_path):
    """`D1` and `D01` are distinct identifiers. The register forbids
    normalizing, because normalization silently merges two items."""
    source = tmp_path / "g.md"
    source.write_text(
        f"{HEAD}# Requirements\n\n- R01 Padded.\n- R2 Unpadded.\n"
    , encoding="utf-8")
    target = tmp_path / "g.ttl"
    result = translate(source, target)
    assert "mixes padded and unpadded ordinals" in result.stderr
    out = target.read_text(encoding="utf-8")
    assert "spec:R01" in out and "spec:R2" in out
