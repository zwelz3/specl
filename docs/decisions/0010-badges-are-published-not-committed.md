# Badges are published, not committed

**Status:** accepted. Applies from 1.0.

## Context

A CI job downloaded the badge artifacts after each push to main, committed the
regenerated SVGs, and pushed them. Every subsequent local push was then rejected
until the bot's commit was pulled, on a repository with one developer where the
bot's only contribution was a rendering of a number.

The friction was the visible half. The other half is that a committed badge is a
snapshot: it describes whichever commit last triggered the job, and disagrees
with the current state between that push and the next one. This project spent
eleven releases removing artifacts that could disagree with each other, and this
one was generating a new disagreement on a schedule.

## Decision

**The badges are built by the Pages workflow and served from the site.** Nothing
is committed, so there is no bot commit and nothing to pull before pushing.

**They are generated during that build rather than copied from the tree,** so a
badge describes the commit being published rather than whenever someone last
committed one. `static/badges/` is deleted.

**The README references the published URLs.** GitHub proxies remote images
through its own cache, so a badge can lag a push by minutes. That is true of
every hosted badge and is a smaller cost than a rejected push.

## Alternatives

**Keep the job and pull before pushing.** Rejected. It works, and it makes every
contributor absorb a step that exists only because derived data is in version
control.

**Commit badges only on tag.** Rejected. It reduces the frequency of the
conflict without removing it, and makes the badge stale by design between tags.

**Push to an orphan branch.** Rejected. It solves the conflict and keeps the
snapshot problem, at the cost of a branch whose purpose nobody remembers.

**A shields.io endpoint.** Rejected. It removes the conflict too, and it adds a
third-party dependency in the render path and discards the palette, which was
chosen for measured contrast rather than appearance.

## Consequences

The Pages workflow installs the package rather than rdflib alone, because it now
runs `specl-translate` and `specl-validate badge`.

A badge is unavailable if Pages is down or disabled, where before it was a file
in the repository. Acceptable for a rendering of a number that the `score`
command prints on demand.

An adopter following the workflow documentation should not commit badges either,
and the README says so where it describes CI.
