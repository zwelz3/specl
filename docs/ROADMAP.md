# specl release roadmap

Covers the 0.x train through 0.11 and the conditions for eventually declaring
1.0. Ordered by dependency, not by date. Each release states its theme, what
lands, what deliberately does not, whether it breaks the graph contract, and
testable exit criteria.

Item identifiers (P1 through P14) refer to `docs/proposals/0001-defects-and-enhancements.md`.

## Versioning, and the two compatibility surfaces

specl has two contracts, and they are not the same thing.

The **API contract** covers the CLI subcommands, the Python entry points, and
the markdown syntax. Pre-1.0, breaking it in a minor release is normal and
cheap: a user changes a command or a front-matter key.

The **graph contract** covers the IRIs specl mints and the triples it emits.
This one is different in kind. IRIs are meant to be permanent, downstream
consumers dereference and store them, and cross-specification references embed
them. A graph-contract break is a data migration for every user, not a code
change.

Staying pre-1.0 for an extended train is the right call, because 1.0 should mean
the graph contract is frozen and it is not close to that. But a long 0.x train
introduces a hazard a short one does not. If graph breaks dribble across many
minor releases, "pre-1.0" stops meaning "unstable, breaks are expected" and
starts meaning "migrate every release." That is the failure mode to design
against.

**Policy: batch graph-contract breaks into designated releases.** In this plan
0.3.0 and 0.11.0 are the only releases permitted to change emitted IRIs or change
a property's range. Everything between them is additive to the graph. If a break
becomes necessary mid-train it waits for the next designated release rather than
shipping when it is ready.

Alongside this, emit a graph-contract version in the Turtle output so a consumer
can ask what it is holding, and state in the README that only designated releases
change it.

## Handling the unreleased 0.3.0

0.3.0 exists in the CHANGELOG but never reached PyPI, which still carries 0.2.0.
Its headline feature is the move to permanent w3id.org identifiers, and that is
the change P3 identifies as wrong.

**The 0.3.0 entry is amended in place and shipped corrected**, rather than
withdrawn in favor of a new number. Nothing external depends on it, so there is
no version to break.

One consequence worth stating explicitly, because it goes beyond a correction.
The amended 0.3.0 also absorbs P1, P2, P13, and P14. The reason is the batching
policy above: P3 and P1 are both graph-breaking, and splitting them across 0.3.0
and 0.4.0 would force two migrations on every user for no benefit. Amending the
namespace alone and deferring the rest would leave the first release under a
permanent-identifier scheme still emitting object properties as literals.

The CHANGELOG entry therefore grows rather than merely being corrected. If that
is unwelcome, the alternative is to designate 0.3.0 and 0.4.0 as a breaking pair
shipped close together with one migration tool covering both, which is messier to
explain but keeps the original entry closer to what it said.

## The train at a glance

| Release | Theme                                  | Graph contract |
| ------- | -------------------------------------- | -------------- |
| 0.3.0   | Identity and correct emission          | **Breaking**   |
| 0.4.0   | Item lifecycle and supersession        | Additive       |
| 0.5.0   | Cross-specification references         | Additive       |
| 0.6.0   | Open sections and acceptance queries   | Additive       |
| 0.7.0   | Provenance                             | Additive       |
| 0.8.0   | Maturity and progress as data          | Additive       |
| 0.9.0   | Multi-file specifications              | Additive       |
| 0.10.0  | Ergonomics and the assistant           | Additive       |
| 0.11.0  | Identifier cleanup and contract freeze | **Breaking**   |
| 1.0.0   | Freeze                                 | Frozen         |

## 0.3.0 — Identity and correct emission

Deliberately the largest release in the train, because it is one of only two
permitted to break the graph and everything graph-breaking should travel
together.

**Lands**

- **P3, project-owned instance IRIs.** The vocabulary stays at
  `https://w3id.org/specl/ns#`. specl stops minting instance IRIs under its own
  domain entirely; `https://w3id.org/specl/spec#` is retired rather than
  partitioned. `spec_base` becomes mandatory front matter, and translation fails
  with a clear message pointing at the syntax documentation when it is absent.
  A `prefix` key gives CURIE references a declared expansion. The five self-specs
  each gain a `spec_base`, which is the first real test of the error message.
- **P1, object properties emitted as IRIs.** `affects`, `constrains`, and
  `verifiedBy` resolve item references against the specification base and emit as
  links. External verification references emit as a typed node so the property
  keeps an object range. Dangling references produce a parser warning.
