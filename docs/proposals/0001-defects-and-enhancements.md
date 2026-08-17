# Proposed modifications to specl

Revised against the repository at `main` (30 files, no test directory). Supersedes
the earlier draft, which was written against the PyPI 0.2.0 distribution.

Reading the repo changed three things. The `ekga:` rename is already done and the
question about it has a more specific answer than expected. The maturity gap is
larger than a missing feature. And one defect proved worse in `main` than in the
published release rather than better.

## Repository state

The source carries the 0.3.0 namespace work, but `pyproject.toml` and
`__init__.py` both declare `0.2.0`, the CHANGELOG describes 0.3.0 as shipped, and
`NAMESPACE-MIGRATION.md` is referenced by the CHANGELOG but is not in the tree.
Worth reconciling before the next release, since the CHANGELOG is currently a
promise the package metadata does not keep.

There is no test directory. That matters for a specific reason developed under P2.

## Summary

| ID   | Item                                                              | Severity   |
| ---- | ----------------------------------------------------------------- | ---------- |
| P1   | Object properties emitted as string literals                        | Critical   |
| P2   | Decision records cannot satisfy their own shape                     | Critical   |
| P3   | One global instance namespace; specs collide permanently            | Critical   |
| P4   | Maturity and progress are computed and discarded, never modeled     | High       |
| P5   | No cross-specification references or layering                       | High       |
| P6   | No supersession relation despite a superseded status                | High       |
| P7   | Section vocabulary closed; unknown sections silently dropped        | High       |
| P8   | Content-hash IRIs for unnumbered sections                           | Medium     |
| P9   | `prov:` declared and never used                                     | Medium     |
| P10  | Front-matter parsed ad hoc rather than as YAML                      | Medium     |
| P11  | `status` maps to three properties implicitly                        | Medium     |
| P12  | `diff` writes a changelog as an unrequested side effect             | Low        |
| P13  | `score` divides by requirements but counts all focus nodes          | Low        |
| P14  | No tests                                                            | Structural |
| P16  | Bullet grammar narrower than the published identifier grammar       | High       |

## On the namespace question

Two separate questions hide behind this, and they have different answers. One is
whether vocabulary and instances should use different prefixes. The other is who
owns the IRIs those prefixes expand to.

**Prefixes: the split the rename produced is right and should stay.** A
vocabulary term (`specl:Requirement`) and an instance of it (`spec:R1`) are
different kinds of thing with different lifecycles. The vocabulary is versioned,
published, and shared by every user of the tool; instances belong to one project
and change constantly. Collapsing both into one prefix makes a project's items
compete for local names with the language's terms, and `spec:Requirement` becomes
ambiguous between the class and an item someone happened to name Requirement.

So `spec:` remains the correct prefix label for instances, and `specl:` for the
vocabulary. Nothing below changes that.

**Bases: the instance base is wrong and belongs to the consumer.** What the
rename got wrong is the IRI each prefix expands to:

```
current                                      target
specl: -> https://w3id.org/specl/ns#         unchanged
spec:  -> https://w3id.org/specl/spec#       supplied by the project, required
```

The vocabulary base is specl's to own, because the vocabulary is specl's
artifact. The instance base is not, because a user's requirements are the user's
data. P3 below is that change; the prefix label `spec:` survives it and binds to
whatever base the project declares.

## P3. One global instance namespace, and it is now permanent

**Critical.** `SPEC = "https://w3id.org/specl/spec#"` is a single hash namespace
shared by every specification ever authored with specl, by anyone. Every project
mints `https://w3id.org/specl/spec#R1`.

This is demonstrable in this repository. Translating `excel_service` and
`pptx_templater` and merging the results yields 11 shared item IRIs. The node
`spec#R1.1` then carries two descriptions, one about an HTTP POST endpoint and
one about preserving master slides, and is `specl:partOf` both `spec#xlsvc-001`
and `spec#pptxgen-001`. Neither specification is wrong; the namespace conflated
them.

