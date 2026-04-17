---
spec_id: ekga-001
title: Enterprise Knowledge Graph Application (EKGA)
version: 0.1.0-draft
status: draft
authors: [zachary]
---

# Intent

Provide a single, versioned, human- and machine-readable source of truth for an enterprise application that captures, manages, and reasons over heterogeneous organizational data through a graph-native knowledge layer. The spec itself must be translatable to RDF so it can be linked to the running system it describes and consumed by downstream AI agents as authoritative context.

# Purpose

Stand up an enterprise application that unifies a vector store, an RDBMS, and an RDF triplestore behind a governed ontology, with schema-driven editing, LLM-assisted structured extraction, provenance on every graph mutation, and a chat interface backed by persistent agentic memory.

# Requirements

## R1 Storage Layer

- R1.1 RDF triplestore: Apache Jena Fuseki, TDB2 backend, named-graph aware.
  - priority: MUST
  - constrains: TriplestoreService, FusekiContainer
  - acceptance: Given a running Fuseki instance, when a SPARQL UPDATE writes to a named graph, then the graph is visible to subsequent SELECTs and survives container restart.
  - verifiedBy: tests/integration/test_fuseki.py::test_named_graph_persistence
- R1.2 RDBMS: PostgreSQL (default), virtualized into the KG via Ontop (OBDA, OWL 2 QL profile). PK/FK relationships surfaced as object properties in the virtual graph.
  - priority: MUST
  - constrains: RDBMSService, OntopMapping
  - acceptance: Given a registered PostgreSQL source with an Ontop mapping, when a SPARQL query joins on a PK/FK relationship, then results match an equivalent SQL JOIN.
  - verifiedBy: tests/integration/test_ontop.py::test_pk_fk_traversal
- R1.3 Vector store: pgvector (preferred, co-located with RDBMS) or Qdrant (fallback). Embeddings linked back to RDF resources via stable IRIs.
  - priority: MUST
  - constrains: VectorStore, EmbeddingRegistry
  - acceptance: Given an embedding stored for an RDF resource, when a k-NN query runs, then returned embeddings resolve to valid IRIs in the knowledge graph.
  - verifiedBy: tests/integration/test_embeddings.py::test_embedding_iri_roundtrip
- R1.4 All three stores addressable through a single internal service layer; no direct client-to-store calls outside the service boundary.

## R2 Ontology Layer

- R2.1 Core ontology: a minimal OWL 2 ontology describing the application itself (modules, users, sessions, ingest jobs, provenance) and the business domain (initially stub classes; extended per deployment).
- R2.2 Inferencing: OWL 2 RL rules via Jena reasoner OR Ontop's own rewriting; SHACL (shacl-compact where practical) for structural and closed-world validation.
- R2.3 Provenance: PROV-O, emitted on every graph write, attributing the change to a user, agent, or module with a timestamp and source activity IRI.
- R2.4 Entity resolution: every RDF view must expose a resolution hook (default: SHACL-driven key shapes plus configurable string/embedding similarity). Resolved equivalences recorded as `owl:sameAs` in a dedicated `urn:graph:sameas` named graph and optionally materialized into target named graphs.

## R3 AuthN / AuthZ

- R3.1 Authentication: SAML 2.0 and OAuth 2.0 / OIDC only. Local password auth is prohibited.
- R3.2 Must support Azure AD on GCC High tenants end to end (metadata exchange, certificate rotation, group claim mapping).
- R3.3 Authorization: RBAC with a seeded `admin` role. Roles stored in the KG under `urn:graph:iam` and enforced at the service layer.
- R3.4 Multi-user: asynchronous parallel transactions required; no real-time collaborative editing in v1.

## R4 User Interface

- R4.1 Clean, minimal web UI. Recommended stack: React plus a shadcn/ui-style component library, or HTMX plus server-rendered templates for a lower-dependency path.
- R4.2 RDBMS lookup view: table browser with filter, sort, paginated read, and in-cell edit for permitted tables.
- R4.3 RDF query view: SPARQL editor (YASGUI or equivalent) with named-graph selector and saved-query support.
- R4.4 Schema-driven forms: generated from SHACL node shapes, with JSON Schema as an interchange format where a SHACL-to-JSON-Schema transform is available.
- R4.5 Chat view: conversational panel with streamed responses, citations back to source IRIs, and a memory inspector.

## R5 Ingest

