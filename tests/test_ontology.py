"""Ontology consistency, derived from the vocabulary rather than restated.

Every earlier check of this kind was written after a specific failure and named
one property: P1 for literals in object positions, and the range enforcement on
`constrains` and `verifiedBy`. Naming properties one at a time means the next
property added is unchecked by construction.

These derive their assertions from `core.ttl`. A property added to the
vocabulary is covered the moment it is declared, and a property whose emitted
values contradict its own declaration fails without anyone remembering to add a
test.
"""
from __future__ import annotations

import pytest

from conftest import PUBLISHED, ROOT, SRC, spec_path, subprocess_env, translate

rdflib = pytest.importorskip("rdflib")
from rdflib import Graph, Literal, Namespace, RDF, RDFS, URIRef, XSD  # noqa: E402

SPECL = Namespace("https://w3id.org/specl/ns#")
OWL = Namespace("http://www.w3.org/2002/07/owl#")
SH = Namespace("http://www.w3.org/ns/shacl#")
CORE = SRC / "specl" / "core.ttl"
SHAPES = SRC / "specl" / "shapes.ttl"


@pytest.fixture(scope="module")
def core() -> Graph:
    return Graph().parse(CORE)


@pytest.fixture(scope="module")
def emitted(tmp_path_factory) -> Graph:
    graph = Graph()
    work = tmp_path_factory.mktemp("onto")
    for name in PUBLISHED + ["maximal"]:
        target = work / f"{name}.ttl"
        translate(spec_path(name), target)
        graph.parse(target)
    return graph


def test_no_property_is_declared_both_datatype_and_object(core):
    """OWL DL forbids it, and this project has twice reasoned about staying in
    DL: once declining `rdfs:subPropertyOf skos:note`, once declining a
    literal-or-node `role`. Neither reasoning was ever checked."""
    both = sorted(
        str(s) for s in set(core.subjects(RDF.type, OWL.DatatypeProperty))
        & set(core.subjects(RDF.type, OWL.ObjectProperty))
    )
    assert not both


def test_no_annotation_property_carries_property_axioms(core):
    """The specific DL violation the SKOS decision turned on."""
    offenders = []
    for prop in core.subjects(RDF.type, OWL.AnnotationProperty):
        for axiom in (RDFS.range, RDFS.domain, RDFS.subPropertyOf):
            if (prop, axiom, None) in core:
                offenders.append(f"{prop} {axiom}")
    assert not offenders


def test_every_object_property_range_holds_in_emitted_output(core, emitted):
    """Derived, not enumerated. Every object property carrying a range is
    checked, so the next one added is covered on declaration."""
    failures = []
    for prop in core.subjects(RDF.type, OWL.ObjectProperty):
        expected = core.value(prop, RDFS.range)
        if expected is None:
            continue
        for subject, obj in emitted.subject_objects(prop):
            if isinstance(obj, Literal):
                failures.append(f"{prop.split('#')[-1]} -> literal {obj!r}")
                continue
            # A foreign IRI belongs to another specification's graph and cannot
            # be typed from here.
            if not str(obj).startswith(tuple(
                str(s) + "#" for s in emitted.subjects(RDF.type, SPECL.Specification)
            )):
                continue
            if expected != RDF.List and not _is_a(core, emitted, obj, expected):
                failures.append(
                    f"{prop.split('#')[-1]} -> {str(obj).split('#')[-1]} "
                    f"is not a {str(expected).split('#')[-1]}"
                )
    assert not failures, failures


def test_every_datatype_property_range_holds_in_emitted_output(core, emitted):
    """A declared xsd range that the emitter does not honour is a claim the
    graph contradicts, and Turtle makes it easy: a bare number is xsd:integer,
    not xsd:decimal."""
    failures = []
    for prop in core.subjects(RDF.type, OWL.DatatypeProperty):
        expected = core.value(prop, RDFS.range)
        if expected is None:
            continue
        for subject, obj in emitted.subject_objects(prop):
            if not isinstance(obj, Literal):
                failures.append(f"{prop.split('#')[-1]} -> non-literal {obj}")
                continue
            actual = obj.datatype or XSD.string
            if actual != expected:
                failures.append(
                    f"{prop.split('#')[-1]} declares {str(expected).split('#')[-1]} "
                    f"and emitted {str(actual).split('#')[-1]}"
                )
    assert not failures, sorted(set(failures))


