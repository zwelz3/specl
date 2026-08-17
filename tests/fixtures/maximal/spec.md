---
title: Maximal fixture
spec_base: https://example.org/specs/maximal#
prefix: MAX
vocabularies:
  skos:
    base: http://www.w3.org/2004/02/skos/core#
references:
  UP:
    base: https://example.org/specs/upstream#
    path: ../upstream/spec.ttl
  DOWN:
    base: https://example.org/specs/downstream#
    path: ../downstream/spec.ttl
dependsOn: UP
refines: UP
upstreamOf: DOWN
spec_id: maximal-001
version: 1.2.3
status: prototype
---

<!--specl
created: 2020-01-01
-->

# Intent
Exercise every section type and every annotation key the translator recognizes,
so that shapes coverage is checked against what the translator can actually
produce rather than against what it is assumed to produce.

# Purpose
Serve as the input to the coverage assertion and as a golden that changes
whenever the emission surface changes.

# Requirements

- R1 The system MUST exercise every requirement annotation.
  - title: Exercise every requirement annotation
  - priority: MUST
  - implementation: implemented
  - acceptance: Given a fixture, when translated, then every annotation appears
  - verifiedBy: tests/test_shapes_coverage.py::test_violation_paths_are_producible
  - constrains: Translator, Emitter
  - affects: UP:R1
  - governs: skos:Concept

- R1.1 A dotted identifier with one group MUST translate.
  - priority: SHOULD
  - itemStatus: superseded
  - supersededBy: R1

# Agents

- AG1 The maintainer accountable for this repository.
  - prefLabel: Maintainer

# Personas

- P1 The maintainer who runs this fixture.
  - prefLabel: Maintainer
  - altLabel: repository maintainer

# User Stories

- US1 As a maintainer, I want every user story annotation exercised, so that coverage is real.
  - role: P1
  - capability: every user story annotation exercised
  - benefit: coverage is real
  - acceptance: Given this fixture, when translated, then role, capability, and benefit appear

# Open Questions

- OQ1 Whether the coverage assertion should treat warnings as required.
  - owner: AG1
  - recommendation: Treat Violation severity as required and Warning as advisory
  - resolutionStatus: open

# Decisions

- D1 Use one maximal fixture rather than one fixture per annotation key.
  - decisionStatus: accepted
  - rationale: A single input keeps the emission surface visible in one golden
  - affects: R1, R1.1

# Acceptance Queries

- Q001 Every annotation key the translator recognizes appears in the emitted graph.
  - gates: R1, R1.1

# Verification Notes
<!--specl: parked, exercising the pre-adoption marker-->

Prose parked under a marker, so this heading does not warn.

# Open Issues

- OQ2 Whether the alias heading `Open Issues` should remain, given `Open Questions` reads better.
  - resolutionStatus: open
  - owner: AG1

# Design Considerations

The design notes section carries prose rather than identified bullets, so its
items are keyed by content hash.

# Comments

A comment section, present so the golden covers the last unbulleted class.