Under `example.org` this was a latent defect. Under w3id.org it is a permanent
identifier commitment, which is exactly the case where a collision cannot be
walked back. A tool whose premise is RDF-native traceability should not mint one
IRI for two unrelated requirements.

**Proposed change.** Keep w3id.org for the vocabulary. Stop minting instance
IRIs under it entirely, and require the project to supply its own base.

```yaml
spec_id: xlsvc-001
prefix: XLSVC
spec_base: https://spec.example.org/xlsvc-001#
```

The principle is ownership. A user's requirements are the user's data, not
specl's. Defaulting them into `w3id.org/specl/spec#` means every specification
ever authored with the tool lives permanently under the tool author's namespace,
with the tool author implicitly responsible for the redirects that make those
IRIs dereference. A vocabulary is a shared artifact and belongs at a permanent
community identifier; instances are not, and do not.

Making `spec_base` mandatory rather than defaulted is the stronger form and the
one worth taking. A default that is wrong for everyone except the person who set
it is how the current collision arose. Fail translation with a clear message
when it is absent, pointing at the syntax documentation. Retire
`https://w3id.org/specl/spec#` rather than partitioning it.

Item IDs stay bare in the markdown; the parser requirement is fine and bare IDs
read better in source. `prefix` gives CURIE references in prose and across
specifications a declared expansion.

The five self-specs in this repository each need a `spec_base` added, which is
also the first real test of the error message.

## P1. Object properties emitted as string literals

**Critical, unchanged in `main`.**

`core.ttl` declares `specl:affects`, `specl:constrains`, and `specl:verifiedBy`
as `owl:ObjectProperty`, two with an `rdfs:range`. `_emit_item` routes every
annotation through one path:

```python
triples.append(f'    specl:{prop} "{esc(v)}"')
```

A decision annotated `affects: R8, R8.1` produces the literals `"R8"` and
`"R8.1"`. The graph contradicts its own ontology, and the traceability questions
the tool exists to answer cannot be resolved by traversal, only by string
matching, which is what the RDF was meant to replace.

**Proposed change.** Partition annotation keys by range:

- **Item references** (`affects`, `constrains`, and `verifiedBy` where the value
  matches an item ID pattern): resolve against the specification namespace and
  emit as IRIs. Accept CURIE form for cross-specification references.
- **External references** (`verifiedBy: tests/test_client.py::test_add_holon`):
  emit as a typed node, `[ a specl:Test ; dct:identifier "tests/..." ]`, so the
  property keeps an object range.
- **Prose keys**: unchanged as literals.

Warn when an item reference resolves to an ID absent from the specification. That
check is the practical payoff: it catches a decision pointing at a renumbered or
deleted requirement, which append-only identifier discipline currently has no
enforcement for.

This also unblocks P4, since evidence-based progress needs `verifiedBy` to be a
real edge.

## P2. Decision records cannot satisfy their own shape

**Critical, unchanged in `main`.** `DecisionRecordShape` requires `dct:title` at
Violation severity. `PROP_MAP` has no key producing `dct:title` and `_emit_item`
emits only `dct:description`. Every markdown-authored decision record fails the
gate unconditionally.

Why this survived two releases is visible in the repository: none of the five
self-specs contains a `# Decisions` section. The tool is dogfooded only on the
paths that work. A user who adopts decision records gets a specification that
cannot pass its own gate no matter how well it is written.

**Proposed change.** Add a `title:` key mapping to `dct:title`, available on all
item classes, and derive a title from the first sentence of the description when
the key is absent. A Violation-severity shape must be satisfiable through the
primary authoring path.

Then add the structural test in P14: assert that every property any shape
requires at Violation severity is emittable by the translator. This class of
defect should be caught by construction rather than found in use.

## P4. Maturity and progress are computed and discarded, never modeled

