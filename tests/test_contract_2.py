"""The 0.11.0 breaks, and the migration off contract 1.

The last release that may change an IRI or a property range before 1.0 freezes
the contract. Three changes land together because the batching policy exists to
make one migration rather than three.
"""
from __future__ import annotations

import subprocess
import sys

import pytest

from conftest import FIXTURE_SPECS, PUBLISHED, ROOT, SRC, spec_path, subprocess_env, translate

rdflib = pytest.importorskip("rdflib")
from rdflib import Graph, Literal, Namespace, URIRef  # noqa: E402

SPECL = Namespace("https://w3id.org/specl/ns#")
DCT = Namespace("http://purl.org/dc/terms/")
BASE = "https://example.org/specs/t#"
HEAD = f"---\ntitle: T\nspec_base: {BASE}\nspec_id: t-001\n---\n\n"

CONTRACT_1 = """@prefix specl: <https://w3id.org/specl/ns#> .
@prefix spec: <https://example.org/specs/t#> .
@prefix dct:  <http://purl.org/dc/terms/> .

<https://example.org/specs/t> a specl:Specification ;
    dct:conformsTo <https://w3id.org/specl/contract/1> .

spec:US1 a specl:UserStory ;
    specl:partOf <https://example.org/specs/t> ;
    specl:asA "operator" ;
    specl:iWant "a durable store" ;
    specl:soThat "restarts are safe" .
"""


def build(tmp_path, body):
    source = tmp_path / "s.md"
    source.write_text(HEAD + body, encoding="utf-8")
    target = tmp_path / "s.ttl"
    result = translate(source, target)
    return result, Graph().parse(target)


def migrate(*args):
    return subprocess.run(
        [sys.executable, "-m", "specl.migrate", *args],
        cwd=ROOT, env=subprocess_env(),
        capture_output=True, text=True,
    )


def test_p8_design_notes_and_comments_require_identifiers(tmp_path):
    """An IRI that is a function of prose changes when the wording changes,
    breaking inbound references and showing in diff as a removal and an
    addition."""
    result, _ = build(tmp_path, "# Design Considerations\n\n- A note with no identifier.\n")
    assert "does not match the identifier grammar" in result.stderr


def test_p8_identified_notes_carry_stable_iris(tmp_path):
    _, graph = build(
        tmp_path,
        "# Design Considerations\n\n- DN1 Prefer declarative CSS.\n\n"
        "# Comments\n\n- C1 A comment with an identifier.\n",
    )
    assert (URIRef(BASE + "DN1"), rdflib.RDF.type, SPECL.DesignNote) in graph
    assert (URIRef(BASE + "C1"), rdflib.RDF.type, SPECL.Comment) in graph


@pytest.mark.parametrize("name", PUBLISHED + FIXTURE_SPECS)
def test_no_iri_is_a_function_of_prose(name, tmp_path):
    """The 0.11.0 exit criterion."""
    target = tmp_path / f"{name}.ttl"
    translate(spec_path(name), target)
    import re
    offenders = [
        str(n) for n in Graph().parse(target).all_nodes()
        if isinstance(n, URIRef)
        and re.search(r"#(designnote|comment)-[0-9a-f]{8}$", str(n))
    ]
    assert not offenders


def test_p19_user_story_properties_say_what_they_mean(tmp_path):
    """asA, iWant, and soThat named fragments of a sentence template. What they
    denote is a role, a capability, and a benefit."""
    _, graph = build(
        tmp_path,
        "# User Stories\n\n- US1 As an operator, I want a durable store.\n"
        "  - role: operator\n  - capability: a durable store\n"
        "  - benefit: restarts are safe\n",
    )
    story = URIRef(BASE + "US1")
    assert graph.value(story, SPECL.role) == Literal("operator")
    assert graph.value(story, SPECL.capability) == Literal("a durable store")
    assert graph.value(story, SPECL.benefit) == Literal("restarts are safe")
    assert not list(graph.objects(story, SPECL.asA))


def test_p11_explicit_status_keys_do_not_depend_on_the_section(tmp_path):
    """`status:` still resolves by class. The explicit keys say which property
    they mean, so a bullet moved between sections does not silently change what
    it asserts."""
    _, graph = build(
        tmp_path,
        "# Open Questions\n\n- OQ1 Whether to embed the store.\n"
        "  - resolutionStatus: open\n\n"
        "# Decisions\n\n- D1 Use SQLite.\n  - decisionStatus: accepted\n",
    )
    assert graph.value(URIRef(BASE + "OQ1"), SPECL.resolutionStatus) == Literal("open")
    assert graph.value(URIRef(BASE + "D1"), SPECL.decisionStatus) == Literal("accepted")


def test_p11_the_context_sensitive_key_still_works(tmp_path):
    """Removing it would break every existing specification for no gain."""
    _, graph = build(tmp_path, "# Decisions\n\n- D1 Use SQLite.\n  - status: accepted\n")
    assert graph.value(URIRef(BASE + "D1"), SPECL.decisionStatus) == Literal("accepted")


