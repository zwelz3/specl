---
title: Downstream commitments
spec_base: https://w3id.org/specl/commitments/spec#
prefix: COMMIT
item_prefix: UR
spec_id: commitments-001
version: 0.5.0
status: review
---

<!--specl
created: 2026-08-16
-->

# Intent
Behavior specl has already specified to a downstream consumer that authored
against those answers. These are not proposals. A consumer has made irreversible
authoring decisions on each one, and changing an answer here costs that consumer
a migration rather than a rewrite of a plan. Before changing any behavior listed
here, check whether it is listed here.

# Purpose
This register is itself a specl specification, so that each commitment carries an
identifier a second party can cite, a status that can be retired rather than
deleted, and a verification claim checked against the test suite on every run.
Three releases in a row under-delivered against clauses written here because the
roadmap summarized what this document committed, and the summary was believed.
Identifiers are the consumer's own request numbers, UR1 through UR17, so that a
conversation about UR11 resolves to one IRI on both sides.

# Requirements

- UR1 Hash termination is required in `spec_base`. Translation rejects a value that does not end in `#` and does not append a missing terminator, rejects a bare authority with no path segment, and rejects a value carrying a fragment beyond the terminating `#`. Slash-terminated bases remain unsupported until a post-1.0 extension.
  - title: spec_base grammar
  - priority: MUST
  - acceptance: Given a value failing any clause, translation exits non-zero and writes no graph.
  - verifiedBy: tests/test_spec_base.py::test_rejections
  - constrains: spec_to_rdf
- UR2 The legacy base table in `NAMESPACE-MIGRATION.md` is recognized by `specl-migrate iris` as the set of migration sources, and the tool fails rather than guessing when no known source is present.
  - title: Legacy base table
  - priority: MUST
  - acceptance: Given a graph with no legacy IRIs, migration reports nothing to migrate rather than rewriting.
  - verifiedBy: tests/test_migrate.py::test_a_migrated_graph_is_left_alone
  - constrains: migrate
- UR3 Reference resolution is string concatenation onto the base, not RFC 3986 relative resolution. The token is used verbatim, so dotted identifiers are safe under any base shape.
  - title: Reference resolution algorithm
  - priority: MUST
  - acceptance: Given a decision annotated with an item identifier, the emitted object is the base concatenated with that token.
  - verifiedBy: tests/test_references.py::test_an_item_reference_resolves_against_the_base
  - constrains: spec_to_rdf
- UR4 A `title:` fallback is derived from the description and materialized into the graph: split at the first sentence boundary, strip trailing sentence punctuation, and truncate at the last word boundary within 80 characters with an ellipsis appended.
  - title: title fallback derivation
  - priority: MUST
  - acceptance: Given an item with no title, the emitted graph carries a derived one.
  - verifiedBy: tests/test_title.py::test_every_item_carries_a_title
  - constrains: spec_to_rdf
- UR5 `specl-validate diff --ignore-base` compares graphs modulo their instance base, so a migration reports as unchanged content rather than as wholesale removal and addition.
  - title: Graph comparison modulo base
  - priority: MUST
  - acceptance: Given a graph and its migration, keying by token yields no added or removed requirements.
  - verifiedBy: tests/test_migrate.py::test_diff_ignore_base_sees_a_rebased_graph_as_the_same_items
  - constrains: validate_spec
- UR6 Every emitted graph declares the version of the graph contract it conforms to, identifying the vocabulary and shapes pair rather than the tool version.
  - title: Versioned graph contract
  - priority: MUST
  - acceptance: Given any translated specification, the Specification node carries dct:conformsTo naming a contract IRI.
  - verifiedBy: tests/test_spec_base.py::test_the_specification_is_the_base_without_its_terminator
  - constrains: spec_to_rdf
- UR9 A section heading the translator does not recognize produces a warning rather than being dropped in silence, and content under it is not lost without notice.
  - title: Warn on unrecognized sections
  - priority: MUST
  - acceptance: Given a heading nothing recognizes, translation warns and names it; given one marked parked, translation is silent.
  - verifiedBy: tests/test_sections_and_queries.py::test_an_unrecognized_heading_warns_rather_than_vanishing
  - constrains: spec_to_rdf