**High, and the most interesting of these.** `cmd_score` computes a percentage,
`cmd_badge` renders it to SVG, and nothing is retained. Maturity exists as a
transient number and a committed image. It is not in `core.ttl`, not in the
graph, and not queryable.

Three consequences. There is no history, so no trend, so no answer to whether a
specification is converging. There is no breakdown, so a 60% cannot be
attributed. And the metric is narrow in ways the number conceals.

The narrowness is measurable here. `specl_tool` scores 100%, and its census is 16
requirements, 3 user stories, 0 open issues, 0 decisions, 0 design notes. The
score counts only requirements, so a specification declares itself fully mature
while the classes that would record its unresolved questions are empty. A metric
that cannot see open issues cannot distinguish a mature specification from one
that has not yet asked itself anything. `cmd_score` also builds its `bad` set
from all focus nodes while dividing by requirements only, so findings against
other classes silently do not count (P13).

**The conceptual fix is to separate three things the word "maturity" currently
carries.**

| Concept                 | Question it answers                          | Source of truth               |
| ----------------------- | -------------------------------------------- | ----------------------------- |
| Specification maturity  | How completely is this specified?             | SHACL findings per item        |
| Implementation progress | How much of it is built?                      | Per-item declaration           |
| Verification coverage   | How much is demonstrated rather than claimed? | Verification artifact results  |

Only the first exists, and it is named ambiguously enough to be read as either of
the others.

**Proposed changes.**

*Model assessments as data.* Add `specl:MaturityAssessment` as a `prov:Activity`
recording `prov:generatedAtTime`, the specification assessed, the overall score,
and per-class subscores. Have `specl-validate score` append the assessment to a
history graph rather than only printing it. Maturity then becomes queryable and
diffable, the badge becomes a rendering of the latest record rather than the only
artifact, and trend over time is a SPARQL query rather than something nobody has.

*Add per-item implementation status.* `specl:implementationStatus` with a
vocabulary of `not-started`, `in-progress`, `implemented`, `verified`, exposed as
an `implementation:` annotation key. This is distinct from `priority`
(importance) and from lifecycle status (P6). Progress rolls up from items rather
than being declared for the whole specification, which is what makes it honest.

*Weight by priority.* Already deferred in the CHANGELOG. A clean MUST and a clean
COULD should not contribute equally, and an unclean MUST should cost more than an
unclean WONT.

*Score all item classes.* Either extend the denominator or state in the output
that the metric covers requirements only. The current combination of a complete
numerator and a partial denominator is the worst of both.

*Optionally, derive verification coverage from evidence.* Once `verifiedBy` is a
real edge (P1), ingesting test results turns coverage into an observed fact
rather than a self-report. This is the ambitious version and can follow.

The general principle: a tool that produces an RDF graph should record its own
assessments in that graph. Computing a number about the specification and
discarding it is the one place specl steps outside its own model.

## P5. No cross-specification references or layering

**High.** Once one specification is upstream of another, three things are needed
and none exist: a way to reference an item in another specification, a
declaration of the relationship, and a check that it holds.

The concrete case from current use is a substrate specification upstream of an
application specification, where the application may cite the substrate and the
substrate must never cite the application. That is presently enforced by a grep
in a Makefile.

**Proposed change.** Add `specl:dependsOn`, `specl:upstreamOf`, and
`specl:refines` between specifications, declarable in front matter. Accept CURIE
item references resolved through a declared prefix map. Add a
`specl-validate layering` subcommand that fails when a specification references
an item in a specification declared downstream of it.

Depends on P3, since cross-specification references are meaningless while all
specifications share one namespace.

## P6. No supersession relation despite a superseded status

**High.** `decisionStatus` accepts `superseded` with nothing recording what
superseded the decision. Requirements have no status property at all, so retiring
one requires deleting it, which breaks append-only identifier discipline.

**Proposed change.** Add `specl:supersededBy` (item to item) with a
`supersededBy:` key, and `specl:itemStatus` on requirements with `active`,
`superseded`, `withdrawn`. Add a Warning-severity shape requiring `supersededBy`
when status is `superseded`.