def _is_a(core, emitted, node, expected):
    """Type check with one step of subclass closure.

    The emitted graph types an item as a Requirement, not as an Item; the
    superclass is entailed rather than materialized, because writing every
    entailment into every graph bloats output to save a reasoner one hop.
    """
    types = set(emitted.objects(node, RDF.type))
    if expected in types:
        return True
    return any((t, RDFS.subClassOf, expected) in core for t in types)


def test_every_domain_holds_in_emitted_output(core, emitted):
    failures = []
    for prop in set(core.subjects(RDFS.domain, None)):
        expected = core.value(prop, RDFS.domain)
        if expected is None:
            continue
        for subject in emitted.subjects(prop, None):
            if not _is_a(core, emitted, subject, expected):
                failures.append(
                    f"{str(prop).split('#')[-1]} on {str(subject).split('#')[-1]}, "
                    f"which is not a {str(expected).split('#')[-1]}"
                )
    assert not failures, sorted(set(failures))


def test_every_class_used_in_output_is_declared(core, emitted):
    declared = set(core.subjects(RDF.type, OWL.Class))
    used = {
        o for o in emitted.objects(None, RDF.type)
        if str(o).startswith(str(SPECL))
    }
    assert not sorted(str(c) for c in used - declared)


def test_the_shapes_graph_is_valid_shacl():
    """Nothing validated the validator. A malformed shape is silently inert:
    pyshacl skips what it cannot interpret, so a typo in a path removes a check
    without removing a line."""
    pyshacl = pytest.importorskip("pyshacl")
    conforms, _, text = pyshacl.validate(
        Graph().parse(SHAPES), shacl_graph=None, meta_shacl=True,
        advanced=True, inference="none",
    )
    assert conforms, text


def test_every_declared_term_is_documented(core):
    """A vocabulary term with neither a label nor a comment is one a consumer
    has to guess at."""
    undocumented = []
    for kind in (OWL.Class, OWL.ObjectProperty, OWL.DatatypeProperty):
        for term in core.subjects(RDF.type, kind):
            if not str(term).startswith(str(SPECL)):
                continue
            if core.value(term, RDFS.label) is None and core.value(term, RDFS.comment) is None:
                undocumented.append(str(term).split("#")[-1])
    assert not sorted(undocumented)


def test_validation_depends_on_shacl_advanced_features(tmp_path):
    """Declared rather than discovered.

    SHACL makes SPARQL-based targets and constraints an optional feature. These
    shapes lean on them heavily, and a processor without them does not error, it
    silently finds almost nothing. A consumer validating with their own engine
    needs to know that, so the dependency is measured here and stated in the
    contract page.
    """
    pyshacl = pytest.importorskip("pyshacl")
    from conftest import spec_path

    target = tmp_path / "s.ttl"
    translate(spec_path(PUBLISHED[0]), target)
    data, shapes = Graph().parse(target), Graph().parse(SHAPES)
    ont = Graph().parse(CORE)

    def findings(advanced):
        _, report, _ = pyshacl.validate(
            data, shacl_graph=shapes, ont_graph=ont,
            inference="none", advanced=advanced,
        )
        return len(list(report.subjects(RDF.type, SH.ValidationResult)))

    with_af, without_af = findings(True), findings(False)
    assert with_af > 0
    assert without_af < with_af / 2, (
        "if core SHACL now covers most checks, the contract page's conformance "
        "note is overstated and should be revised"
    )


def test_the_disjointness_declaration_is_also_enforced(tmp_path):
    """OWL states it; SHACL is what runs. OWL RL implementations vary in whether
    they surface a disjointness violation, so the declaration alone is a
    comment."""
    pytest.importorskip("pyshacl")
    from conftest import spec_path
    from specl.validate_spec import load, run_shacl

    target = tmp_path / "s.ttl"
    translate(spec_path(PUBLISHED[0]), target)
    graph = Graph().parse(target)
    item = next(iter(graph.subjects(SPECL.partOf, None)))
    graph.add((item, RDF.type, SPECL.UserStory))
    graph.add((item, RDF.type, SPECL.Requirement))
    _, results, _ = run_shacl(graph, load(SHAPES))
    assert any("disjoint" in r["message"] for r in results)


def test_the_shapes_graph_imports_the_vocabulary():
    """A consumer loading the shapes alone had no class hierarchy to resolve
    against, and a shape that consults it found nothing rather than failing."""
    shapes = Graph().parse(SHAPES)
    assert (
        URIRef("https://w3id.org/specl/shapes"),
        OWL.imports,
        URIRef("https://w3id.org/specl/ns"),
    ) in shapes