- UR11 Identifiers are one or more uppercase ASCII letters, one or more digits, then zero or more dot-separated digit groups, case sensitive and never normalized. `R`, `US`, `OQ`, `D`, `DN`, `C`, and `Q` are reserved; project-declared prefixes are at least two characters.
  - title: Reserved prefixes and identifier grammar
  - priority: MUST
  - acceptance: Given an identifier legal under the grammar, translation emits it; given a bullet that looks like an item and does not parse, translation warns rather than dropping it.
  - verifiedBy: tests/test_grammar.py::test_committed_grammar_identifiers_translate
  - constrains: spec_to_rdf
- UR12 A superseded or withdrawn item is still emitted and is not evaluated by the shapes, except the one requiring a successor. A successor is the same class in the same specification. `withdrawn` is the no-successor case, and a withdrawn identifier is permanently reserved, with reuse a violation rather than a warning.
  - title: Supersession semantics
  - priority: MUST
  - acceptance: Given a retired item, no shape other than the successor requirement reports against it.
  - verifiedBy: tests/test_lifecycle.py::test_a_retired_item_accumulates_no_other_warnings
  - constrains: shapes
- UR13 Layering never touches the network. An upstream declaration names a prefix, a base IRI, and a local path. A missing or unreadable peer produces a warning and reports inconclusive, never passing and never failing.
  - title: Layering resolution and offline operation
  - priority: MUST
  - acceptance: Given a peer that cannot be read, layering reports inconclusive and exits 3, never passing.
  - verifiedBy: tests/test_layering.py::test_an_unreadable_peer_is_inconclusive_rather_than_a_pass
  - constrains: validate_spec
- UR15 Cross-specification references are `PREFIX:ID` in reference-valued fields, with foreign prefixes declared in the referencing specification's front matter as a two-level `references:` mapping carrying a base and a path. References resolve to IRIs always. An unresolvable peer is a warning and the reference is still emitted as an IRI.
  - title: Cross-specification reference syntax
  - priority: MUST
  - acceptance: Given a declared prefix, a PREFIX:ID token resolves to the peer base concatenated with the identifier; given an undeclared one, translation warns and emits a literal.
  - verifiedBy: tests/test_references.py::test_a_declared_prefix_resolves_to_the_peer_base
  - constrains: spec_to_rdf
- UR16 Each release's notes name the downstream compensations that release makes unnecessary, and state the observable condition for removing each.
  - title: Per-release obsolescence notes
  - priority: MUST
  - itemStatus: active
- UR17 The shapes graph and vocabulary are published at versioned locations and remain fetchable, with the constraint that nothing fetches at validation time.
  - title: Versioned fetchable shapes and vocabulary
  - priority: MUST
  - acceptance: Given the shapes graph, it declares an ontology IRI carrying a version IRI, and that version is the graph contract rather than the release.
  - verifiedBy: tests/test_drift.py::test_the_shapes_graph_is_identified_and_versioned
  - constrains: shapes
- UR18 Prefixed tokens are illegal in reference-valued fields until cross-specification references exist. Such a token produces a parser warning and is emitted as a literal rather than a guessed IRI.
  - title: Prefixed tokens before layering
  - priority: MUST
  - acceptance: Given a CURIE in a reference field before 0.5.0, translation warns and emits a literal.
  - verifiedBy: tests/test_references.py::test_an_undeclared_prefix_warns_and_stays_a_literal
  - constrains: spec_to_rdf
- UR19 A reference token that does not match the identifier grammar produces a parser warning and is emitted as a literal, never silently discarded.
  - title: Unresolvable reference tokens survive
  - priority: MUST
  - acceptance: Given a reference to an identifier no item declares, translation warns and still emits the IRI.
  - verifiedBy: tests/test_references.py::test_a_dangling_reference_warns_and_still_resolves
  - constrains: spec_to_rdf
- UR20 The acceptance query class arrives under the section heading `# Acceptance Queries` with prefix `Q`, one bullet per query with the intent as description, and a `gates:` annotation taking a comma-separated list of requirement identifiers.
  - title: Acceptance query class
  - priority: MUST
  - acceptance: Given a Q-prefixed bullet under the committed heading with a gates annotation, the query is emitted and the requirements it gates are reachable from it.
  - verifiedBy: tests/test_sections_and_queries.py::test_a_requirement_is_reachable_from_the_query_that_gates_it
  - constrains: spec_to_rdf
- UR21 Per-term stability tiers are deferred rather than refused, because assigning stability to a vocabulary that gains classes in four of the next five releases would record an assurance that cannot be honored.
  - title: Per-term stability tiers
  - priority: SHOULD
  - itemStatus: active