## P7. Section vocabulary closed; unknown sections silently dropped

**High.** `SECTION_MAP` is a fixed list of literal English headings, and `emit`
iterates only known sections, so an "Acceptance Queries", "Verification", or
"Glossary" section is dropped with no warning. Silent content loss is the serious
part.

**Proposed change.** Warn on any H1 not in the map. Allow the map to be extended
from front matter. Add `specl:AcceptanceQuery` (prefix `Q`) to the core
vocabulary with a `specl:gates` property linking a query to the requirements it
verifies. A query set is a recurring artifact and arguably the only part of a
specification that can falsify the rest, which earns it a class.

Whether `SECTION_MAP` and `PROP_MAP` were intended as extension points changes
how this is framed. Nothing in the repository suggests they were, so it reads as
a defect rather than an unfinished feature.

## P8 through P14

**P8. Content-hash IRIs.** Design notes and comments are minted as
`spec:{class}-{sha1(text)[:8]}`, so editing wording changes the IRI, breaks
inbound references, and appears in `diff` as a removal plus an addition. Require
IDs for these sections as everywhere else.

**P9. `prov:` declared and never used.** `HEADER` binds the prefix and no code
path emits a `prov:` triple. Either emit source provenance per item
(`prov:wasDerivedFrom` the source document with a line number,
`prov:generatedAtTime` on the graph) or drop the dead prefix. P4 needs
`prov:Activity` regardless, and multi-file specs make per-item source provenance
necessary rather than decorative.

**P10. Front matter is not YAML.** The `[]` handling implies list parsing that
does not happen. Parse with a YAML library or document the restricted grammar
honestly. Given `pyshacl` is already a dependency, YAML is not a meaningful
addition.

*Correction, made while onboarding.* The cause given in the original text was
wrong. `line.split(":", 1)` does not break on values containing colons;
`title: specl: a spec language` parses as intended. What breaks is nesting.
Every line carrying a colon is assigned into one flat dict regardless of
indentation, so the committed 0.5.0 front matter

```yaml
references:
  SBL:
    base: https://spec.example.org/sibyl#
```

parses to `references` and `SBL` as empty strings and a top-level `base`, which
collides with any other nested `base`. The consequence is a sequencing change:
P10 blocks 0.5.0 rather than riding along in 0.10.0 ergonomics.

**P11. `status` polymorphism is undocumented.** It becomes `decisionStatus` on
decisions and `resolutionStatus` elsewhere, while `specl:status` on the
Specification is a third property with a third vocabulary. Document it in
`SYNTAX.md` or split the keys.

**P12. `diff` side effect.** `cmd_diff` appends to `CHANGELOG.spec.md` in the
working directory on every invocation, including read-only inspection, and
duplicates entries when run twice. Gate behind `--changelog PATH`.

**P13. `score` denominator.** Covered under P4.

**P14. No tests.** P2 is exactly what one test would have caught. A minimal
suite: fixture specification to expected Turtle; the shapes-versus-translator
coverage assertion; a fixture per parser-warning path; and an idempotence check.
Include a fixture exercising every section type, so the dogfooding gap that hid
P2 cannot recur.

## Suggested sequencing

**0.3.0, amended before release, correctness and identity.** P1, P2, P3, P14. These make output either wrong or
unusable across projects. P3 belongs here rather than later specifically because
w3id.org makes the current IRIs permanent, so every day of delay adds
specifications that will need migrating. P14 lands alongside P1 because P1
changes emitted triples and a fixture comparison is the only cheap way to confirm
nothing else moved.

**Then, multi-specification.** P5, P6, P7. What a layered or federated
project actually needs, and P5 depends on P3.

**Then, measurement.** P4 in full, plus P9. The assessment model wants
`prov:` present and wants `verifiedBy` to be a real edge, so it reads better
after the first two releases than before them.

