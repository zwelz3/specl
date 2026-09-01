# The explorer's dist is build output, and its documentation may name it

**Status:** accepted. Applies from the explorer rewrite.

## Context

The rewritten explorer is authored as `explorer/explorer.html` with four empty
JSON slots, and built into `explorer/dist/explorer.html` by filling them from
the grammar, an example graph, and a validation report. The built file is what
is packaged as `src/specl/explorer.html`, hosted, and attached to a release.

`dist/` is generated, so it is not committed. The workflow rebuilds it on every
push that touches the explorer, copies it over the packaged copy, and warns if
the two had drifted. Committing it would put a second byte-identical 191 KB copy
in version control beside `src/specl/explorer.html` and produce two large diffs
for every change to one file. This is the same reasoning as
`0010-badges-are-published-not-committed.md`: derived data in version control is
a snapshot that disagrees with the tree between the change and the job that
regenerates it.

Both `explorer/README.md` and `explorer/STATUS.md` name `dist/explorer.html`,
because it is the artifact the reader is being told about: which file is hosted,
which one the guard checks, which one the smoke tests read. `tools/check_docs.py`
resolves referenced repository paths and found neither, since in a fresh clone
neither exists until something builds them.

That failure was not visible locally. The check passed in a working tree where
the build had already run, which is the blind spot invariant 12 in `CLAUDE.md`
describes: a claim tested only in the environment that happens to satisfy it.
CI would have caught it, in a job that runs `check_docs.py` and never builds the
explorer.

## Decision

**`dist/` stays uncommitted and gitignored.** `src/specl/explorer.html` is the
committed artifact, and the workflow's drift warning is the guard.

**The two references are declared in `tools/documented-gaps.toml` under
`[paths]`, citing this record.** The registry is the only exception route for
repository content, and an undeclared reference to a path that does not exist is
a failure whether or not a human would find it reasonable.

**What closes the entry is reversing the first half of this decision.** If
`dist/` is ever committed, the path exists and the entry is deleted. That is the
condition the registry asks every entry to name.

## Alternatives

**Commit `explorer/dist/explorer.html`.** Rejected. It satisfies the checker
with no registry entry and costs a duplicated 191 KB artifact and a doubled diff
on every explorer change.

**Skip path references that resolve inside a gitignored directory.** Rejected.
It is a general rule rather than a proximity heuristic, and it would still be a
second exception route in a checker whose registry is documented as the only
one. `0002-documented-gaps-registry.md` removed the last mechanism that
suppressed a finding without a record.

**Reword both documents so the references are not path-shaped.** Rejected. The
checker's pattern would stop matching and the documents would say less than they
do now. Writing around a check is not the same as answering it.

## Consequences

Any document may name the built file, because a `[paths]` entry is the path
rather than the pair of documents, which is looser than the per-document form
`[umbrella_mentions]` uses. Two spellings are registered: the relative
`dist/explorer.html` that documents inside `explorer/` write, and the
root-relative `explorer/dist/explorer.html` that this record and
`0006-artifact-agreement-strategy.md` write. If build output starts appearing
in documents that are not describing the build, that is a signal to tighten the
entry to a per-document form rather than to add a third spelling.

A fresh clone has no `dist/`, so `node build/build.mjs` is a prerequisite for
anything that reads it, including the two smoke tests. `explorer/README.md`
lists the command.
