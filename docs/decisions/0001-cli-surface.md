# CLI surface for the migration tool

**Status:** accepted, unimplemented. Applies to 0.3.0.

## Context

0.3.0 ships an IRI migration tool for consumers holding only Turtle. Early
drafts of the roadmap, the migration guide, and the downstream commitments
register all wrote it as `specl migrate-iris`, which implies an umbrella `specl`
command that does not exist.

The actual console scripts are `specl-translate`, `specl-validate`, and
`specl-assist`. Each is a verb-named binary; `specl-validate` carries
subcommands (`validate`, `diff`, `score`, `badge`).

Nobody recorded a decision about which shape the new tool takes. Three documents
asserted a fourth one by implication.

## Decision

**Add `specl-migrate` as a fourth console script**, with `iris` as its first
subcommand:

```
specl-migrate iris <old.ttl> <new.ttl> --spec-base <iri>
```

The subcommand exists so later migrations have somewhere to go without another
entry point.

Two corollaries, both correcting text written before this decision:

- The migration verification mode is `specl-validate diff --ignore-base`, not
  `specl diff --ignore-base`. `diff` is already a `specl-validate` subcommand and
  the flag extends it.
- The layering check is `specl-validate layering`, which was written correctly
  and needs no change.

## Alternatives

**An umbrella `specl` command** with the existing binaries as subcommands is the
better long-term surface: one entry point, discoverable help, no proliferation of
verb-binaries. It was rejected for 0.3.0 because it is an API break, and 0.3.0
already carries a graph break plus a mandatory front-matter key. Stacking a CLI
migration on top of a data migration makes the release harder to adopt for no
correctness gain.

It remains a candidate for 0.10.0 ergonomics, where the hyphenated names would be
retained as aliases rather than removed.

**Folding migration into `specl-translate`** was rejected because translation
reads markdown and migration reads Turtle. They share no input.

## Consequences

`pyproject.toml` gains one entry under `[project.scripts]`. Documentation that
referenced `specl migrate-iris` has been corrected. The `specl` bare command
remains unclaimed, which keeps the umbrella option open.
