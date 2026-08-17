# What is left

Compiled from `docs/ROADMAP.md`, `docs/decisions/0006-artifact-agreement-strategy.md`,
and `specs/commitments/spec.md`. Nothing here requires a graph break: both
designated breaks are spent, and 1.0 freezes the contract rather than the
feature list.

## Blocking 1.0

1.0 marks a change in who may change the specification rather than a claim that
it is finished; see `docs/decisions/0009-what-1.0-means.md`. Three of its five
criteria are met. The three open items below are all achievable now, which the
previous criteria were not.

**Published IRIs must resolve. This is the only criterion still open.** One pull request against perma-id/w3id.org.
Nine rules are new and one target changes; `tools/w3id/README.md` carries the
measured delta, the ordering constraint that Pages must serve a target before a
redirect to it merges, and the verification loop. A stability promise over
identifiers that return 404 is not worth making.

**Done: known limitations.** `LIMITATIONS.md`, linked from the top of the
README.

**Done: the governance mechanism.** `GOVERNANCE.md`. Additive changes land
whenever ready; substantive ones are collected in a one-year window opening at
1.0 and released as 2.0. An adopter registry so silence means something, an
explicit list of what is not governed, issue templates, a register of collected
proposals, and a test asserting the window length agrees across artifacts.

## Deferred to 2.0

Each is expected to break something, so they join the collection window rather
than trickling through 1.x. From 1.0 these are not the author's to decide alone.

**Multi-specification projects and component identity.** Components, and by
extension shared personas and agents, are minted under the referencing
specification's base, so one entity named by three specifications is three
nodes. Adopting a fix moves every component IRI a project had. It should be
designed with the people who hit it rather than invented first.

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