- **P2, done.** `title:` is a recognized annotation on every item class and
  maps to `dct:title`. When absent the committed fallback derives one and
  materializes it. A specification carrying a `# Decisions` section passes the
  gate for the first time, and the shapes-coverage assertion turned green.
  Original entry:
- **P2, decision titles.** A `title:` annotation key on all item classes, with a
  fallback derived from the first sentence of the description.
- **P14, test suite.** Golden-file fixtures, a fixture exercising every section
  type including `# Decisions`, one fixture per parser-warning path, an
  idempotence check, and the shapes-versus-translator coverage assertion. It
  covers `tools/` as well as `src/`: both holes later found in
  `tools/check_docs.py` existed because nothing tested the checker.
- **P13, done.** The population is every item class rather than requirements
  only, so a finding against a decision or an open issue now counts instead of
  matching nothing and being discarded. A specification whose gate fails
  reports no percentage at all and its badge reads "failing", because a
  maturity number for a specification that does not validate describes
  nothing. The two published badges moved from 100% and 0% to 76% and 8%.
  Original entry:
- **P13, score denominator.** The bug half of P4. Correcting the arithmetic
  alone is not enough, because the two disagreements it produces both survive
  it: a specification with a Violation currently scores 100% and renders a
  brightgreen badge while the gate fails it, and the all-or-nothing per
  requirement rule reads 0% for `specl_explorer`, which passes the gate across
  47 requirements.
  0.3.0 makes score and gate agree in sign, by scoring every item class rather
  than requirements only and by refusing to report a clean number for a
  specification the gate fails. Weighting, subscores, and assessment history
  stay in 0.8.0.
- **P17, done.** `dct:created` is emitted only when the specification supplies
  it. Output is byte-stable across days and the golden comparison runs against
  unmodified output. Original entry:
- **P17, translation-time date stamping.** A specification that does not supply
  `created` gets today's date in `dct:created`, so output is not byte-stable
  across days and the value records when the translator ran rather than
  anything about the specification. Emit it only when supplied. Removing a
  triple is why this waits for a designated break.
- **Open question, gating on parser warnings.** `--strict` prints and exits 0,
  which R1.5 specifies and which is correct. Nothing else gates either. The surface is
  small: four parser warnings across both published specifications, all one
  class, all prose inside a bulleted list that looks like a sub-bullet. Either a separate flag fails on warnings or the exit criterion for P16
  is weaker than it reads.
- **P16, done.** The grammar published in the commitments register is
  implemented: any uppercase prefix, any number of dot-separated digit groups.
  A top-level bullet that looks like an item and does not parse now warns
  instead of vanishing, and mixing padded with unpadded ordinals under one
  prefix warns without merging. Adding the missing `Open Questions and Gaps`
  alias surfaced ten open questions across both published specifications that
  had never reached the graph; they now carry `OQ` identifiers. Original entry:
- **P16, the published identifier grammar.** `BULLET_RE` accepts `R1.1` but
  rejects `R1.2.3`, `US1.2`, and `D1.1`, all legal under the grammar published
  in `docs/DOWNSTREAM-COMMITMENTS.md`, and drops them without a warning even
  under `--strict`. Implement the committed grammar, warn on a bullet that
  looks like an item and does not parse, and reserve `DN`, `C`, and `Q` as
  committed. This is conformance to an answer a consumer authored against, not
  a feature.
- **Graph-contract version** emitted in the Turtle header.
- **Repository reconciliation.** Align `pyproject.toml`, `__init__.py`, and the
  CHANGELOG. Write the referenced `NAMESPACE-MIGRATION.md`, which now documents a
  different migration than originally planned.

**Not in scope:** cross-specification references, the maturity model, new item
classes, multi-file specs.

**Breaking.** Every item IRI changes, and `spec_base` becomes required, so every
existing spec needs a front-matter addition before it will translate at all.
`affects`, `constrains`, and `verifiedBy` change from literals to IRIs.

**Migration.** Ship `specl-migrate iris <old.ttl> <new.ttl> --spec-base <iri>`
rewriting the old flat namespace into the project base and converting the three
properties. Because the old namespace conflated specifications, the tool refuses
to run on a merged graph containing more than one `specl:Specification`.
Regenerating from markdown is the better path where the markdown exists; the tool
serves consumers holding only Turtle.

Requiring `spec_base` rather than defaulting it is a deliberate friction. A
default that is right only for the person who chose it is how the current
collision arose.

**Exit criteria**