P8, P10, P11, P12 are independent and can ride along with any of the three.

## Addendum: two items found after this analysis

**P15, closed.** `README.md` referenced a file that did not exist in the tree.
Found by `tools/check_docs.py`. The sentence now points at `docs/ROADMAP.md`,
which covers the same deferred material.

**P16, open, scheduled for 0.3.0.** `BULLET_RE` implements a narrower identifier
grammar than the one published in `docs/DOWNSTREAM-COMMITMENTS.md`. The grammar
admits zero or more dot-separated digit groups; the regex accepts one. `R1.2.3`,
`US1.2`, and `D1.1` are legal to a consumer reading the commitments register and
are dropped by the translator with no warning under `--strict`. The reserved
prefixes `DN`, `C`, and `Q` have no bulleted path.

This is the P1 and P2 shape once more. An artifact asserts something the code
does not do, and the artifact in question is the one a downstream consumer was
told to author against.

**Evidence for P7 and P4 in this repository.** `specs/specl_tool/spec.md` heads
its open questions `# Open Questions and Gaps`, which is not in `SECTION_MAP`.
The section is dropped with no warning, so the specification emits zero
`specl:OpenIssue` nodes and scores 100% maturity while carrying three unresolved
questions. The silent-drop defect and the narrow metric compound: the classes
that would lower the score are the ones being discarded.

**P17, open, scheduled for 0.3.0.** A specification that does not supply
`created` gets today's date stamped into `dct:created` on every emission. Exit
criterion 6 for 0.3.0, byte-identical output on repeated translation, therefore
holds within a day and fails across one, and no golden file can be committed
without normalizing the field. The value is also wrong on its face: it records
when the translator ran, not when the specification was created. Emit the
property only when the specification supplies it. Removing a triple is a graph
change, which is why it belongs in a designated breaking release rather than in
a patch.

**Not a defect: `--strict` does not fail.** Written down because it looks like
one and was briefly treated as one while the test suite was being built. R1.5 in
`specs/specl_tool/spec.md` specifies that the flag prints parser warnings to
stderr and exits 0, with an acceptance criterion naming the exit code. The
behavior is correct and the self-specification is the authority.

What follows from it is a real gap. Nothing in the pipeline gates on a parser
warning: CI translates with `--strict`, prints them, and continues. P16 adds a warning for a bullet that
looks like an item and does not parse, and a warning nothing gates on is only
marginally better than the silence it replaces. Whether a separate gating flag
should exist is a question for 0.3.0, not a change to `--strict`.

**P18, closed in 0.3.0.** The deferral reasoning below was wrong: the fix is
additive rather than breaking, and the real obstacle was telling nested content
from a mistyped annotation. See `docs/decisions/0005-nested-content-under-items.md`.
`R6.2` is restored to its nested form and the discarded lines now reach the
graph.

**P18, as originally recorded.** An indented bullet under an item is always read as
an annotation, so the format cannot express a nested content list. `R6.2` in
`specl_explorer` used one to enumerate field ordering per type, and all four
lines were parsed as failed annotations and discarded: the requirement reached
the graph as a description ending in a colon. Folding the content into the
description recovered it, which is the right authoring fix today, but the gap is
real and the warning is the only thing that surfaces it. Supporting nested
content is a format change and belongs in a designated breaking release if it is
wanted at all.

**P19, open, scheduled for 0.11.0.** The user story properties are named after
the sentence template rather than after what they mean. `specl:asA`,
`specl:iWant`, and `specl:soThat` denote a role, a capability, and a benefit,
and a local name that is a pronoun with a verb describes the authoring form
instead of the resource. All three predate this review round; the gap that
surfaced them was that `iWant` had no annotation key at all, so a user story
could carry the first and third clauses of its own sentence and not the second.
Wiring the key was additive and is done. Renaming is an IRI change, and turning
the role into a reference to a persona is also a range change, so both wait for
the designated break.
