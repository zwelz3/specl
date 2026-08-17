# The commitments register is a specification

**Status:** accepted. Applies from 0.5.0.

## Context

`docs/DOWNSTREAM-COMMITMENTS.md` was prose. It is the document a second party
read and made irreversible authoring decisions against, and it is the only
artifact in this repository whose readership is external.

Three consecutive releases under-delivered against it. P16's identifier grammar
was published there and not implemented. The title derivation left two details
unspecified there and an independent implementation would have diverged on both.
0.4.0's supersession semantics named four rules there and shipped two. Each was
caught by hand, and each had the same cause: the roadmap summarizes what the
register commits, the summary is shorter, and the summary is what gets built.

`docs/decisions/0006-artifact-agreement-strategy.md` left this pair unassigned
and named it the largest and hardest of the three remaining. It also named the
answer.

## Decision

**The register becomes a specl specification at `specs/commitments/spec.md`,
translated, validated, and scored in CI alongside the other two.** Each committed
clause is an item with an identifier, a status, and where the implementation
exists, a `verifiedBy` claim that `tests/test_drift.py` checks against pytest
collection. A clause whose implementation has not landed carries no verification,
which the shapes report, so the gap is visible rather than inferred.

**Identifiers are the consumer's request numbers.** `UR1` through `UR17` are what
the consumer wrote and what both parties cite. `UR18` onward are commitments this
register makes that no request asked for, numbered in the same sequence so one
identifier space covers everything a second party can reference. A conversation
about UR11 resolves to `https://w3id.org/specl/commitments/spec#UR11`.

**Project item prefixes move from 0.6.0 to now.** `SECTION_MAP` hardcodes the
reserved prefix each section accepts, so `UR11` would have warned. An
`item_prefix` front-matter key declares a project's own prefix, at least two
characters and never one of the reserved seven, accepted in any item section.
Pulling a capability forward breaks nobody, and the alternative was permanently
wrong identifiers: renumbering waits for 0.11.0.

**The old path becomes a pointer,** not a copy. A copy would be a seventh
artifact restating the sixth, which is what this strategy exists to prevent.

**The register's status is `review`, not `production`, and says why.** Six
commitments are answers for releases that have not happened and carry no
verification. At `production` the gate fails on warnings and those six would
block it. `review` reports them without blocking, which accurately describes a
register whose answers run ahead of its implementation. It moves to `production`
when the last of them lands.

## Alternatives

**A machine-readable companion alongside the prose.** Rejected. Two documents
saying the same thing is the defect being fixed, not a fix.

**Wait for 0.6.0, when project prefixes were already scheduled.** Rejected. 0.5.0
carries the largest committed surface of any remaining release, including the
reference syntax and the layering semantics, and is therefore the release most
likely to be under-delivered the same way the last three were.

**Codify with `R` identifiers and drop the UR correspondence.** Rejected. The
consumer cites UR numbers in its own documents, and an IRI change waits for
0.11.0, so the wrong choice here is permanent for six releases.

**Convert the disposition document too.** Rejected. It records how each request
was decided, including reasoning that was later corrected. That is a history, and
histories are prose.

## Consequences

`https://w3id.org/specl/commitments/spec#` is a third permanent base and needs a
w3id rule. It is added to `tools/w3id/specl.htaccess` with the others.

The register scores 78% with 26 warnings, and that number is now visible on every
run rather than being a property nobody measured. Most of the warnings are the
six unimplemented commitments and the missing acceptance criteria on clauses that
predate the acceptance convention.

`specl:itemPrefix` joins the vocabulary. It is distinct from `specl:prefix`,
which is how other specifications refer to this one, and the two are easy to
confuse.

One pair in the 0006 inventory closes. Two remain: the section table and the
annotation table in `docs/SYNTAX.md`.
