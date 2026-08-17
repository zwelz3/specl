# Upstream requests to specl

Raised by a downstream consumer: the unnamed memory substrate specification
(placeholder `xyzzy`), currently authored against specl 0.2.0 with a local
post-processor, pre-publication, and holding under a publication embargo until
0.3.0 ships and the migration completes.

These requests concern what specl must state, not what it must build. The
release plan already names the features. What is missing is the specified
behavior a downstream project needs in order to decide, without guessing, what
to author today, what to defer, and what will change under it.

Each request records the observation that prompted it and the downstream
decision it unblocks.

## Group A: required before the 0.3.0 migration can be executed

### UR1. Specify the `spec_base` value grammar, including separator handling

**Request.** State normatively whether `spec_base` must be hash-terminated,
slash-terminated, or either. If a terminator is required, state whether
translation appends a missing one, rejects the value, or warns. State whether a
bare-authority value with no path is legal, and whether a fragment already
present in the value is preserved or replaced.

**Observation.** Two documents in the consuming repository, written in the same
review pass, state opposite requirements for the same value. One holds that the
existing `https://spec.xyzzy.example/xyzzy/` is the shape specl will expect; the
other holds that specl expects hash termination so items resolve within one
document, and that the value must become `https://spec.xyzzy.example/xyzzy#`.
Nothing in the release description settles it.

**Unblocks.** The base is the first cross-repository contract this project
emits. It cannot be chosen while the required shape is ambiguous, and it cannot
be corrected cheaply after a downstream specification cites an item under it.

### UR2. Publish the complete set of legacy instance and vocabulary bases, per released version

**Request.** Publish a table of every instance base and vocabulary namespace
minted by each released specl version, and state which of them `migrate-iris`
recognizes as a migration source.

**Observation.** The release description identifies `https://w3id.org/specl/spec#`
as the retiring instance base. Installed specl 0.2.0 mints under
`https://example.org/ekga/spec/` with vocabulary `https://example.org/ekga/ns#`.
At least two distinct schemes therefore exist across the released and unreleased
lines, and a downstream tool cannot tell from the documentation which one a given
artifact carries. The local post-processor now infers both from prefix bindings
in the input graph, which is a workaround for an undocumented fact rather than a
design choice.

**Unblocks.** Confidence that regeneration and `migrate-iris` cover the same set
of source schemes, and removal of the inference logic once the set is published.

### UR3. Specify the reference resolution algorithm for object-valued properties

**Request.** For `affects`, `constrains`, `verifiedBy`, and any successor
property, state the exact procedure that turns an authored token into an IRI.
Cover at minimum: whether the operation is string concatenation onto the base or
relative IRI resolution against it; the treatment of dot-bearing identifiers
such as `R2.1`; whether a prefixed token such as `SBL:D14` is legal in these
fields; and if prefixed tokens are legal, where the prefix-to-base mapping is
declared and how it is resolved.

**Observation.** The release description states that these properties will emit
as IRIs resolved against the specification base, and that non-resolving
references produce a parser warning. It does not define resolution. Under
relative IRI resolution against a slash-terminated base, a dotted segment
behaves differently from concatenation; under a hash-terminated base the two
converge. This interacts directly with UR1.

**Unblocks.** Whether the 11 existing `affects` and `constrains` values survive
migration untouched, which is currently asserted rather than derivable. It also
determines whether cross-specification references can be expressed in these
fields at all, which the layering feature depends on.

### UR4. Specify the `title:` fallback derivation

**Request.** Publish the exact derivation used when `title:` is absent:
sentence-boundary rule, length limit, truncation and ellipsis behavior, and
trailing punctuation handling. State whether the derived title is materialized
into the emitted Turtle or computed at validation time and left out of the
graph.

**Observation.** The consuming repository's post-processor derives titles by
splitting on the first sentence boundary and truncating at 80 characters with an
ellipsis. The graph currently carries those derived literals. If 0.3.0 derives
differently, migration produces title diffs that are indistinguishable from
authored content changes.

**Unblocks.** Whether the migration step needs to author explicit `title:`
values for all ten decision records in advance, or whether the fallback
reproduces the current graph.

### UR5. Provide a graph-level comparison mode for migration verification

**Request.** Ship a way to compare two emitted graphs modulo instance base, so a
migration can be verified as an IRI change with no content change. A
`specl diff --ignore-base` mode or equivalent.