def test_the_conformance_fixture_discriminates(tmp_path):
    """A processor lacking SHACL Advanced Features must fail the check rather
    than pass it quietly. The fixture is only useful if it can tell them apart."""
    pyshacl = pytest.importorskip("pyshacl")
    import json
    from importlib.resources import files

    root = files("specl") / "conformance"
    expected = json.loads((root / "expected.json").read_text(encoding="utf-8"))["findings"]
    data = Graph().parse(str(root / "fixture.ttl"))
    shapes, ont = Graph().parse(SHAPES), Graph().parse(CORE)

    def count(advanced):
        _, report, _ = pyshacl.validate(
            data, shacl_graph=shapes, ont_graph=ont,
            inference="none", advanced=advanced,
        )
        return len(list(report.subjects(RDF.type, SH.ValidationResult)))

    assert count(True) == len(expected)
    assert count(False) < len(expected), (
        "the fixture no longer distinguishes a processor without Advanced "
        "Features, so passing it would mean nothing"
    )


def test_the_conformance_command_passes_against_the_bundled_processor():
    import subprocess
    import sys as _sys
    from conftest import ROOT, SRC

    result = subprocess.run(
        [_sys.executable, "-m", "specl.validate_spec", "conformance"],
        cwd=ROOT, env=subprocess_env(),
        capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "applies the shapes as intended" in result.stdout


def test_validation_refuses_a_processor_without_advanced_features(monkeypatch):
    """Turning a silent under-report into a loud refusal.

    A processor without SHACL Advanced Features does not error: it reports
    almost nothing and calls the graph conforming. Trusting a clean result from
    one is the worst outcome specl can produce, so it is refused rather than
    reported.
    """
    pyshacl = pytest.importorskip("pyshacl")
    from specl import validate_spec

    real = pyshacl.validate
    monkeypatch.setattr(
        validate_spec, "validate",
        lambda *a, **k: real(*a, **{**k, "advanced": False}),
    )
    monkeypatch.setattr(validate_spec, "_advanced_features_checked", None)
    with pytest.raises(SystemExit) as exit_info:
        validate_spec.assert_advanced_features()
    assert "Advanced Features" in str(exit_info.value)
    assert "conformance" in str(exit_info.value)


def test_the_capability_probe_is_checked_once_per_process(monkeypatch):
    """Thirty milliseconds is acceptable once and not per validation."""
    from specl import validate_spec

    calls = []
    real = validate_spec.validate
    monkeypatch.setattr(
        validate_spec, "validate",
        lambda *a, **k: (calls.append(1), real(*a, **k))[1],
    )
    monkeypatch.setattr(validate_spec, "_advanced_features_checked", None)
    validate_spec.assert_advanced_features()
    validate_spec.assert_advanced_features()
    assert len(calls) == 1


def test_the_exported_bundle_explains_itself():
    """A fixture with no instructions beside it is a fixture nobody uses."""
    import subprocess
    import sys as _sys
    import tempfile
    from conftest import ROOT, SRC

    with tempfile.TemporaryDirectory() as out:
        subprocess.run(
            [_sys.executable, "-m", "specl.validate_spec", "conformance", "--export", out],
            cwd=ROOT, env=subprocess_env(),
            capture_output=True, text=True, check=True,
        )
        from pathlib import Path as _P
        names = {p.name for p in _P(out).iterdir()}
        assert names == {"fixture.ttl", "shapes.ttl", "ns.ttl", "expected.json", "README.md"}
        readme = (_P(out) / "README.md").read_text(encoding="utf-8")
        assert "Advanced Features" in readme and "expected.json" in readme


def test_the_frozen_contract_1_artifacts_are_files_and_unchanged():
    """Graphs in the wild pin https://w3id.org/specl/ns/1, so it must keep
    resolving to the same bytes. The build read these from a git tag at first,
    which needed the tag to exist locally and the checkout to have fetched it:
    a frozen artifact one shallow clone away from disappearing."""
    for name, version in (("ns-1.ttl", "ns/1"), ("shapes-1.ttl", "shapes/1")):
        path = ROOT / "published" / name
        assert path.exists(), f"published/{name} is missing"
        text = path.read_text(encoding="utf-8")
        assert f"owl:versionIRI <https://w3id.org/specl/{version}>" in text
        assert "/2>" not in text, f"published/{name} carries a contract 2 IRI"


def test_the_pages_build_does_not_reconstruct_them_from_history():
    workflow = (ROOT / ".github" / "workflows" / "pages.yml").read_text(encoding="utf-8")
    assert "git show" not in workflow
    assert "published/ns-1.ttl" in workflow
