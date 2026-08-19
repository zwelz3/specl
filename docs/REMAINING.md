# What is left

Compiled from `docs/ROADMAP.md`, `docs/decisions/0006-artifact-agreement-strategy.md`,
and `specs/commitments/spec.md`. Nothing here requires a graph break: both
designated breaks are spent, and 1.0 freezes the contract rather than the
feature list.

## Blocking 1.0

Nothing. All five criteria are met; `docs/ROADMAP.md` carries the table. The w3id pull request merged on 2026-08-19, which closed the last one.

Verified 2026-08-19: all thirteen paths return 303 to their declared targets, and `ns` negotiates Turtle and JSON-LD correctly. Nothing in CI can check this, so it is re-run by hand whenever the rules change.

## Deferred to 2.0

These join the collection window rather than trickling through 1.x. From 1.0 they are not the author's to decide alone. Neither is now expected to change an IRI or a property range: what puts them here is that they are syntax and vocabulary changes, which `GOVERNANCE.md` governs whether or not they break a graph.

**The component-name abbreviation.** A specification family can already share a component: write the absolute IRI and every specification naming it names the same node. What waits for 2.0 is the front-matter map that shortens `constrains: https://example.org/components#engine` to `constrains: engine`.

This is no longer expected to break anything. The earlier claim that adopting a map moves every component IRI held only for a project that had already minted local hashed nodes; one writing absolute IRIs has nothing to abbreviate yet and nothing to move. Personas and agents were never affected. See `docs/proposals/0003-g3t-component-identity-disposition.md`.

The open design question is whether a declared component namespace should carry a `path` the way `vocabularies:` does, so a typo in an absolute IRI is caught. Today it is not, and a misspelled IRI is a valid IRI naming a node nothing else references.

**Agent integration.** An MCP server for the deterministic verbs and a skill for
the authoring rules, plus `--print-prompt` on `gaps` and `check`. The analysis,
including why those two subcommands are not deprecated, is in the roadmap. Only
the parts touching the graph need to wait for 2.0.

## Known and unscheduled

**Five ontology findings**, all additive, none blocking:
assessment terms restate W3C DQV, `specl:Test` overlaps EARL, labels carry no
language tags and SKOS cardinality is unenforced, functional properties are
declared sparingly and worth revisiting if consumers reason rather than
validate, and there are no inverse properties.

## Open in the agreement inventory

Three pairs in `0006` are unassigned. The section table and the annotation table
in `docs/SYNTAX.md` restate `SECTION_MAP` and `PROP_MAP` in prose; both are
straightforward tier 2 checks. The assistant's prompts assert what a good
specification looks like and nothing compares them to the shapes they exist to
help satisfy.

## Open in the commitments register

`UR16`, per-release obsolescence notes, is the one commitment with no
verification. `UR22` asks whether it can be verified at all, since release notes
are prose and the condition for removing a downstream compensation is stated in
words. Every other commitment carries a `verifiedBy` checked against the test
suite on each run.

## Optional, no longer urgent

`status:` remains context-sensitive alongside the explicit `decisionStatus:` and
`resolutionStatus:` added in 0.11.0. Retiring the ambiguous key is an authoring
change rather than a graph change, so it is available at any time and blocks
nothing.