1. Translating any two repository specs and merging yields zero shared item IRIs.
2. Translating a spec with no `spec_base` fails with an actionable message rather
   than silently minting under a shared namespace.
3. A fixture spec with a `# Decisions` section validates with zero violations.
4. For a decision annotated `affects: R8`, a SPARQL traversal reaches the
   requirement node.
5. Every property required at Violation severity by any shape is produced by the
   translator, asserted by test.
6. Translating twice produces byte-identical output.
7. Every identifier legal under the published grammar translates, and a bullet
   that looks like an item and does not parse produces a warning rather than
   silence.
8. No specification reports a maturity percentage that contradicts its gate
   result.
9. *Moved.* The w3id pull request no longer gates this release. Under
   `docs/decisions/0007-internal-releases-until-1.0.md` a release is tagged
   rather than published, no installed copy of 0.3.0 will exist, and an IRI is
   an identifier whether or not it resolves. What the redirects gate is the
   downstream embargo, where documents citing those IRIs start appearing
   outside this repository.

Criteria 1 through 8 are asserted in `tests/test_exit_criteria.py`, so whether
0.3.0 is tagged is answerable by running the suite rather than by reading this
list and trusting it. They pass.

Throughout this document, shipping a release means tagging it in this
repository. Publication to PyPI happens once, at 1.0.

## 0.4.0 — Item lifecycle and supersession

Small and additive. First among the additive releases because it makes
append-only identifier discipline expressible rather than merely advised, and
every later release accumulates items that may need retiring.

**Lands, done.** P6: `specl:supersededBy` between items, `specl:itemStatus` with
`active`, `superseded`, `withdrawn`, both annotation keys, and a
Warning-severity shape requiring `supersededBy` when the status is `superseded`.

The committed semantics in `docs/DOWNSTREAM-COMMITMENTS.md` are implemented in
full, which is more than the roadmap entry above describes: a retired item is
no longer evaluated by the shapes, a successor must be the same class and in the
same specification, `withdrawn` must not name one, and reuse of a withdrawn
identifier fails `diff`.

Two further details settled in implementation. `supersededBy` routes through
reference resolution rather than carrying a literal, so a supersession pointing at an
undeclared identifier warns for the same reason a decision pointing at a
renumbered requirement does. And both properties apply to every item class
rather than to requirements only; a decision record already accepted
`superseded` as a status with nothing recording what replaced it, which is where
P6 started.

**Exit criteria.** A requirement can be retired in place with its replacement
linked, its identifier is never reused, and a query returns the supersession
chain for any retired item.

## 0.5.0 — Cross-specification references and layering

**Lands, done.** P5: `specl:dependsOn`, `specl:upstreamOf`, and `specl:refines`
between specifications, declarable in front matter. CURIE item references resolved
through a declared prefix map. A `specl-validate layering` subcommand failing
when a specification references an item in a specification declared downstream of
it.

Also landed P10, real YAML front matter, moved here from 0.10.0. The parser is
now `yaml.safe_load`, so the committed two-level mapping round-trips and invalid
YAML is rejected rather than half-parsed.

Original entry: Also lands P10, real YAML front matter, moved here from 0.10.0. The committed
`references:` syntax is a two-level mapping, and the current parser flattens
nested mappings into one dict, so `references:` and the prefix key parse to
empty strings and the inner `base` key collides at top level. The feature cannot
be implemented as specified against the existing parser.

Depends on 0.3.0. Cross-specification references are meaningless while all
specifications share one namespace, and are straightforward once each owns its
own base.

**Exit criteria.** Front matter round-trips a two-level `references:` mapping
without flattening or key collision. Two specifications with a declared upstream
relationship
translate, merge without collision, and support traversal from a downstream item
to the upstream item it references. `layering` fails on a deliberately inverted
reference and passes on a correct one.

## 0.6.0 — Open sections and acceptance queries

Also closed UR17, which no release had scheduled. The shapes graph had no
ontology header, so there was nothing to attach a version to; the commitment was
unsatisfiable rather than unmet. Versioning is by graph contract, following UR6,
which makes the contract the identity of the vocabulary and shapes pair. Two
published copies of each across the run to 1.0, rather than one per release.

**Lands, done.** P7: an H1 the map does not know warns and names itself, the map
extends from a `sections:` front-matter mapping onto classes the vocabulary
already declares, and `specl:AcceptanceQuery` with `specl:gates` links a query to
the requirements it verifies.

