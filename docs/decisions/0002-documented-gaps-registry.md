# One registry for everything documentation may reference before it exists

**Status:** accepted, implemented. Applies to `tools/check_docs.py`.

## Context

The doc checker fails when a document references a repository path, console
script, or subcommand that does not exist. Two categories of reference are
legitimate anyway. A downstream consumer authors against announced behavior, so
naming an unshipped command is necessary. A known defect has to be written down,
so naming a dangling path is necessary.

Two different mechanisms had grown for these.

Unimplemented CLI surface was declared in tools/planned-cli.toml, with each
entry naming the decision record that authorized it. The checker verified the
record existed.

A dangling path was exempted instead by proximity: the checker flattened the
document and skipped the finding if `does not exist`, `is missing`, or `dangling`
appeared within 120 characters of the reference.

The proximity rule suppresses on coincidence. Appending a backticked reference to
a nonexistent file under docs/, followed by an unrelated sentence containing the words
"is missing" produced a passing run. Nothing is recorded, nothing names who owes
the fix, and the suppression is invisible in review because it lives in prose
rather than in a registry.

That mechanism is also the shape this project declined downstream. A per-item
shape suppression with a reason field was refused on the grounds that it makes a
warning invisible. A keyword in prose that silences a checker is the same trade
with less ceremony.

## Decision

**One registry, `tools/documented-gaps.toml`, covering every category.** It
replaces tools/planned-cli.toml and carries four tables: `[scripts]`,
`[validate_subcommands]`, `[paths]`, and `[umbrella_mentions]`. Every entry
names a `record`, and the checker fails when that record does not exist.

**The proximity heuristic is removed.** A dangling path is either fixed or
registered. Registering it is a claim that the absence is tracked, and the named
record says what closes it.

**`[umbrella_mentions]` is scoped per document and per verb.** A document that
quotes `specl migrate-iris` while describing the defect declares that verb, and
declaring it does not license a different bare-`specl` invocation elsewhere in
the same file.

`EXCLUDE` and `FOREIGN_PATHS` stay in the checker. They cover documents received
from elsewhere, whose references describe another repository and are not claims
about this one. That is a different category from an exception granted to this
repository's own content.

## Alternatives

**Keep the proximity rule and tighten the window.** Rejected. A narrower window
changes how often it misfires, not whether the suppression is recorded.

**Require a marker comment beside the reference,** such as `<!--gap-->`.
Rejected because the marker travels with the prose rather than with the registry,
so no single place answers what this repository currently owes.

**Drop the path check.** Rejected. It found the reference this record's
companion fix removed.

## Consequences

`README.md` no longer references the ISSUES.md file under
specs/specl_explorer/; the sentence
now points at `docs/ROADMAP.md`, which covers the same deferred material. P15 is
closed, and `[paths]` is empty on arrival. An empty table is the intended
steady state.

The umbrella check found three references nobody had noticed: an unreleased
changelog entry, a released one, and an open question in specl's own
self-specification. The unreleased entry and the open question were corrected.
The released entry is registered, because a shipped changelog section records
what was said at the time.

A retired name mentioned in prose is written without backticks, which is what
distinguishes describing a name from asserting a path. The registry is for gaps
that will close, not for names that are gone.
