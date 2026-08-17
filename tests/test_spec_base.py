"""The `spec_base` grammar, and what the translator refuses.

Specified in `docs/DOWNSTREAM-COMMITMENTS.md`. Every rejection here is a value
that would otherwise become a permanent identifier, so nothing is appended,
trimmed, or normalized on the author's behalf.
"""
from __future__ import annotations

import pytest

from conftest import PUBLISHED, FIXTURE_SPECS, spec_path, translate

module = pytest.importorskip("specl.spec_to_rdf")
check_base, SpecError = module.check_base, module.SpecError


def test_a_hash_terminated_base_with_a_path_is_accepted():
    assert check_base("https://example.org/specs/a#") == "https://example.org/specs/a#"


@pytest.mark.parametrize(
    "value,because",
    [
        (None, "required"),
        ("https://example.org/specs/a", "does not end in '#'"),
        ("https://example.org/specs/a/", "slash terminated"),
        ("https://example.org/specs/a#frag", "does not end in '#'"),
        ("https://example.org/a#b#", "fragment beyond"),
        ("https://example.org#", "bare authority"),
    ],
)
def test_rejections(value, because):
    with pytest.raises(SpecError) as exc:
        check_base(value)
    assert because in str(exc.value)


def test_a_rejected_base_writes_no_output(tmp_path):
    """A warning describes something dropped. This describes a value that would
    have become a permanent identifier, so no graph is written at all."""
    source = tmp_path / "s.md"
    source.write_text(
        "---\ntitle: T\nspec_base: https://example.org/specs/a\nspec_id: t-001\n---\n\n"
        "# Requirements\n\n- R1 A requirement.\n"
    , encoding="utf-8")
    target = tmp_path / "s.ttl"
    result = translate(source, target)
    assert result.returncode == 2
    assert not target.exists()
    assert "does not end in '#'" in result.stderr


@pytest.mark.parametrize("name", PUBLISHED + FIXTURE_SPECS)
def test_the_specification_is_the_base_without_its_terminator(name, tmp_path):
    """0004. The Specification node is the hash namespace minus the hash, and
    spec_id is not part of any IRI."""
    text = spec_path(name).read_text(encoding="utf-8")
    base = next(l.split(": ", 1)[1].strip() for l in text.splitlines()
                if l.startswith("spec_base:"))
    target = tmp_path / f"{name}.ttl"
    translate(spec_path(name), target)
    out = target.read_text(encoding="utf-8")
    assert f"<{base[:-1]}> a specl:Specification" in out
    assert f"@prefix spec: <{base}>" in out
    assert f"dct:conformsTo <https://w3id.org/specl/contract/2>" in out


@pytest.mark.parametrize("name", PUBLISHED + FIXTURE_SPECS)
def test_no_node_is_minted_under_the_retired_namespace(name, tmp_path):
    """Structural rather than textual: a description may legitimately mention
    the legacy IRI, but no node may be identified by one."""
    rdflib = pytest.importorskip("rdflib")
    from rdflib import Graph, URIRef

    target = tmp_path / f"{name}.ttl"
    translate(spec_path(name), target)
    graph = Graph().parse(target)
    offenders = [
        str(n) for n in graph.all_nodes()
        if isinstance(n, URIRef) and str(n).startswith(module.LEGACY_SPEC_BASE)
    ]
    assert not offenders