The parked marker committed under UR10 is `<!--specl: parked-->` beneath the
heading, detected against the raw source. It has to be: the document-level
`<!--specl ... -->` block would otherwise consume it, and one marker namespace is
better than two.

A query set is a recurring artifact and arguably the only part of a specification
that can falsify the rest, which earns it a class rather than a plain-markdown
home outside the graph.

**Exit criteria.** An unrecognized H1 warns under `--strict` rather than silently
dropping content. A query linked by `gates` to a requirement is reachable from
that requirement by traversal.

## 0.7.0 — Provenance

**Lands, done.** P9: `prov:wasDerivedFrom` per item pointing at the source
document with a line number, and `prov:generatedAtTime` on a translation
activity. Removes the dead `prov:` prefix by using it.

One deviation, recorded rather than quietly made. The timestamp is supplied with
`--generated-at` rather than read from the clock. Exit criterion 6 for 0.3.0 is
that the same source produces byte-identical output, and a translator that reads
the clock breaks it and every golden file. Recording when a graph was produced is
a deliberate act by the caller. The same constraint governs any future
fingerprint of code or environment: translation stays a pure function of its
source, and anything else belongs to a separate command.

Placed before both the assessment model and multi-file specs because both need
it. Assessments are provenance-bearing activities, and per-item source provenance
stops being decorative the moment items come from several files.

**Exit criteria.** Every emitted item carries a resolvable source reference, and
a query answers which source line produced a given triple.

## 0.8.0 — Maturity and progress as data

The release that moves measurement out of a transient number and into the graph.
**Done.** All four exit criteria are asserted in `tests/test_assessment.py`.

**Lands**

- `specl:MaturityAssessment` as a `prov:Activity` carrying
  `prov:generatedAtTime`, the specification assessed, the overall score, and
  per-class subscores. `specl-validate score` appends to a history graph rather
  than only printing. The badge becomes a rendering of the latest assessment.
- `specl:implementationStatus` per item with `not-started`, `in-progress`,
  `implemented`, `verified`, exposed as an `implementation:` annotation key,
  rolling up rather than being declared for the whole specification.
- Priority-weighted scoring, deferred since 0.2.0.

**Not in scope:** verification coverage derived from ingested test results. Worth
doing separately, since it introduces a dependency on test-runner output formats.

Placed here rather than earlier so the scoring model is designed against the full
item vocabulary. Building it before acceptance queries, supersession, and
cross-specification references exist would freeze a metric around the classes
that happen to exist today, which is precisely how the current requirements-only
score came about.

**Exit criteria**

1. Three successive assessments of a changing specification produce a history
   graph from which a query returns the trend.
2. A specification with unresolved open issues cannot score 100%.
3. Marking a requirement `implemented` changes progress and does not change
   maturity, demonstrating the two are separable.
4. Two specifications with identical finding counts but different priority
   distributions score differently.

## 0.9.0 — Multi-file specifications

**Lands, done.** The `companion_files` front-matter key, deferred twice. Depends
on 0.7.0 for per-item source provenance, and the dependency was real: without it,
splitting a specification loses the answer to which file an item came from.

The exit criterion is stated precisely in the tests, because as written it was
self-contradicting. A split specification cannot translate to *the same* graph as
the single file while every item's provenance identifies the correct source, so
the assertion is graph isomorphism modulo provenance, plus per-file source
identity.

0.7.0's choice of source identity had to change here, as flagged when it was
made: the basename collides once one specification holds several files. Identity
is now the path relative to the root.

**Exit criteria.** A specification split across three files translates to the
same graph as the equivalent single file, and every item's provenance identifies
the correct source file.

## 0.10.0 — Ergonomics and the assistant

Independent improvements, none of which blocks anything.

**Done.**

- P11, `status` polymorphism documented. Four unrelated properties share the
  word and a fifth deliberately avoids it. Documented rather than split:
  renaming the annotation key would rename properties in every existing
  specification, which waits for 0.11.0 and is recorded there as a candidate.
- P12, `diff` writes only with `--changelog PATH`. It had appended to the
  working directory on every invocation, including read-only inspection, and
  duplicated the entry on a second run.
- Assistant decoupling. One OpenAI-compatible chat-completions path covers
  Ollama, vLLM, llama.cpp, and hosted providers, configured by `--endpoint` or
  `SPECL_LLM_ENDPOINT`, defaulting to local Ollama. A bearer token is sent only
  when configured, because local endpoints reject the header.