**Observation.** The stated migration path for a project holding its source
markdown is regeneration. Regeneration through a release that also changes
property ranges, adds a title key, and adds a header field produces a graph that
differs in several dimensions at once, with no mechanical way to confirm that
only the intended dimensions moved.

**Unblocks.** Signing off the migration as complete rather than as apparently
complete.

## Group B: required to interpret validation output and plan against it

### UR6. Publish the versioned graph contract the header field refers to

**Request.** Alongside the graph-contract version in the Turtle header, publish
the contract itself as a versioned document: the class list, the property list,
each property's range and whether it is object- or datatype-valued, cardinality
expectations, and a stability tier per term. State the compatibility policy that
governs it, specifically what a version bump within the batching policy may and
may not change.

**Observation.** A version identifier in the header is only actionable against a
document it identifies. The property-range correction in 0.3.0 is precisely the
class of change a contract would have made visible in advance: three properties
were declared as object properties while emitting string literals, and no
published artifact recorded the discrepancy.

**Unblocks.** Downstream consumers reading the graph directly, and the ability
to detect the next range correction before a release rather than during a
migration.

### UR7. Document the status-conditional severity model

**Request.** Publish the mapping from specification `status:` to shape severity:
the enumeration of legal status values, and for each shape, its severity at each
status. State whether the shapes graph is versioned and released with the
vocabulary or independently.

**Observation.** The consuming repository's working notes record that warnings
are production-readiness signals that tighten automatically when status advances
from `draft` to `production`. The current run reports 0 violations and 77
warnings. Which of those 77 become violations at `production` is not derivable
from any published artifact, so the remaining work to reach that status cannot
be scoped.

**Unblocks.** Sequencing the specification's advance to `production` against the
milestone plan, rather than discovering the gate contents by flipping the value.

### UR8. Provide a means to mark a shape expectation as not applicable

**Request.** Provide a per-specification or per-item way to declare a shape
expectation inapplicable, with a recorded reason, so that a suppressed
expectation is visible as a decision rather than as a persistent warning. Failing
that, state the intended reading of a warning that no authoring action can clear.

**Observation.** Of 77 current warnings, 21 request `verifiedBy` targets that
have no representable target until the acceptance query class arrives, and 21
request `constrains` targets in a specification that declares no components.
Roughly half the warning volume is therefore structurally unclearable at the
current release, which erodes the value of the count as a signal and encourages
consumers to stop reading it.

**Unblocks.** Treating the warning count as a tracked metric.

### UR9. Warn on unrecognized sections, and provide an explicit non-normative marker

**Request.** Emit a warning, and fail under `--strict`, when a top-level section
is not recognized by the parser. Separately, provide a marker that declares a
section intentionally non-normative prose, so that a document can carry
commentary without tripping the warning.

**Observation.** The parser currently drops unrecognized sections silently. The
practical effect downstream is a standing instruction not to experiment with
document structure, because a mistake is indistinguishable from success. This is
the single behavior most limiting a consumer's ability to adopt new sections
incrementally as releases add them.

**Unblocks.** Adopting new item classes on arrival by trying them, instead of
waiting for confirmation that the section name is correct.

## Group C: required to author forward-compatibly ahead of a class arriving

### UR10. Publish the intended pre-adoption path for each planned item class

**Request.** For each class scheduled in a later release, publish, at the time
the release is planned rather than when it ships: the section name, the
identifier prefix, the property names, and the shape that prose written today
should take so that adoption is a mechanical lift. State explicitly where the
correct action is to write nothing.

**Observation.** The consuming repository maintains its acceptance query set as
prose in a separate file under a standing instruction not to restructure it
until the acceptance query class arrives. That set is described in the project's
own materials as its gating artifact, and it already uses the `Q` identifiers
that the class will adopt. Whether the prose is currently shaped so that
adoption is mechanical is unknown to the consumer, because the class is
described by name and property only.

**Unblocks.** Whether the requirement-to-query mapping now recorded in prose
("gates R8", "gates R2.1 and R2.4") should be restructured in place now.

### UR11. Publish the reserved identifier prefix registry and the identifier grammar

**Request.** Publish the set of identifier prefixes specl reserves, including
those reserved for planned classes, and the legal identifier grammar: permitted
characters, sub-item notation, case sensitivity, and whether zero-padded and
unpadded ordinals are distinct identifiers. State whether the prefix set is
closed or whether a project may declare additional prefixes.