@pytest.mark.parametrize("name", PUBLISHED)
def test_every_graph_declares_contract_2(name, tmp_path):
    target = tmp_path / f"{name}.ttl"
    translate(spec_path(name), target)
    assert (None, DCT.conformsTo, URIRef("https://w3id.org/specl/contract/2")) in Graph().parse(target)


def test_migration_renames_the_user_story_properties(tmp_path):
    source, target = tmp_path / "one.ttl", tmp_path / "two.ttl"
    source.write_text(CONTRACT_1, encoding="utf-8")
    assert migrate("contract", str(source), str(target)).returncode == 0
    graph = Graph().parse(target)
    story = URIRef(BASE + "US1")
    assert graph.value(story, SPECL.capability) == Literal("a durable store")
    assert graph.value(story, SPECL.benefit) == Literal("restarts are safe")
    assert not list(graph.objects(story, SPECL.iWant))
    assert (None, DCT.conformsTo, URIRef("https://w3id.org/specl/contract/2")) in graph


def test_migration_refuses_to_invent_identifiers_it_cannot_know(tmp_path):
    """The old IRI was a function of the prose, so nothing in the graph says
    what it should become. Reported, not guessed."""
    source, target = tmp_path / "one.ttl", tmp_path / "two.ttl"
    source.write_text(
        CONTRACT_1
        + '\nspec:designnote-84653a77 a specl:DesignNote ;\n'
          '    specl:partOf <https://example.org/specs/t> .\n'
    , encoding="utf-8")
    result = migrate("contract", str(source), str(target))
    assert result.returncode == 3
    assert "designnote-84653a77" in result.stderr
    assert "regenerate" in result.stderr


def test_role_is_an_object_property_to_a_declared_persona(tmp_path):
    """A role is an entity many stories share, not an adjective repeated on each
    of them. It is referenced by identifier rather than minted from a name,
    because minting from the surface string makes 'finance clerk' and 'Finance
    Clerk' two personas with nothing reporting it."""
    _, graph = build(
        tmp_path,
        "# Personas\n\n- P1 The person who reconciles invoices at month end.\n"
        "  - prefLabel: Finance clerk\n  - altLabel: accounts clerk\n\n"
        "# User Stories\n\n- US1 As a finance clerk, I want PDFs, so that I can archive them.\n"
        "  - role: P1\n"
        "- US2 As a finance clerk, I want a summary, so that reconciliation is quick.\n"
        "  - role: P1\n",
    )
    skos = Namespace("http://www.w3.org/2004/02/skos/core#")
    persona = URIRef(BASE + "P1")
    assert (persona, rdflib.RDF.type, SPECL.Persona) in graph
    assert graph.value(URIRef(BASE + "US1"), SPECL.role) == persona
    assert graph.value(URIRef(BASE + "US2"), SPECL.role) == persona, "one node, not two"
    assert graph.value(persona, skos.prefLabel) == Literal("Finance clerk")
    assert Literal("accounts clerk") in set(graph.objects(persona, skos.altLabel))


def test_surface_forms_vary_without_the_identity_moving(tmp_path):
    """The reason the value is an identifier. Two spellings on one persona are
    labels; two spellings as values would have been two personas."""
    _, graph = build(
        tmp_path,
        "# Personas\n\n- P1 The clerk.\n  - altLabel: finance clerk\n"
        "  - altLabel: Finance Clerk\n  - altLabel: accounts clerk\n",
    )
    skos = Namespace("http://www.w3.org/2004/02/skos/core#")
    assert len(set(graph.objects(URIRef(BASE + "P1"), skos.altLabel))) == 3
    assert len(list(graph.subjects(rdflib.RDF.type, SPECL.Persona))) == 1


def test_a_role_naming_no_declared_persona_warns(tmp_path):
    result, _ = build(
        tmp_path, "# User Stories\n\n- US1 A story.\n  - role: P9\n"
    )
    assert "no item in this specification declares" in result.stderr


def test_a_role_given_as_a_name_warns(tmp_path):
    """The mistake the design exists to prevent, caught rather than silently
    minting a persona from a spelling."""
    result, _ = build(
        tmp_path, "# User Stories\n\n- US1 A story.\n  - role: finance clerk\n"
    )
    assert "does not match the identifier grammar" in result.stderr


def test_migration_mints_one_persona_per_distinct_literal(tmp_path):
    """Faithful rather than a guess: two stories that said the same string meant
    the same person under contract 1, and two that said different strings were
    already distinct there."""
    source, target = tmp_path / "one.ttl", tmp_path / "two.ttl"
    source.write_text(CONTRACT_1, encoding="utf-8")
    assert migrate("contract", str(source), str(target)).returncode == 0
    graph = Graph().parse(target)
    personas = list(graph.subjects(rdflib.RDF.type, SPECL.Persona))
    assert len(personas) == 1
    assert graph.value(URIRef(BASE + "US1"), SPECL.role) == personas[0]
    assert not list(graph.objects(None, SPECL.asA))


