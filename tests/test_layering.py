"""Cross-specification layering.

UR13 in the commitments register: layering never touches the network, a peer is
read from a local path or not at all, and an unreadable peer reports
inconclusive rather than passing. A validator that fetches at check time is
non-deterministic in CI, and that holds independently of the consumer's
air-gapped environment.
"""
from __future__ import annotations

import subprocess
import sys

import pytest

from conftest import SRC, translate

pytest.importorskip("rdflib")

OK, FAIL, INCONCLUSIVE = 0, 1, 3

UPSTREAM = (
    "---\ntitle: Upstream\nspec_base: https://example.org/specs/up#\n"
    "spec_id: up-001\n---\n\n# Requirements\n\n- R1 The upstream requirement.\n"
)


def downstream(peer_path, relation="dependsOn", token="UP:R1"):
    return (
        "---\ntitle: Downstream\nspec_base: https://example.org/specs/down#\n"
        "spec_id: down-001\nreferences:\n  UP:\n"
        "    base: https://example.org/specs/up#\n"
        f"    path: {peer_path}\n{relation}: UP\n---\n\n"
        f"# Requirements\n\n- R1 Builds on it.\n  - affects: {token}\n"
    )


def layering(graph_path):
    return subprocess.run(
        [sys.executable, "-m", "specl.validate_spec", "layering", str(graph_path)],
        env={"PYTHONPATH": str(SRC), "PATH": "/usr/bin:/bin"},
        capture_output=True, text=True,
    )


@pytest.fixture
def peer(tmp_path):
    source = tmp_path / "up.md"
    source.write_text(UPSTREAM, encoding="utf-8")
    target = tmp_path / "up.ttl"
    translate(source, target)
    return target


def build(tmp_path, text):
    source = tmp_path / "down.md"
    source.write_text(text, encoding="utf-8")
    target = tmp_path / "down.ttl"
    assert translate(source, target).returncode == 0
    return target


def test_a_reference_upstream_passes(tmp_path, peer):
    result = layering(build(tmp_path, downstream(peer)))
    assert result.returncode == OK and "Result: pass" in result.stdout


def test_a_reference_into_a_specification_declared_downstream_fails(tmp_path, peer):
    """The exit criterion: layering fails on a deliberately inverted
    reference."""
    result = layering(build(tmp_path, downstream(peer, relation="upstreamOf")))
    assert result.returncode == FAIL
    assert "declared downstream of this specification" in result.stdout


def test_an_unreadable_peer_is_inconclusive_rather_than_a_pass(tmp_path):
    result = layering(build(tmp_path, downstream("./nowhere.ttl")))
    assert result.returncode == INCONCLUSIVE
    assert "never a pass" in result.stdout


def test_a_reference_the_peer_does_not_declare_is_inconclusive(tmp_path, peer):
    result = layering(build(tmp_path, downstream(peer, token="UP:R99")))
    assert result.returncode == INCONCLUSIVE
    assert "does not declare" in result.stdout


def test_a_specification_with_no_references_passes(tmp_path):
    source = tmp_path / "s.md"
    source.write_text(
        "---\ntitle: T\nspec_base: https://example.org/specs/t#\nspec_id: t-001\n---\n\n"
        "# Requirements\n\n- R1 Local only.\n"
    , encoding="utf-8")
    target = tmp_path / "s.ttl"
    translate(source, target)
    result = layering(target)
    assert result.returncode == OK and "0 external reference" in result.stdout
