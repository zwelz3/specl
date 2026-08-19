"""How parser warnings surface, and what gates on them.

R1.5, R1.6, and R1.7 in `specs/specl_tool/spec.md`. `--strict` keeps its
original contract, warnings print unconditionally, and gating is a separate
opt-in flag.
"""
from __future__ import annotations

import pytest

from conftest import PUBLISHED, spec_path, specl_warnings, translate

WARNING_SPEC = (
    "---\ntitle: T\nspec_base: https://example.org/specs/t#\n"
    "spec_id: t-001\nversion: 0.1.0\nstatus: draft\n---\n\n"
    "# Requirements\n\n- R1 A requirement.\n  - notAKnownKey: value\n"
)
CLEAN_SPEC = (
    "---\ntitle: T\nspec_base: https://example.org/specs/t#\n"
    "spec_id: t-001\nversion: 0.1.0\nstatus: draft\n---\n\n"
    "# Requirements\n\n- R1 A requirement.\n  - priority: MUST\n"
)


def write(tmp_path, text):
    source = tmp_path / "s.md"
    source.write_text(text, encoding="utf-8")
    return source


def test_warnings_print_without_any_flag(tmp_path):
    result = translate(write(tmp_path, WARNING_SPEC), tmp_path / "s.ttl")
    assert result.returncode == 0
    assert "notAKnownKey" in result.stderr
    assert "1 parser warning(s) in" in result.stderr


def test_strict_still_exits_zero(tmp_path):
    """R1.5 is unchanged. The flag is redundant now, not broken."""
    result = translate(write(tmp_path, WARNING_SPEC), tmp_path / "s.ttl", "--strict")
    assert result.returncode == 0
    assert "notAKnownKey" in result.stderr


def test_fail_on_warning_gates(tmp_path):
    target = tmp_path / "s.ttl"
    result = translate(write(tmp_path, WARNING_SPEC), target, "--fail-on-warning")
    assert result.returncode == 1
    assert target.exists(), "the output is written even when the run fails"
    assert "--fail-on-warning is set" in result.stderr


def test_fail_on_warning_is_silent_when_clean(tmp_path):
    result = translate(write(tmp_path, CLEAN_SPEC), tmp_path / "s.ttl", "--fail-on-warning")
    assert result.returncode == 0
    assert not specl_warnings(result.stderr)


@pytest.mark.parametrize("name", PUBLISHED)
def test_published_specs_translate_without_warnings(name, tmp_path):
    """CI gates on this. A published specification that warns is a bug in the
    specification, not an accepted background level."""
    result = translate(spec_path(name), tmp_path / "s.ttl", "--fail-on-warning")
    assert result.returncode == 0, result.stderr


HEAD = (
    "---\ntitle: T\nspec_base: https://example.org/specs/t#\n"
    "spec_id: t-001\nversion: 0.1.0\nstatus: draft\n---\n\n"
)
PROSE_BODY = (
    "# Design Considerations\n\n"
    "The Turtle parser does not need to be RFC-compliant for the explorer.\n\n"
    "A second paragraph of reasoning that took real effort to write.\n\n"
    "- DN1 A note that is a bullet and survives.\n"
)


def test_prose_under_an_item_heading_warns(tmp_path):
    """UR26. A downstream migration lost three paragraphs this way with zero
    parser warnings, so `--fail-on-warning` passed over silent content loss.
    Under 0.2.0 they became content-hash design notes, which makes it a
    regression across a version boundary that `specl-validate diff` could not
    see either, since the namespace changed in the same step."""
    source = tmp_path / "s.md"
    source.write_text(HEAD + PROSE_BODY, encoding="utf-8")
    result = translate(source, tmp_path / "s.ttl")
    assert "contains prose that produced no DesignNote" in result.stderr
    assert "The Turtle parser" in result.stderr, "the warning does not name the text"


def test_the_prose_marker_declares_it_deliberate(tmp_path):
    source = tmp_path / "s.md"
    source.write_text(
        HEAD + PROSE_BODY.replace(
            "# Design Considerations\n", "# Design Considerations\n<!--specl: prose-->\n"
        ),
        encoding="utf-8",
    )
    result = translate(source, tmp_path / "s.ttl", "--fail-on-warning")
    assert result.returncode == 0, result.stderr


def test_a_subheading_is_not_mistaken_for_lost_prose(tmp_path):
    """specl's own specifications group long sections with H2 headings. Flagging
    those would have made the warning noise on its first run, which is how a
    warning gets ignored rather than fixed."""
    source = tmp_path / "s.md"
    source.write_text(
        HEAD + "# Requirements\n\n## R1 Translation\n\n"
        "- R1.1 The translator must accept markdown.\n",
        encoding="utf-8",
    )
    result = translate(source, tmp_path / "s.ttl", "--fail-on-warning")
    assert result.returncode == 0, result.stderr


def test_prose_in_a_section_that_models_nothing_is_not_flagged(tmp_path):
    """Intent and Purpose are prose sections by design."""
    source = tmp_path / "s.md"
    source.write_text(
        HEAD + "# Intent\nProse belongs here.\n\n# Purpose\nAnd here.\n",
        encoding="utf-8",
    )
    assert translate(source, tmp_path / "s.ttl", "--fail-on-warning").returncode == 0
