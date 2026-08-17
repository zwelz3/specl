# Instance bases for specl's own specifications

**Status:** accepted. Applies to 0.3.0.

An earlier draft of this record proposed bases under `zwelz3.github.io` and
rejected the w3id path on two grounds that were factually wrong. Both are
corrected below, in the section recording what the registration contains,
because the correction is the substance of the decision.

## Context

0.3.0 makes `spec_base` mandatory and stops minting instance IRIs under a shared
namespace. Every specification in the repository needs a base before it will
translate, and the values become permanent the moment 0.3.0 ships:
`docs/DOWNSTREAM-COMMITMENTS.md` permits an IRI change only in a designated
breaking release, so a base chosen now holds until 0.11.0.

The repository also holds three specifications that describe unrelated example
systems. They were serving two jobs at once, as the demonstration corpus and as
published instances, and only one of those jobs needs an identifier.

## What the registration contains

`https://w3id.org/specl/ns` resolves. The rules live at `specl/.htaccess` in the
perma-id/w3id.org repository, and four facts follow.

**The registration covers the whole `/specl/` path,** not the `ns` term. Adding
a rule is an edit to a file already maintained by this project.

**Every rule redirects to `zwelz3.github.io`.** w3id.org hosts nothing and is
redirect-only, which is the point of it: the IRI is stable while the host behind
it is not. Putting the hosting account into the identifier discards the
indirection layer that already exists.

**The retired namespace resolves today.** `^spec/?$` redirects to the
repository's specs directory. Retiring it is not only a changelog statement.

**Rules are exact-match rather than path-preserving.** A client resolving
`.../spec#R1.1` strips the fragment and requests `.../spec`, so one rule serves
a whole specification regardless of item count.

## Decision

**specl's own specifications take bases under the registered path.**

| Specification  | `spec_base`                              | `prefix` |
| -------------- | ---------------------------------------- | -------- |
| specl_tool     | `https://w3id.org/specl/tool/spec#`      | `TOOL`   |
| specl_explorer | `https://w3id.org/specl/explorer/spec#`  | `EXPL`   |

**The retired base is not reused.** `https://w3id.org/specl/spec#` stays retired
and is not reassigned to specl_tool, despite specl_tool being the only remaining
claimant. That string is published, is registered as the legacy migration source,
and carries items from five specifications in graphs already distributed.
Reassigning it would not retire it; it would narrow what it refers to without
changing the string, so a consumer merging a pre-0.3.0 graph with a post-0.3.0
graph would get a false join on exactly the identifiers that collided. It would
also defeat `specl-migrate iris`, which is committed to detecting the legacy
namespace by prefix binding and could no longer distinguish a migrated graph
from an unmigrated one.

The existing `^spec/?$` rule is repointed at `NAMESPACE-MIGRATION.md` rather
than removed, so distributed identifiers continue to land somewhere that
explains them.

**Each base fixes the Specification IRI as well as the item IRIs.** The
Specification node is the base without its terminating hash, so specl_tool's
specification is `https://w3id.org/specl/tool/spec` and its items are fragments
under it. `spec_id` is not part of any IRI. See
`docs/decisions/0004-graph-contract-version.md`, which settles that and follows
the pattern `src/specl/core.ttl` already uses for the vocabulary.

**The two segments are symmetric and permanent.** `tool` and `explorer`, not the
directory names, and no version anywhere in the base. An item keeps one
identifier across revisions of the specification containing it; versioning lives
on `dct:hasVersion`.

**The three example specifications move to `tests/fixtures/` and take bases
under `https://example.org/specs/<name>#`.** That domain is reserved by RFC 2606
and will never resolve, which is correct for a fixture and removes the
identifier question for them entirely. They keep their job as the collision
demonstration and as the corpus P14 builds goldens from, and they stop being
published instances.

## Consequences

Two w3id rules are added and one is repointed. Redirect targets are source files
already on GitHub, so nothing new is hosted. `tools/w3id/specl.htaccess` holds
the intended rules and is the source of truth for the upstream pull request.

The CI matrix drops from five specifications to two, and three badges are
deleted. `NAMESPACE-MIGRATION.md` and `HANDOFF.md` cite the collision
demonstration at its new path.

Invariant 8 in `CLAUDE.md` prohibits minting instance IRIs under a specl-owned
domain, on the rationale that a user's requirements are the user's data. specl's
own specifications satisfy that rationale rather than violating it, but the
wording does not say so, and reading around it silently is not appropriate. The
invariant is amended to state the distinction: the prohibition is against
placing a user's items in the tool's namespace, not against a project using a
namespace it controls.

With the examples gone, the objection that motivated the earlier draft
disappears. No shipped specification is presented as a base to copy, and
`docs/SYNTAX.md` states the rule directly: the base must be a namespace the
project itself controls, of which w3id is one option among several.

Exit criterion 1 for 0.3.0 remains checkable. Translating specl_tool and
specl_explorer and merging must yield zero shared item IRIs, and the fixtures
provide the same check against a pair that collided before the fix.
