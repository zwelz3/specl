# Disposition of upstream requests to specl

Response to `docs/proposals/0002a-downstream-requests-as-received.md`, raised by the unnamed memory substrate
specification (placeholder `xyzzy`).

Every request is answered. Fourteen are accepted in some form, two are accepted
with reduced scope, and one is declined with the answer supplied instead. Four
are answered normatively here rather than deferred to a release, because the
consumer needs them to author today and none requires code to state.

Two of the observations were checked against the artifacts rather than taken at
face value. Both hold, and one of them is my error.

## Verified before answering

**UR1's contradiction is real and mine.** `HANDOFF.md:104` states that
`https://spec.xyzzy.example/xyzzy/` is the shape specl will expect.
`docs/upstream-specl-notice.md:62` states it must become
`https://spec.xyzzy.example/xyzzy#`. Both were written in the same review pass.
The notice is correct and the handoff line is wrong.

**UR8's warning breakdown is exact.** Counted against the current graph: 21
`verifiedBy`, 21 `constrains`, 16 `acceptanceCriterion`, 9 `owner`, 5
`recommendation`, 3 `rationale`, 2 `affects`. The 42 unclearable warnings the
consumer reports are the first two categories, and both are structurally
unclearable at the present release.

**UR7's premise is partly wrong, and correcting it makes UR8 more serious.**
Shape severities are fixed in the shapes graph. Nothing is reclassified when
status advances. What changes is the gate: `gate()` in `validate_spec.py` fails
the run when violations exist, or when warnings exist and status is
`production`. So the answer to "which of the 77 become violations at
`production`" is that none of them do and all of them block. Combined with UR8,
the consequence is that the consuming specification cannot reach `production`
status today no matter how it is authored, because half its warnings have no
representable target. That converts UR8 from a metric-quality complaint into a
blocker.

## Group A: before the 0.3.0 migration

### UR1. `spec_base` grammar — accepted, answered now

**Hash termination is required.** Translation rejects a `spec_base` that does not
end in `#`, with a message naming the expected form. It does not append a missing
terminator, because silently altering an identifier base is the wrong default for
a value that becomes permanent.

- A bare authority with no path segment is rejected. `https://example.org#` is
  legal IRI syntax and terrible practice, and rejecting it costs nothing.
- A value containing a fragment beyond the terminating `#` is rejected.
- Slash-terminated bases stay unsupported in 0.3.0. Per-item dereferencing is a
  legitimate design that some projects will want, and it arrives with the
  slash-namespace option already noted as a post-1.0 extension, not before.

Rationale: items within one specification are authored, validated, and consumed
as a unit, which is what a hash namespace models. Slash termination asserts that
each item is a separately retrievable document, which is a claim specl cannot
currently honor.

**Downstream action:** the consuming repository's base becomes
`https://spec.xyzzy.example/xyzzy#`, and the erroneous handoff line is corrected.

### UR2. Legacy base table — accepted

Published with 0.3.0 in `NAMESPACE-MIGRATION.md`:

| Version                | Vocabulary                       | Instances                          |
| ---------------------- | -------------------------------- | ---------------------------------- |
| 0.1.0 – 0.2.0 (PyPI)   | `https://example.org/ekga/ns#`   | `https://example.org/ekga/spec/`   |
| unreleased `main`      | `https://w3id.org/specl/ns#`     | `https://w3id.org/specl/spec#`     |
| 0.3.0 onward           | `https://w3id.org/specl/ns#`     | project-supplied, required         |

`specl-migrate iris` recognizes both legacy instance bases as sources. It detects which
by prefix binding and fails rather than guessing when neither is present, which
is the behavior the consumer's post-processor currently implements by inference.

### UR3. Reference resolution algorithm — accepted, answered now

**String concatenation onto the base, not RFC 3986 relative resolution.**
`base + token`, with the token used verbatim.