def test_owner_names_a_declared_agent(tmp_path):
    """An owner is an agent, not a spelling. Held as a literal it was joinable
    only by string equality, which is the defect the persona work fixed for
    role, and no check caught it because the property was declared a datatype
    property and emitted exactly that."""
    _, graph = build(
        tmp_path,
        "# Agents\n\n- AG1 The platform team, accountable for storage decisions.\n"
        "  - prefLabel: Platform team\n\n"
        "# Open Questions\n\n- OQ1 Whether to embed the store.\n  - owner: AG1\n"
        "- OQ2 Whether to shard by tenant.\n  - owner: AG1\n",
    )
    agent = URIRef(BASE + "AG1")
    assert (agent, rdflib.RDF.type, SPECL.Agent) in graph
    assert graph.value(URIRef(BASE + "OQ1"), SPECL.owner) == agent
    assert graph.value(URIRef(BASE + "OQ2"), SPECL.owner) == agent, "one node, not two"


def test_an_agent_is_a_prov_agent(tmp_path):
    """Subclassed rather than minted independently, so a consumer already
    modelling agents recognises one."""
    core = Graph().parse(str(__import__("conftest").SRC / "specl" / "core.ttl"))
    prov = Namespace("http://www.w3.org/ns/prov#")
    assert (SPECL.Agent, rdflib.RDFS.subClassOf, prov.Agent) in core
    assert core.value(SPECL.owner, rdflib.RDFS.range) == prov.Agent


def test_an_owner_given_as_a_name_warns(tmp_path):
    result, _ = build(
        tmp_path, "# Open Questions\n\n- OQ1 A question.\n  - owner: platform team\n"
    )
    assert "does not match the identifier grammar" in result.stderr


def test_migration_mints_agents_from_owner_literals(tmp_path):
    source, target = tmp_path / "one.ttl", tmp_path / "two.ttl"
    source.write_text(
        CONTRACT_1
        + '\nspec:OQ1 a specl:OpenIssue ;\n'
          '    specl:partOf <https://example.org/specs/t> ;\n'
          '    specl:owner "platform team" .\n'
    , encoding="utf-8")
    assert migrate("contract", str(source), str(target)).returncode == 0
    graph = Graph().parse(target)
    agents = list(graph.subjects(rdflib.RDF.type, SPECL.Agent))
    assert len(agents) == 1
    assert graph.value(URIRef(BASE + "OQ1"), SPECL.owner) == agents[0]


def test_source_migration_renames_annotation_keys(tmp_path):
    """Regenerating from markdown was always the better path than migrating a
    graph, and nothing existed to migrate the markdown with. Found by running a
    real 0.2.0-era specification through current specl."""
    source = tmp_path / "old.md"
    source.write_text(
        "---\ntitle: T\nspec_base: https://example.org/specs/t#\nspec_id: t-001\n---\n\n"
        "# User Stories\n\n- US1 A story about a clerk.\n"
        "  - asA: finance clerk\n  - iWant: a report\n  - soThat: it is archived\n"
    , encoding="utf-8")
    target = tmp_path / "new.md"
    result = migrate("source", str(source), str(target))
    text = target.read_text(encoding="utf-8")
    assert "- role: finance clerk" in text
    assert "- capability: a report" in text
    assert "- benefit: it is archived" in text
    assert "asA" not in text


def test_source_migration_reports_what_it_will_not_guess(tmp_path):
    """Renaming asA to role turns a value that worked into one that warns, so
    the report names them rather than leaving the author to discover it."""
    source = tmp_path / "old.md"
    source.write_text(
        "---\ntitle: T\nspec_base: https://example.org/specs/t#\nspec_id: t-001\n---\n\n"
        "# User Stories\n\n- US1 A story.\n  - asA: finance clerk\n\n"
        "# Open Questions\n\n- OQ1 A question.\n  - owner: zwelz3\n\n"
        "# Design Considerations\n\n- A note with no identifier.\n"
    , encoding="utf-8")
    result = migrate("source", str(source), str(tmp_path / "new.md"))
    assert result.returncode == 3
    assert "role value(s) name" in result.stderr and "finance clerk" in result.stderr
    assert "owner value(s) name" in result.stderr and "zwelz3" in result.stderr
    assert "DN identifiers" in result.stderr


def test_source_migration_dry_run_writes_nothing(tmp_path):
    source = tmp_path / "old.md"
    source.write_text(
        "---\ntitle: T\nspec_base: https://example.org/specs/t#\nspec_id: t-001\n---\n\n"
        "# User Stories\n\n- US1 A story.\n  - asA: clerk\n"
    , encoding="utf-8")
    target = tmp_path / "new.md"
    result = migrate("source", str(source), "--dry-run")
    assert not target.exists()