- `specl-assist suggest-annotations`, deferred since 0.2.0. It reads the shapes
  rather than a model: every value is a placeholder, because a plausible
  acceptance criterion nobody checked is worse than an absent one. The shapes
  stop reporting it and the gap becomes invisible.

## 0.11.0 — Identifier cleanup and contract freeze

The second and final designated graph-breaking release. Its job is to absorb
every break accumulated during the additive run and leave the graph contract in
the shape 1.0 will freeze.

**Lands, done.** P8: design notes and comments require `DN` and `C` identifiers,
replacing content-hash IRIs. P19, both halves. `specl:role`, `specl:capability`, and `specl:benefit` replace
`specl:asA`, `specl:iWant`, and `specl:soThat`, and `specl:role` is an object
property naming a declared `specl:Persona` rather than holding a literal. The
second half was nearly missed: the entry below listed two questions and the
first pass answered only the naming one.

Referenced by identifier rather than minted from a name, so `finance clerk` and
`Finance Clerk` cannot become two personas. Surface forms live on the persona as
SKOS labels. `capability` and `benefit` stay literals by decision: they are prose
specific to one story rather than entities anything refers to. P11:
`decisionStatus:` and `resolutionStatus:` are accepted directly, with `status:`
retained because removing it would break every existing specification for no
gain.

Contract 2 is emitted. Contract 1 copies of the vocabulary and shapes stay
fetchable, built from the `v0.10.0` tag rather than from HEAD, which would
silently republish them as contract 2.

- **P19, the user story property names.** `specl:asA`, `specl:iWant`, and
  `specl:soThat` are transliterated fragments of the sentence template "as a
  role, I want a capability, so that a benefit". A property whose local name is
  a pronoun and a verb, or a conjunction, describes the template a resource was
  authored from rather than anything about the resource. What they denote is a
  role, a capability, and a benefit, and the vocabulary should say so.

  Two questions to settle together. Whether the replacements are datatype
  properties as today, or whether the role becomes an object property pointing
  at a persona, which would stop a literal reading "maintainer" from repeating
  across every story. And whether the old names remain as deprecated aliases or
  are removed outright; removal is available only in this release.

  Renaming is both an IRI change and, if the role becomes an object property, a
  range change, so this release is the only window before the 1.0 freeze.

**Migration, done.** `specl-migrate contract` renames the user story properties
and updates the conformance declaration. It does not rewrite content-hash IRIs:
the old identifier was a function of the prose, so nothing in the graph says what
it should become. Those are reported and the tool exits 3, because a guessed
identifier is worse than a named gap.

**Exit criteria.** No item IRI is a function of prose. The graph-contract version
emitted by 0.11.0 is the one 1.0 will declare stable.

## 1.0.0 — The contract stops being the author's to change

1.0 marks a change in who may change the specification, not a claim that the
specification is finished. Before it, the author changes the contract on the
schedule above. From it, the underlying specification does not change without
consensus among the user base. See
`docs/decisions/0009-what-1.0-means.md`, which replaced an earlier set of
criteria that asked for adoption evidence as a precondition for the release that
makes adoption reasonable.

**Criteria.**

| | Criterion | State |
| --- | --- | --- |
| 1 | Documented graph contract with a migration path from every prior version | met |
| 2 | Every section type, annotation key, and shape exercised by the corpus | met, asserted in `tests/test_exit_criteria.py` |
| 3 | Published IRIs resolve | open: one pull request, see `tools/w3id/README.md` |
| 4 | Known limitations documented where an evaluating adopter reads first | open |
| 5 | Governance mechanism written down | met: `GOVERNANCE.md`, with issue templates and a check that the comment period agrees across artifacts |

Additive changes land whenever they are ready, because nobody migrates for them.
Substantive changes are collected in a window that opens the day 1.0 ships and
closes one year later, all sharing that one date, and are released together as
2.0. A substantive objection from a registered adopter blocks rather than being
outvoted. `GOVERNANCE.md` also lists what is not governed at all, because a
process that gates defect fixes becomes an obstacle to keeping the promises it
protects.

**Not criteria, and previously were.** That the IRI scheme survived a
multi-specification project, and that an outside author passed the gate. Both
are adoption evidence, both were circular as gates, and the first is now
unavailable by choice: multi-specification component identity is deferred below
and expected to break things. The outside author remains the only real test of
whether the syntax documentation is sufficient; 1.0 is what enables it rather
than what waits on it.

## 2.0.0 — One year after 1.0