- R5.1 Register new RDBMS sources through the UI, capturing connection metadata, Ontop mapping file, and responsible owner. Registration writes a record into the KG under `urn:graph:registry`.
- R5.2 Holonic ingest: consume external holons with awareness of named graphs, membranes, and holon boundaries; preserve source graph identity on import.
- R5.3 Generic RDF ingest: accept any RDF serialization. Sources with insufficient write metadata are flagged read-only.
- R5.4 Every ingest produces a PROV-O activity record.

## R6 LLM-Assisted Extraction

- R6.1 Pluggable LLM connector layer. Must support at least one local or open-source model backend (vLLM, Ollama, or llama.cpp) in addition to vendor APIs.
- R6.2 Structured extraction via Pydantic schemas (Instructor or Pydantic-AI patterns), with schemas derived from or validated against the target SHACL shapes.
- R6.3 Extraction context: the LLM is given a distilled view of the relevant ontology fragment and recent graph neighborhood so outputs align with existing IRIs and vocabulary.
- R6.4 Extracted triples land in a quarantine named graph, validated against SHACL, and only promoted on review or auto-promotion policy.
- R6.5 Every extraction writes provenance (model, prompt hash, source document IRI, reviewer).

## R7 Chat Mode and Agentic Memory

- R7.1 Chat answers draw from SPARQL over the KG, vector retrieval, and, where appropriate, direct RDBMS queries through the virtual graph.
- R7.2 User turns and assistant responses are persisted to a Fuseki dataset `urn:graph:memory` with user, session, and turn IRIs. Initial memory strategy: load recent turns for the active session plus top-k semantic recall from prior sessions.
- R7.3 Memory writes are PROV-O annotated.

## R8 Non-Functional

- R8.1 FOSS preference: prioritize well-vetted open-source components.
- R8.2 Deployment: containerized (OCI images), Helm chart for Kubernetes, docker-compose for single-node dev.
- R8.3 Observability: structured logs, OpenTelemetry traces, Prometheus metrics.
- R8.4 Backup and restore for all three stores.

# User Stories

- US1. As an admin, I register a new PostgreSQL source, upload an Ontop mapping, and see its tables appear as a virtual named graph.
- US2. As a data steward, I open a SHACL-driven form for a domain class, fill fields, submit, and the resulting triples appear in the target named graph with provenance.
- US3. As an analyst, I run a SPARQL query across the virtual RDBMS graph and a holon-ingested graph, join on resolved `owl:sameAs` links, and export the result set.
- US4. As a knowledge engineer, I configure an extraction pipeline over a directory of PDFs, review the quarantine graph, and promote validated triples.
- US5. As any authorized user, I ask a question in chat, receive a grounded answer with IRI citations, and the interaction is preserved to memory.
- US6. As an admin, I add a user, assign a role, and the change is reflected in the IAM named graph and enforced on next request.

# Design Considerations

- Treat the spec itself as RDF: each section above maps to an `ekga:Requirement`, `ekga:UserStory`, or `ekga:DesignNote` individual, linked to the application components it constrains.
- Prefer SPARQL and SHACL as the primary control surfaces; Python only where graph operations are insufficient.
- Keep the bootstrap ontology small and extend per deployment rather than shipping a heavy domain model.
- Entity resolution must be observable and reversible; `owl:sameAs` decisions carry provenance and can be retracted.
- Chat memory is a dataset, not a bolt-on cache. Future agents should be able to query it as first-class RDF.

# Comments

- The spec leans on Ontop for RDBMS virtualization because it gives a SPARQL entry point without ETL and preserves PK/FK semantics as properties.
- Holonic ingest assumes the `holonic` library's four-graph holon model as the canonical shape for imported holons.

# Open Questions and Gaps (flag for follow-up)

1. Versioning strategy for the KG itself (named-graph snapshots vs quad-level diffs) is undecided. Recommendation: start with named-graph snapshots plus PROV-O activity log.
2. Vector store governance: are embeddings a first-class RDF resource or opaque? Recommendation: first-class, with `ekga:Embedding` class and IRI back-link.
3. Backup and restore semantics across the three stores must be transactional or explicitly eventually consistent. Recommendation: document as eventually consistent with reconciliation job.
4. Rate limiting and quotas for LLM connectors are unspecified.
5. Chat memory retention, redaction, and user export rights are unspecified.

- 

# Appendix A: Suggested Namespaces

```turtle
@prefix ekga: <https://example.org/ekga/ns#> .
@prefix prov: <http://www.w3.org/ns/prov#> .
@prefix sh:   <http://www.w3.org/ns/shacl#> .
@prefix owl:  <http://www.w3.org/2002/07/owl#> .
```