# Tagged internally, published at 1.0

**Status:** accepted. Applies from 0.3.0 onward.

## Context

The roadmap runs to 1.0 through nine intermediate releases, two of which break
the graph contract. Publishing each one to PyPI would mean asking anyone who
installed it to migrate on the project's schedule rather than their own, and
`docs/ROADMAP.md` already names that failure mode: a project that breaks its
consumers repeatedly teaches them that upgrading means migrating.

PyPI currently carries 0.2.0, and only 0.2.0. That version predates every fix in
0.3.0: its item IRIs collide across specifications, its decision records cannot
pass their own gate, its object properties carry literals, and it stamps
translation time into every graph.

Two things in the repository assumed publication would resume before 1.0, and
both are commitments rather than conveniences.

## Decision

**Two states, named separately.**

*Tagged* means the version is closed in this repository: the changelog section is
dated, `pyproject.toml`, `src/specl/__init__.py`, and `core.ttl`'s
`owl:versionInfo` carry the number, the exit criteria for that release pass, and
a git tag marks the commit. Tagging is internal and happens per release.

*Published* means a distribution on PyPI. It happens once, at 1.0.

Every use of "ships" in the roadmap, the commitments register, and the exit
criteria means tagged unless it names publication.

**The w3id pull request stops gating the tag and starts gating the embargo.**
Exit criterion 9 for 0.3.0 required the redirects to be live before the release.
Under internal tagging that is the wrong dependency: an IRI is an identifier
whether or not it resolves, nothing in this project fetches one, and no installed
copy of 0.3.0 will exist. What the redirects actually gate is the moment someone
outside this repository starts publishing documents that cite those IRIs, which
is the downstream embargo lifting.

**The embargo term is redefined and the consumer is told.**
`docs/DOWNSTREAM-COMMITMENTS.md` says a downstream specification is held
pre-publication under an embargo that lifts when 0.3.0 ships. Read against this
decision, that term would hold the consumer until 1.0, which is not what either
party agreed to. The embargo lifts when 0.3.0 is tagged and the w3id redirects
are live, whichever is later. This changes the meaning of a commitment made to
another party, so it is not a silent amendment: the consumer is notified.

**The README stops recommending a stale install.** `pip install specl` returns
0.2.0 and will keep doing so for the whole run to 1.0. The install section says
which version PyPI carries, what is wrong with it, and how to install from the
repository instead.

## Alternatives

**Publish each release.** Rejected for the reason the roadmap already gives.
Nine releases, two of them graph-breaking, is a migration schedule imposed on
consumers who did not ask for one.

**Yank 0.2.0 from PyPI.** Rejected. Yanking breaks anyone pinned to it and the
version is not dangerous, only outdated. Saying plainly what it is costs a
paragraph in the README and breaks nothing.

**Publish pre-releases, `0.3.0rc1` and so on.** Rejected as the worst of both.
It carries the maintenance surface of publication and the instability of
development, and pip installs a pre-release only when asked, so the people who
would get it are the ones who least need protecting from it.

**Leave the embargo term as written.** Rejected. It would hold the consumer's
work for the entire run to 1.0 on a reading of "ships" they never agreed to,
which is a commitment quietly broken rather than renegotiated.

## Consequences

The gap between PyPI and this repository widens for the whole run to 1.0, and
the README carries that fact rather than leaving someone to discover it after
installing.

Exit criterion 9 moves from the 0.3.0 list to the embargo condition. Criteria 1
through 8 are executable and pass, so 0.3.0 can be tagged now.

Two unreleased changelog sections is the normal state during this run rather than
a problem to resolve. A section is dated when its release is tagged.