**Observation.** The consuming repository's records list `R`, `D`, `OQ`, and
`US` as its item prefixes, with `US` currently unused, and the planned
acceptance query class introduces `Q`. A consumer that mints a local prefix
today has no way to know whether a future release will claim it.

**Unblocks.** Safe use of local item prefixes, and confidence that existing `Q`
identifiers carry over rather than collide.

### UR12. Specify supersession semantics, not only the vocabulary

**Request.** For the supersession feature, state: whether a superseded or
withdrawn item is still emitted into the graph; whether shapes continue to
evaluate it and therefore continue to accumulate warnings against it; whether
`supersededBy` requires the successor to exist and be of the same class; and
whether a withdrawn item's identifier remains reserved against reuse.

**Observation.** The consuming repository enforces an append-only identifier
rule that is currently prose advice with no mechanism, and it has an open
question whose resolution may strike four requirements outright. Striking one by
deletion would violate the rule, so the resolution path depends on what
withdrawal does to the graph and to the validation report.

**Unblocks.** Resolving that open question by expressing the outcome rather than
by deferring it until the mechanism exists.

## Group D: required for cross-specification work

### UR13. Specify how the layering check resolves the specification it points at

**Request.** For the layering feature, state what the upstream declaration
identifies: a base IRI, a file path, a published graph location, or a registry
entry. State how the validator obtains the other specification's graph, and
confirm that the check operates against a local file or a committed lock
artifact with no network access required.

**Observation.** The consuming project is required to operate its own core
functions with no network egress, and the layering check is described as the
release that matters most for its final milestone. A validator that fetches a
peer specification over the network at check time would be unusable in the
environments this project targets, and would also make the check
non-deterministic in CI.

**Unblocks.** Retiring the hand-rolled string-search layering target in favor of
the real subcommand, and relying on it in a restricted environment.

### UR14. State whether specl owns a multi-specification namespace registry concept

**Request.** State plainly whether specl intends to model a registry of
specification namespaces and their bases, or whether that remains a project-level
concern outside the tool. If it remains outside, say so, so consumers can retitle
their local registries as governance records rather than as tool inputs.

**Observation.** The consuming repository maintains a namespace registry file
that no tooling reads, and whose own comments and the post-processor's docstring
both describe it as driving the namespace rebase. The base is in fact supplied by
a build variable. Moving `spec_base` and `prefix` into front matter makes that
file's role less clear rather than more, since the values it records will then be
authored elsewhere.

**Unblocks.** Whether that file becomes a tool input, is retitled, or is deleted
at migration.

### UR15. Specify how cross-specification references are written and validated

**Request.** State how an item in one specification references an item in
another once bases are project-supplied: the authored syntax, where the foreign
prefix is declared, whether such references are resolved and validated or
recorded opaquely, and what a reference to an unresolvable foreign specification
produces.

**Observation.** The layering relationship between this specification and its
downstream consumer is the reason the consuming project enforces a direction
rule at all, and the rule is currently enforced by grepping for a hardcoded
prefix string. A prefix-based grep is also the mechanism the project would keep
if no specified alternative exists.

**Unblocks.** Expressing the direction rule as a graph constraint rather than as
a text search, which is the stated goal of the layering feature.

## Group E: release process

### UR16. State, per release, which downstream workarounds it obsoletes and the condition for removing them

**Request.** In each release's notes, name the downstream compensations the
release makes unnecessary, and state the observable condition under which a
consumer should delete each one.

**Observation.** The consuming repository carries a post-processing tool whose
deletion condition is recorded in prose in its own docstring and repeated in two
other files. That condition is a guess about upstream behavior maintained
downstream. Stating it upstream moves it to the party that knows it.

**Unblocks.** Deleting compensating tooling on a defined trigger instead of on
inspection.

### UR17. Publish the shapes graph and vocabulary as versioned, fetchable artifacts

**Request.** Publish the shapes graph and the vocabulary at stable versioned
locations, independent of the installed package, and state their version
relationship to the tool version.

**Observation.** The consuming repository's build locates the shapes graph by
introspecting the installed package's file path. A consumer that wants to
validate against a specific contract version, or to review what changed in a
shape between releases, has no artifact to point at.

**Unblocks.** Pinning validation to a contract version, and reviewing shape
changes as part of upgrade planning.

## Priority

UR1, UR2, UR3, and UR4 gate the migration itself and are requested before 0.3.0
ships. UR7 and UR9 gate the ability to plan and to experiment, and are requested
early irrespective of which release carries them. The remainder are requested
alongside the release that introduces the feature each concerns.