- Dotted identifiers are therefore safe. `R2.1` against
  `https://spec.example.org/x#` yields `https://spec.example.org/x#R2.1`, with no
  dot-segment interpretation.
- The token must match the identifier grammar published under UR11. Anything else
  produces a parser warning and is emitted as a literal rather than silently
  discarded.
- **Prefixed tokens such as `SBL:D14` are not legal in 0.3.0.** There is no
  prefix map before layering exists, so accepting the syntax early would mint
  wrong IRIs. They become legal in 0.5.0, resolved through the front-matter
  declaration specified under UR15. Until then a prefixed token in a
  reference-valued field is a parser warning.

Concatenation is chosen over relative resolution because it is predictable under
both terminator styles and because relative resolution would make identifier
legality depend on base shape, coupling UR1 and UR3 permanently.

**Consequence the consumer asked for:** under hash termination and concatenation,
all 11 existing `affects` and `constrains` values migrate unchanged. That is now
derivable rather than asserted.

### UR4. `title:` fallback derivation — accepted, with a recommendation against relying on it

The fallback is **materialized into the emitted graph**, not computed at
validation time. A shape requires the property at Violation severity, and a
consumer reading the graph directly must see the same thing the validator saw.

Derivation, normatively: take the description, split at the first sentence
boundary (`.` or `;` followed by whitespace), strip trailing sentence
punctuation, and if the result exceeds 80 characters truncate at the last word
boundary within 80 and append an ellipsis.

This matches the consumer's post-processor exactly, so migration produces no
title diffs. That is deliberate, and it is also the weaker reason to specify it
this way.

**Recommendation:** author explicit `title:` values for all ten decision records
anyway. Depending on a derivation to satisfy a Violation-severity constraint
means a description edit can change a title silently, and titles are what appear
in every downstream rendering.

### UR5. Graph comparison modulo base — accepted, scoped

`specl-validate diff --ignore-base` normalizes instance IRIs in both graphs to a common
sentinel before comparison, so an IRI-only change reports as no difference. It
ships in 0.3.0, since migration verification is what it exists for.

Scoped down from "a graph-level comparison mode": this extends the existing
`diff` rather than adding a general graph-diff facility, which is a larger tool
than the problem needs.

## Group B: interpreting validation output

### UR7. Status-conditional severity model — accepted with the premise corrected

The mapping the request asks for does not exist because severity is not
status-conditional. Published in 0.3.0:

- Legal status values are `draft`, `prototype`, `review`, `production`. This
  enumeration currently appears only inside a shape message.
- The gate fails on any violation at any status, and additionally on any warning
  when status is `production`. `prototype` and `review` behave identically to
  `draft`, which is undocumented today and is the part genuinely worth
  publishing.
- Shape severities are fixed and released with the shapes graph.

So the remaining work to reach `production` is the full warning count, not a
subset. For the consuming specification that is 77, of which 42 are currently
unclearable, which UR8 addresses.

### UR8. Marking a shape expectation inapplicable — declined as requested, root cause accepted

**Declined:** a per-item suppression mechanism. A suppression key with a reason
field is a warning that has been made invisible, and it will be used to clear
warnings that should have been fixed. The consumer's own framing, that a
suppressed expectation should be visible as a decision, is right in principle,
and specl already has a construct for a recorded decision.

**Accepted instead:** fix the shapes so the unclearable warnings are not raised.

- The `constrains` warning becomes conditional on the graph containing at least
  one `specl:Component`. A specification that declares no components is not
  failing to link to them.
- The `verifiedBy` warning becomes conditional on a verification target class
  existing, which means it stays quiet until 0.6.0 introduces acceptance queries
  and then activates for specifications that adopt them.

This removes all 42 without adding a suppression facility. Both changes ship in
0.3.0 rather than waiting, because UR7 establishes that they currently make
`production` unreachable.

If a genuine inapplicability case survives after this, the answer is a design
note recording why, not a suppression key.