- UR23 An absolute IRI in a reference-valued field is used as written rather than minted into a local node. Several specifications naming the same IRI name the same node, which is how a specification family shares a component without a name-to-IRI map.
  - title: Absolute IRIs in reference-valued fields
  - priority: MUST
  - acceptance: Given three specifications whose requirements each name the same absolute IRI under constrains, merging their graphs yields one node reached by three requirements.
  - verifiedBy: tests/test_references.py::test_three_specifications_naming_one_iri_share_a_node
  - constrains: spec_to_rdf
- UR24 A `constrains` or `verifiedBy` value resolving against a specification reference that declares no path warns and names the absolute IRI as the alternative. A reference prefix declares a peer specification, and using one for a component namespace pins layering to inconclusive.
  - title: Warn on a reference prefix used for a component
  - priority: MUST
  - acceptance: Given constrains resolving a CURIE against a pathless specification reference, translation warns and the message names the absolute IRI alternative.
  - verifiedBy: tests/test_references.py::test_a_reference_prefix_used_for_a_component_warns
  - constrains: spec_to_rdf

# Decisions

- UR8 Per-item shape suppression is declined as requested, and the root cause is accepted instead. A suppression key with a reason field is a warning made invisible, and specl already has decision records for recording a judgment.
  - title: No per-item shape suppression
  - status: accepted
  - rationale: The requester's own framing was that the warnings were unclearable; the answer is to make them clearable rather than to hide them.
- UR14 specl does not model a namespace registry and will not. `spec_base` and `prefix` live in front matter, and foreign prefixes live in the front matter of the referencing specification. There is no tool-level registry and none is planned.
  - title: No namespace registry
  - status: accepted
  - rationale: A registry is a second source of truth for a value the specification already declares.
- UR7 The severity gate is driven by the specification's own status rather than by a fixed severity threshold, with the original premise corrected.
  - title: Status-conditional severity model
  - status: accepted
  - rationale: A fixed threshold makes every warning either blocking or ignorable, and neither is a representable target.
- UR10 Each planned class has a pre-adoption path: content is authored under a prose marker before the class exists, and adoption becomes moving the section rather than rewriting it.
  - title: Pre-adoption path per planned class
  - status: accepted
  - affects: UR9, UR20
  - rationale: Adoption should be a mechanical lift rather than a rewrite.

# Open Questions

- UR22 Whether the process commitment under UR16 should itself be verifiable, given that release notes are prose and the observable condition for removing a compensation is stated in words rather than checked.
  - recommendation: Bind each compensation to a test the way the contract page binds its guarantees
  - status: open

# Design Considerations

The consumer is a federated RDF memory substrate specification, currently
pre-publication under an embargo. The original term was that the embargo lifts
when 0.3.0 ships. `docs/decisions/0007-internal-releases-until-1.0.md` makes
0.3.0 a tag rather than a publication, so read literally that term would hold the
consumer until 1.0, which is not what was agreed. The embargo lifts when 0.3.0 is
tagged and the w3id redirects are live, whichever is later, so that documents
citing specl IRIs resolve from the day they appear. The consumer is notified of
this amendment rather than left to infer it.

Seventeen requests were raised. All were answered: fourteen accepted, two scoped
down, one declined with the answer supplied instead. The full disposition is
`docs/proposals/0002-downstream-request-disposition.md`, and the requests as
received are `docs/proposals/0002a-downstream-requests-as-received.md`.

Identifiers UR1 through UR17 are the consumer's own request numbers. UR18 onward
are commitments this register makes that no request asked for, numbered in the
same sequence so that one identifier space covers everything a second party can
cite. A commitment is retired with `itemStatus` rather than deleted, because a
consumer may be holding the old answer.

This specification's status is `review` rather than `production` for a stated
reason: six commitments here are answers for releases that have not happened, so
they carry no acceptance criterion and no verification. At `production` the gate
fails on warnings, and those six would block it. `review` reports them without
blocking, which is the accurate description of a register whose answers are ahead
of its implementation. It moves to `production` when the last of them lands.

An item here carrying no `verifiedBy` is a commitment whose implementation has
not landed, and that absence is the honest state rather than an omission. The
shapes report it, and `tests/test_drift.py` checks that every claim present names
a test that exists.

The legacy base table, the exact reference resolution algorithm, the title
derivation details, and the identifier grammar are stated in full in
`docs/proposals/0002-downstream-request-disposition.md` under the matching UR
heading. This register states what is committed; that document states how it was
decided.
