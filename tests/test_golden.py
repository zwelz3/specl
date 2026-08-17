"""Every specification translates to a recorded output, twice, identically."""
from __future__ import annotations

import pytest

from conftest import GOLDEN, PUBLISHED, FIXTURE_SPECS, normalize, spec_path, translate

ALL = PUBLISHED + FIXTURE_SPECS


@pytest.mark.parametrize("name", ALL)
def test_translation_matches_golden(name, tmp_path):
    out = tmp_path / f"{name}.ttl"
    result = translate(spec_path(name), out)
    assert result.returncode == 0, result.stderr

    golden = GOLDEN / f"{name}.ttl"
    assert golden.exists(), f"no golden for {name}; run tools/refresh_goldens.py"
    assert normalize(out.read_text(encoding="utf-8")) == golden.read_text(encoding="utf-8")


@pytest.mark.parametrize("name", ALL)
def test_translation_is_idempotent(name, tmp_path):
    first, second = tmp_path / "a.ttl", tmp_path / "b.ttl"
    translate(spec_path(name), first)
    translate(spec_path(name), second)
    assert first.read_text(encoding="utf-8") == second.read_text(encoding="utf-8")


def test_strict_prints_warnings_without_failing(tmp_path):
    """R1.5 in `specs/specl_tool/spec.md` specifies this exactly: --strict prints
    parser warnings to stderr and exits 0. An earlier version of this test
    asserted a non-zero exit, which the self-specification refuted.

    Nothing in the pipeline gates on a parser warning as a result. CI translates
    with --strict, prints them, and continues. Whether a separate gating flag
    should exist is recorded in the roadmap rather than decided here.
    """
    source = tmp_path / "warn.md"
    source.write_text(
        "---\ntitle: T\nspec_base: https://example.org/specs/t#\nspec_id: t-001\n---\n\n"
        "# Requirements\n\n"
        "- R1 A requirement.\n"
        "  - notAKnownKey: value\n"
    , encoding="utf-8")
    result = translate(source, tmp_path / "warn.ttl", "--strict")
    assert result.returncode == 0
    assert "annotation key" in result.stderr


@pytest.mark.parametrize("name", ALL)
def test_goldens_compare_without_normalization(name, tmp_path):
    """Nothing is filtered out of the comparison. The seam in conftest is the
    identity, and this test is what keeps it that way."""
    out = tmp_path / f"{name}.ttl"
    translate(spec_path(name), out)
    raw = out.read_text(encoding="utf-8").splitlines()
    golden = (GOLDEN / f"{name}.ttl").read_text(encoding="utf-8").splitlines()
    assert len(raw) == len(golden)
    assert raw == golden, "output is byte-identical to its golden; nothing is normalized"


@pytest.mark.parametrize("name", ALL)
def test_created_is_emitted_only_when_supplied(name, tmp_path):
    """P17. Translation time is not a fact about the specification, and stamping
    it made output differ across days."""
    out = tmp_path / f"{name}.ttl"
    translate(spec_path(name), out)
    supplied = "created:" in spec_path(name).read_text(encoding="utf-8")
    assert ("dct:created" in out.read_text(encoding="utf-8")) == supplied