### UR9. Warn on unrecognized sections — accepted, moved earlier

**Moved from 0.6.0 into 0.3.0.** The argument in the request is correct and I
underweighted it: silent content loss makes experimentation indistinguishable
from success, which blocks incremental adoption of every class in the plan. It is
a small change and it should not wait for the release that makes the section map
extensible.

0.3.0 emits a warning for any unrecognized top-level section and fails under
`--strict`. 0.6.0 still carries the extensible map.

**Non-normative marker: accepted.** A section may be marked prose with an HTML
comment immediately beneath the heading, following the existing `<!--specl ... -->`
convention already used for front-matter extension. Marked sections are skipped
without warning and contribute nothing to the graph.

## Group C: authoring forward-compatibly

### UR10. Pre-adoption path per planned class — accepted

Published as a forward-compatibility appendix, updated when a release is planned
rather than when it ships.

For `specl:AcceptanceQuery`, publishable now: section heading
`# Acceptance Queries`, identifier prefix `Q`, one bullet per query with the
query intent as the description, and a `gates:` annotation taking a
comma-separated list of requirement identifiers.

**Answer to the consumer's specific question:** the prose mapping currently
written as "Gates R8" in running text should be restructured now into a
`gates: R8` sub-bullet under a `Q001` bullet, kept in its existing separate file
under a prose marker per UR9. Adoption then becomes moving the section into the
specification and deleting the marker.

### UR11. Reserved prefixes and identifier grammar — accepted

Reserved by specl, including for planned classes: `R`, `US`, `OQ`, `D`, `DN`,
`C`, `Q`.

Grammar: one or more uppercase ASCII letters, followed by one or more digits,
followed by zero or more dot-separated digit groups. Case sensitive. `D1` and
`D01` are **distinct identifiers**, because they are distinct strings and any
normalization would silently merge items; mixing padded and unpadded ordinals
within one specification produces a warning.

The prefix set is closed in 0.3.0. Project-declared prefixes arrive with the
extensible section map in 0.6.0, and will be required to be at least two
characters to keep the single-letter space reserved for specl.

**Consequence:** existing `Q` identifiers in the consumer's query set carry over
rather than colliding.

### UR12. Supersession semantics — accepted, answered now so it does not block

Specified now, mechanized in 0.4.0:

- A superseded or withdrawn item **is emitted** into the graph. Append-only means
  the item persists; the status records that it no longer applies.
- Shapes **do not evaluate** superseded or withdrawn items, except the shape that
  requires `supersededBy` when status is `superseded`. A retired item does not
  accumulate warnings.
- `supersededBy` **requires the successor to exist** in the same specification
  and to be of the same class. Cross-specification supersession is out of scope
  until 0.5.0 and will follow the UR15 syntax.
- A withdrawn item's identifier is **permanently reserved**. Reuse is a violation,
  not a warning.
- `withdrawn` differs from `superseded` in having no successor: it records that
  the item was struck, not replaced.

**Answer to the consumer's blocked open question:** resolve it by expressing the
outcome now in prose against these semantics, marking struck requirements as
withdrawn in their description text, and mechanizing at 0.4.0. Do not delete
them, and do not defer the resolution waiting for the mechanism.

## Group D: cross-specification work

### UR13. Layering resolution and offline operation — accepted without qualification

The validator **never performs network access.** The upstream declaration names a
prefix, a base IRI, and a local path to the peer specification's markdown or
emitted graph. Resolution reads that path. A missing or unreadable peer produces
a warning and the check reports as inconclusive rather than passing or failing,
so an unavailable peer cannot silently turn into a pass.

This is the correct constraint independent of the consumer's environment: a
validator that fetches at check time is non-deterministic in CI, which is
disqualifying on its own.

### UR14. Does specl own a namespace registry — declined, answered plainly

