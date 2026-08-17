"""Checks that compare two artifacts which could otherwise disagree.

Every defect this repository has spent a release fixing had one shape: an
artifact asserting something another artifact did not do. The strategy for
keeping that from recurring is in
`docs/decisions/0006-artifact-agreement-strategy.md`, which also carries the
inventory of every known pair and how each is held together.

These are the tier 2 checks: both artifacts are authored independently and a
test compares them mechanically.
"""
from __future__ import annotations

import re
import subprocess
import sys

import pytest

from conftest import PUBLISHED, ROOT, SRC, spec_path, translate

rdflib = pytest.importorskip("rdflib")
from rdflib import Graph, Namespace, URIRef  # noqa: E402

SPECL = Namespace("https://w3id.org/specl/ns#")
CORE = SRC / "specl" / "core.ttl"
SHAPES = SRC / "specl" / "shapes.ttl"
NODE_ID_RE = re.compile(r"^[\w./-]+\.py::[\w.-]+$")


@pytest.fixture(scope="module")
def collected_tests() -> set[str]:
    """Every test the suite actually contains, parameters stripped."""
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "--collect-only", "-q"],
        cwd=ROOT, capture_output=True, text=True,
    )
    return {
        line.split("[")[0]
        for line in result.stdout.splitlines()
        if "::" in line
    }


@pytest.fixture(scope="module")
def emitted(tmp_path_factory) -> Graph:
    """Everything this project can produce, not only what the translator does.

    The scorer emits assessment properties the translator never will, and a
    check that looked only at translated graphs called those dead. What matters
    is whether any code path produces a declared property, not which one.
    """
    graph = Graph()
    work = tmp_path_factory.mktemp("emitted")
    for name in PUBLISHED + ["maximal"]:
        target = work / f"{name}.ttl"
        translate(spec_path(name), target)
        graph.parse(target)

    history = work / "history.ttl"
    subprocess.run(
        [sys.executable, "-m", "specl.validate_spec", "score",
         str(work / f"{PUBLISHED[0]}.ttl"), str(SRC / "specl" / "shapes.ttl"),
         "--history", str(history), "--at", "2026-01-01T00:00:00Z"],
        cwd=ROOT, env={"PYTHONPATH": str(SRC), "PATH": "/usr/bin:/bin"},
        capture_output=True, text=True,
    )
    if history.exists():
        graph.parse(history)
    return graph


def test_every_emitted_property_is_declared_in_the_vocabulary(emitted):
    """P1's shape. The emitter and the ontology are two artifacts, and the
    ontology is what a consumer reads to know what a graph can contain."""
    core = Graph().parse(CORE)
    declared = {str(s) for s in core.subjects()}
    used = {str(p) for p in set(emitted.predicates()) if str(p).startswith(str(SPECL))}
    assert not used - declared, f"emitted but undeclared: {sorted(used - declared)}"


def test_every_declared_property_is_reachable_or_explained(emitted):
    """The reverse direction. A property nothing can emit is either dead or a
    promise, and either way it should be visible as one."""
    core = Graph().parse(CORE)
    declared = {
        str(s) for s in core.subjects(
            rdflib.RDF.type, URIRef("http://www.w3.org/2002/07/owl#DatatypeProperty")
        )
    } | {
        str(s) for s in core.subjects(
            rdflib.RDF.type, URIRef("http://www.w3.org/2002/07/owl#ObjectProperty")
        )
    }
    used = {str(p) for p in set(emitted.predicates())}
    # A property carrying rdfs:comment explaining that it is reserved does not
    # have to be reachable yet.
    reserved = {
        str(s) for s, o in core.subject_objects(rdflib.RDFS.comment)
        if "Reserved" in str(o) or "reserved" in str(o)
    }
    unreachable = declared - used - reserved
    assert not unreachable, (
        "declared in core.ttl, produced by nothing, and not marked reserved: "
        f"{sorted(unreachable)}"
    )


@pytest.mark.parametrize("name", PUBLISHED)
def test_every_verification_claim_names_a_test_that_exists(name, tmp_path, collected_tests):
    """A specification's verifiedBy is a claim about this repository.

    Fifteen of nineteen claims in specl's own specification pointed at tests
    that had never existed, so the traceability the tool advertises was mostly
    fiction about the tool itself.
    """
    target = tmp_path / f"{name}.ttl"
    translate(spec_path(name), target)
    graph = Graph().parse(target)
    claimed = {
        str(o) for node in graph.objects(None, SPECL.verifiedBy)
        for o in graph.objects(node, URIRef("http://purl.org/dc/terms/identifier"))
    }
    node_ids = {c for c in claimed if NODE_ID_RE.match(c)}
    missing = sorted(c for c in node_ids if c not in collected_tests)
    assert not missing, f"{name} claims verification by tests that do not exist: {missing}"


# Tier 3: prose that cannot be compared mechanically is bound to a test instead.
# Each guarantee in the contract page names the test that asserts it, and both
# halves of that binding are checked: no guarantee without a test, no named test
# that does not exist.
CONTRACT_PAGE = ROOT / "docs" / "contracts" / "2.md"
GUARANTEE_RE = re.compile(r"^\*\*(.+?)\*\*", re.M)
BINDING_RE = re.compile(r"<!--verified-by:\s*([^>]+?)\s*-->\s*\n\*\*(.+?)\*\*")


def contract_section() -> str:
    body = CONTRACT_PAGE.read_text(encoding="utf-8")
    start = body.index("## What a consumer may rely on")
    return body[start:body.index("## What contract 1 does not promise")]


def test_every_contract_guarantee_names_a_verifying_test():
    section = contract_section()
    bound = {claim for _, claim in BINDING_RE.findall(section)}
    stated = set(GUARANTEE_RE.findall(section))
    assert not stated - bound, (
        "contract guarantees with no verified-by binding: "
        f"{sorted(stated - bound)}"
    )


def test_every_contract_binding_names_a_test_that_exists(collected_tests):
    named = {test for test, _ in BINDING_RE.findall(contract_section())}
    assert named
    missing = sorted(t for t in named if t not in collected_tests)
    assert not missing, f"contract page cites tests that do not exist: {missing}"


def test_the_shapes_graph_is_identified_and_versioned():
    """UR17 commits versioned fetchable locations. The shapes graph had no
    ontology header at all, so there was nothing to attach a version to and the
    commitment was unsatisfiable rather than merely unmet."""
    shapes = Graph().parse(SHAPES)
    owl = rdflib.Namespace("http://www.w3.org/2002/07/owl#")
    subject = URIRef("https://w3id.org/specl/shapes")
    assert (subject, rdflib.RDF.type, owl.Ontology) in shapes
    assert shapes.value(subject, owl.versionIRI) == URIRef(
        "https://w3id.org/specl/shapes/2"
    )


def test_neither_published_graph_declares_the_retired_namespace():
    """Both core.ttl and shapes.ttl carried a `spec:` prefix binding to the
    namespace 0.3.0 retired. Unused in both, and shipped in both."""
    for path in (CORE, SHAPES):
        assert "w3id.org/specl/spec#" not in path.read_text(encoding="utf-8"), path