The first release the author does not decide alone, and the first whose contents
are fixed by a date rather than by a plan. The collection window opens the day
1.0 ships and closes a year later; whatever has been raised, discussed, and not
objected to by then is what 2.0 contains.

The work deferred below collects here, alongside whatever a real user base
raises. Expect the contract to change: any honest plan with one developer and
one adopter expects the specification to move once more people use it, and this
is where that is permitted to happen.

1.x releases continue throughout the window. They carry additive changes,
implementation work, and defect fixes, none of which wait for anything.

## Deferred to 2.0

Recorded here rather than scheduled, with the plumbing question answered for
each: whether anything must land before the freeze.

Each item here is expected to break something, which is why they land in 2.0
together rather than trickling through 1.x. From 1.0 these are not the author's
to decide alone.

### Multi-specification projects and component identity

`constrains` and `verifiedBy` mint their nodes under the referencing
specification's own base, so a component named by three specifications is three
nodes with nothing relating them. Not a spelling problem: it happens when
everyone spells it identically. Visible here already, since `specl_tool`
declares `component-explorer` while `specl_explorer` is that component with its
own Specification IRI.

The likely shape is a front-matter map from a component name to a
project-controlled IRI, in the manner of `references:`. **Expect breaking
changes.** The mapping mechanism itself is additive, but a project that adopts
it moves every component IRI it had, and the work may well surface more: shared
personas and agents have the same spec-local minting, and a cross-specification
identity model touches all three.

This should be designed against a real multi-specification project rather than
invented. Designing cross-specification identity without one in front of you is
how it gets designed wrong.

This is the clearest case for why 1.0 cannot mean "proven complete". The defect
is known, a real multi-specification project hits it immediately, and fixing it
properly needs that project to exist. 1.0 documents the limit; 2.0 fixes it with
the people who hit it.

### Agent integration: a skill, an MCP server, and printable prompts

specl's deterministic verbs (`translate`, `validate`, `score`, `diff`,
`layering`, `migrate`) are a natural MCP surface: pure functions over files
returning structured results, which an agent can call instead of shelling out
and parsing text. Authoring is a different question and a skill's job, since the
identifier grammar, the annotation keys, and the conventions around parking a
heading or never fabricating an acceptance criterion are judgment rather than a
tool list. The two are complementary.

The related question was whether `specl-assist gaps` and `check` should be
deprecated, on the grounds that they embed a model call inside a CLI an agent is
already driving. **Answered no.** Four things would be lost, and the last is the
one that decides it.

- Hostless use. The redundancy argument holds only when an agent is driving.
- CI. `check` runs as a pipeline step with a key in the environment. An agent
  does not.
- Air-gapped operation. UR13 exists because the consumer has no network. A local
  endpoint works there; an agent host may not exist at all.
- `check` is the only thing in specl that operates on meaning. Everything else
  reads the graph. No shape finds two requirements that contradict each other
  while both validate cleanly.

The argument that an agent has more context also cuts the other way: an agent
that has just read the implementation is primed to see coherence in requirements
that do not cohere. For a consistency check, the narrower context may be better.

What survives is narrower and additive: `--print-prompt` on both subcommands,
emitting the prompt and calling nothing. The same versioned prompt then serves
the CLI directly and an agent that wants to answer it with its own context. It
also makes the prompts reviewable, which they are not today.

**Plumbing needed before 1.0: none.** Everything here is additive at the CLI
level. A new flag, a structured-output mode, an MCP server, and a skill all leave
IRIs and property ranges untouched, and the batching policy only reserves those
for a designated break. A new vocabulary class, if agent review is ever recorded
as data, is additive too and may land after the freeze. The one thing that would
have needed to precede 1.0 is a graph-contract change, and none of this is one.

The prompts in `spec_assistant.py` are an unassigned pair in
`docs/decisions/0006-artifact-agreement-strategy.md`: they make claims about
what a good specification looks like and nothing checks them against the shapes
they are meant to help satisfy. Printing them is the first step toward binding
them.

## Where the plan is soft

The additive run from 0.4.0 through 0.10.0 is loosely ordered and several
releases could swap. Two constraints actually hold: 0.5.0 depends on 0.3.0, and
0.8.0 should follow 0.6.0 and 0.7.0 so the metric is designed against the full
vocabulary. Everything else is preference.

If the pre-1.0 train runs longer, the natural extensions are verification
coverage from ingested test results, a slash-namespace option for projects
wanting Schema.org-style per-term dereferencing, and a specification diff
reporting semantic change rather than triple change.