**No.** specl does not model a registry of specification namespaces. `spec_base`
and `prefix` live in front matter, and foreign prefix declarations live in the
front matter of the specification that references them, per UR15. There is no
tool-level registry and none is planned.

**Downstream consequence:** the consuming repository's `spec/registry/prefixes.ttl`
is not a tool input and will not become one. Retitle it as a governance record if
the allocation history is worth keeping, or delete it at migration. Its file
comments and the post-processor docstring both currently overstate its role and
should be corrected either way.

### UR15. Cross-specification reference syntax — accepted

Authored syntax in reference-valued fields is `PREFIX:ID`, matching the prose
CURIE convention.

Foreign prefixes are declared in the referencing specification's front matter:

```yaml
references:
  SBL:
    base: https://spec.example.org/sibyl#
    path: ../sibyl/spec/sibyl-spec.md
```

References are **resolved to IRIs always and validated when the peer is
available.** An unresolvable foreign specification produces a warning, not a
failure, and the reference is still emitted as an IRI. A reference to a declared
peer that resolves to a nonexistent item in that peer is a warning at parity with
the local dangling-reference warning from UR3.

This is what lets the direction rule become a graph constraint instead of a
prefix grep.

## Group E: release process

### UR16. Per-release obsolescence notes — accepted

Each release's notes gain a section naming the downstream compensations the
release makes unnecessary and the observable condition for removing each. For
0.3.0 that names the consumer's post-processor explicitly, with both halves
(namespace rebase and title derivation) and their conditions.

Cheap, and it moves a guess about upstream behavior to the party that knows it.

### UR17. Versioned fetchable shapes and vocabulary — accepted, with one constraint

Both are published at versioned locations and remain shipped inside the package.
Validation resolves them from the package by default and never fetches at
validation time. The published copies exist for pinning, review, and diffing
between releases, not as a runtime dependency, because UR13's offline constraint
applies here equally.

The version relationship is stated explicitly: the graph contract version from
UR6 identifies the vocabulary and shapes pair, and it is not the tool version.

### UR6. The versioned graph contract — accepted, scoped

Published as a versioned document alongside the header field: the class list, the
property list, each property's range, whether it is object- or datatype-valued,
and cardinality expectations.

**Scoped down:** per-term stability tiers are deferred. Assigning stability to
terms in a vocabulary that will gain classes in four of the next five releases
would record an assurance that cannot be honored. Tiers arrive at 0.11.0, when
the second graph break closes and the contract is a freeze candidate.

The request's underlying point is granted without reservation: the property-range
defect is exactly what a published contract would have exposed, since three
properties were declared object-valued while emitting literals and no artifact
recorded the discrepancy.

## Changes to the release plan

Four items move earlier than the roadmap placed them, all into 0.3.0:

- UR9's unrecognized-section warning, from 0.6.0. Silent content loss blocks
  incremental adoption of everything downstream of it.
- UR8's shape conditioning, previously unplanned. Without it the consuming
  specification cannot reach `production` at any point in the plan.
- UR5's `diff --ignore-base`, previously unplanned. It verifies the 0.3.0
  migration, so it has to ship with it.
- UR2, UR6, UR7, UR11, and UR16 are documentation deliverables attached to 0.3.0
  rather than code.

Nothing moves later. UR12, UR13, and UR15 are answered now and built in the
releases already scheduled for them, which is the distinction the request
document draws in its own opening and which turned out to be the right frame for
most of this.

## Corrections to make downstream immediately

1. `HANDOFF.md:104` states the wrong base shape. Correct it to hash termination
   and align the Makefile.
2. `spec/registry/prefixes.ttl` and `tools/specl_post.py` both describe the
   registry as driving the namespace rebase. It does not; a build variable does.
3. The CLAUDE.md characterization of warnings tightening at `production` should
   say that the gate changes rather than that severities change, and should state
   that all warnings block.
4. The acceptance query prose should be restructured per UR10 now rather than at
   0.6.0.
