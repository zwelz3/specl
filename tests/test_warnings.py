"""How parser warnings surface, and what gates on them.

R1.5, R1.6, and R1.7 in `specs/specl_tool/spec.md`. `--strict` keeps its
original contract, warnings print unconditionally, and gating is a separate
opt-in flag.
"""
from __future__ import annotations

import pytest

from conftest import PUBLISHED, spec_path, translate

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
    assert result.stderr == ""


@pytest.mark.parametrize("name", PUBLISHED)
def test_published_specs_translate_without_warnings(name, tmp_path):
    """CI gates on this. A published specification that warns is a bug in the
    specification, not an accepted background level."""
    result = translate(spec_path(name), tmp_path / "s.ttl", "--fail-on-warning")
    assert result.returncode == 0, result.stderr
