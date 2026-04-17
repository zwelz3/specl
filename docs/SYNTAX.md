# specl markdown syntax

Reference for the spec format consumed by `specl-translate`.

## Front-matter

A spec begins with a YAML block delimited by `---`:

```markdown
---
spec_id: myproject-001
title: My Project
version: 0.1.0
status: prototype
---
```

`status` must be one of `draft`, `prototype`, `review`, `production`.
The status drives the CI gate: Warnings fail the build only at
`production`.

Additional spec-level metadata can go in a `<!--specl -->` comment
block anywhere in the document:

```markdown
<!--specl
created: 2026-01-15
-->
```

## Sections

H1 headings delimit structured sections. Recognized section names and
the class they produce:

| Section | Class | ID prefix |
|---------|-------|-----------|
| `# Intent` | (folds into Specification) | — |
| `# Purpose` | (folds into Specification) | — |
| `# Requirements` | Requirement | `R` |
| `# User Stories` | UserStory | `US` |
| `# Open Issues` / `# Open Questions` | OpenIssue | `OQ` |
| `# Decisions` | DecisionRecord | `D` |
| `# Design Considerations` | DesignNote | auto-hash |
| `# Comments` | Comment | auto-hash |

## Bullets and sub-bullets

Items live under structured sections as bullets with an ID prefix:

```markdown
- R1.1 The library MUST do the thing.
  - priority: MUST
  - constrains: ComponentA, ComponentB
  - acceptance: Given X, when Y, then Z.
  - verifiedBy: tests/test_thing.py::test_it
```

Sub-bullets are indented two or more spaces (or a tab) under the parent
bullet. Each sub-bullet matches the pattern `- key: value` where `key`
is one of the recognized annotation keys.

### Multi-value annotations

Two mechanisms, used for different purposes:

**Comma-split** (atomic identifier keys: `constrains`, `affects`):

```markdown
  - constrains: HolonicDataset, HolonicStore, Backend
```

produces three separate `ekga:constrains` triples.

**Multiple sub-bullets** (prose keys: `acceptance`, `verifiedBy`, or
any key where commas appear naturally in the value):

```markdown
  - acceptance: Given a fresh dataset, when add_holon is called, then iri appears in list_holons.
  - acceptance: Given an existing holon, when add_holon is called again, then the duplicate is rejected.
```

produces two separate `ekga:acceptanceCriterion` triples, with commas
inside each value preserved.

## Annotation key reference

| Key | RDF property | Classes | Multi-value |
|-----|--------------|---------|-------------|
| `priority` | `ekga:priority` | Requirement | single |
| `acceptance` | `ekga:acceptanceCriterion` | Requirement, UserStory | multiple sub-bullets |
| `verifiedBy` | `ekga:verifiedBy` | Requirement | multiple sub-bullets |
| `constrains` | `ekga:constrains` | Requirement | comma-split |
| `asA` | `ekga:asA` | UserStory | single |
| `soThat` | `ekga:soThat` | UserStory | single |
| `owner` | `ekga:owner` | OpenIssue, DecisionRecord | single |
| `recommendation` | `ekga:recommendation` | OpenIssue | single |
| `status` | `ekga:resolutionStatus` or `ekga:decisionStatus` | OpenIssue / DecisionRecord | single |
| `rationale` | `ekga:rationale` | DecisionRecord | single |
| `affects` | `ekga:affects` | DecisionRecord | comma-split |

`status:` is context-sensitive. On an `OQ`-prefixed bullet it maps to
`ekga:resolutionStatus` (enum: `open`, `in-review`, `resolved`,
`deferred`). On a `D`-prefixed bullet it maps to `ekga:decisionStatus`
(enum: `proposed`, `accepted`, `superseded`, `rejected`).

## Backward compatibility

Sub-bullets are entirely optional. A spec with no sub-bullets produces
exactly the same RDF it would have in specl 0.1.x. Teams can
adopt annotations incrementally.

## Strict mode

`specl-translate --strict spec.md spec.ttl` prints parser warnings
to stderr: unrecognized annotation keys, sub-bullets with no parent,
ID prefix mismatches. Warnings are diagnostic only — the translation
still succeeds.
