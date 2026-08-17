# specl changelog

Releases from 0.3.0 onward are tagged in this repository and not published.
PyPI carries 0.2.0 until 1.0; see
`docs/decisions/0007-internal-releases-until-1.0.md`. A section is dated when
its release is tagged.

## 0.11.0 — tagged 2026-08-16

The second and final graph-breaking release. Graphs move from contract 1 to
contract 2 with `specl-migrate contract`.

### Build correctness
- The contract 1 vocabulary and shapes are frozen files in `published/` rather
  than reconstructed with `git show v0.10.0:`. The tag does not exist in every
  clone and `actions/checkout` fetches none by default, so the Pages build
  failed. A frozen artifact a build rebuilds from history is one shallow clone
  away from disappearing.
- An f-string nesting its own quote parsed on 3.12 and was a syntax error on
  3.11, the floor the package claims. Caught by the version matrix on its first
  real run, and now checked for directly.

### Release readiness
- `LIMITATIONS.md`, linked from the top of the README: what specl does not do,
  collected where someone deciding whether to adopt will read it rather than
  scattered across the roadmap and the contract page. Closes 1.0 criterion 4.
- `RELEASING.md`. The 1.0 procedure has ordering that matters: Pages content
  must be live before the redirects pointing at it merge, and creating the
  GitHub release is what publishes to PyPI.

### Portability
- Every text read and write declares an encoding. Python falls back to the
  locale encoding, which is cp1252 on most Windows installs, so 110 calls were
  reading files as cp1252 off Linux. An adopter running the suite on Windows hit
  three failures on a single non-ASCII byte in `explorer.html`; the rest were
  equally wrong and merely lucky.
- `specl-validate diff --changelog` appended in the platform encoding, which
  would have corrupted a changelog containing non-ASCII.
- `tests/test_portability.py` walks the AST rather than matching text. Its first
  version scanned line by line, so a call split across two lines never found its
  closing parenthesis, and it treated what it could not parse as passing: ten
  writes went through and six reached the adopter. A file it cannot parse now
  raises rather than reporting clean.
- CI runs the suite on Windows as well as Linux.

### Governing vocabulary terms
- `vocabularies:` in front matter and a `governs:` annotation, for a requirement
  that constrains a term in an ontology the project implements rather than a
  component it builds. Found in the first real consumer specification, which
  wrote a Python class and an RDF class in one `constrains:` list.
- `constrains` keeps `specl:Component` as its range rather than being widened,
  because the range is what makes it checkable. A vocabulary term written under
  `constrains` warns and names the right key.
- `specl-validate layering` verifies that a governed term is defined by its
  vocabulary when a local path is declared. A misspelled class name is a valid
  IRI, so nothing else would catch it.

### Migration and badges
- `specl-migrate source` rewrites a pre-0.11 specification's markdown for
  contract 2. Regenerating from source was always the better path than migrating
  a graph, and nothing existed to prepare the source with. Renaming `asA` to
  `role` turns a working value into a warning, so the command reports which
  values now need a declared persona or agent rather than leaving it to be
  found.
- `specl-validate badge` prints a markdown snippet linking the badge to the
  Specification IRI, which already resolves to the source. `--link` overrides
  it. The link cannot live in the SVG, because GitHub sanitizes images.

### Governance
- `GOVERNANCE.md`. From 1.0 the author does not change the specification
  unilaterally. Additive changes, which leave every existing graph valid, land
  whenever they are ready. Substantive ones are collected in a window that opens
  the day 1.0 ships and closes one year later, all sharing that date, and are
  released together as 2.0. Silence at the close is assent, so adopters register
  and are notified; a substantive objection from a registered adopter blocks
  rather than being outvoted, and an unresolved one at the close drops a
  proposal to the next window rather than shipping over it.
- A proposal raised in the last sixty days rolls to the following window,
  because one nobody has had time to object to has not been agreed to.
- What is *not* governed is listed explicitly. A process that gates defect fixes
  becomes an obstacle to keeping the promises it protects.
- The window is a year because specl targets organisations that review tooling
  annually, and a two-week window is invisible to them. `docs/proposals/OPEN.md`
  lists what is collected against the shared closing date, so a reader on an
  annual cycle finds pending changes without having watched the discussion.
- Issue templates for specification changes and adopter registration, and a test
  asserting the comment period agrees between `GOVERNANCE.md` and the template.
- `docs/decisions/0009-what-1.0-means.md` recasts 1.0 as a change in who may
  change the specification, replacing criteria that asked for adoption evidence
  as a precondition for the release that makes adoption reasonable.

### Build correctness
- The contract 1 vocabulary and shapes are frozen files in `published/` rather
  than reconstructed with `git show v0.10.0:`. The tag does not exist in every
  clone and `actions/checkout` fetches none by default, so the Pages build
  failed. A frozen artifact a build rebuilds from history is one shallow clone
  away from disappearing.
- An f-string nesting its own quote parsed on 3.12 and was a syntax error on
  3.11, the floor the package claims. Caught by the version matrix on its first
  real run, and now checked for directly.

### Release readiness
- The 1.0 criteria are measured in the roadmap rather than assumed. Three of
  five are open.
- Criterion 3 is closed: `Open Issues` and `decisionStatus` were never exercised
  by any specification in the corpus, and a test now asserts every section type
  and annotation key is.
- The w3id pending table is computed from a diff against the live upstream file
  rather than remembered. It listed six changes; there are ten. A test asserts
  every rule not already upstream is named in it.
- The w3id procedure gains the upstream path, the ordering constraint that
  content must be published before a redirect to it merges, and the curl loop
  to verify each rule after the merge.

### Adoption
- Validation probes for SHACL Advanced Features and refuses to run without
  them, rather than reporting the clean result a processor lacking them would
  produce. Checked once per process, about thirty milliseconds.
- `specl-validate conformance` checks that a SHACL processor applies these
  shapes as intended, and `--export DIR` writes the fixture, shapes,
  vocabulary, and expected findings out for use with another processor. The
  shapes need SHACL Advanced Features, and a processor without them reports
  none of the seven findings rather than erroring.
- The README distinguishes the bundled processor, which needs nothing extra,
  from a third-party one, which needs checking.

### Measurement corrections
- Retired items leave the measured population. They are not evaluated by the
  shapes, so counting them made every one clean and retiring a requirement
  raised the maturity score. Found by adding a withdrawn requirement to a trial
  specification and watching it go from 90% to 91%.
- Progress is computed over requirements and user stories only. A decision
  record has no implementation, and counting one as not-started made a
  specification look less built the more thinking it recorded.
- Subscores use the same population as the headline number, which they did not.
- The `spec_base` error cites a URL rather than a repository path and gives an
  example base.

### Documentation and packaging
- README gains concepts, requirements, and workflow sections. It described the
  commands and not the model, said nothing about dependencies or the Python
  floor, and offered no adoption patterns.
- The publish workflow refuses any version below 1.0. It fires on a published
  GitHub release, so tagging through the UI would have pushed to PyPI and broken
  the policy in 0007 silently. The policy was prose; it is now executable.
- `requires-python` narrows to 3.11, which is what CI tests, and the two are
  checked for agreement. The floor was 3.10 and untested.
- The PyPI badge is removed from the README, where it advertised 0.2.0 two lines
  above the section explaining not to install it.
- Documented that specl is a command-line tool with no supported public API.

### Breaking
- **P8.** Design notes and comments require `DN` and `C` identifiers. Their IRIs
  were minted from a hash of their text, so editing wording changed the IRI and
  broke inbound references.
- **P19.** `specl:role`, `specl:capability`, and `specl:benefit` replace
  `specl:asA`, `specl:iWant`, and `specl:soThat`, which named fragments of a
  sentence template rather than anything about the resource.
- `specl:Persona` and a `# Personas` section with prefix `P`. `specl:role` is an
  object property naming a declared persona, referenced by identifier rather
  than by name so that two spellings cannot become two personas. Surface forms
  are `skos:prefLabel` and `skos:altLabel` on the persona. `capability` and
  `benefit` remain literals.
- Every graph declares `dct:conformsTo <https://w3id.org/specl/contract/2>`, and
  the vocabulary and shapes carry `owl:versionIRI` for contract 2. Contract 1
  copies remain published and fetchable.

### Added
- **P11.** `decisionStatus:` and `resolutionStatus:` are accepted directly.
  `status:` still resolves by class and is unchanged.
- `specl-migrate contract` migrates a contract 1 graph.
- `specl:Item`, a superclass of every item class. `specl:partOf` declared
  `rdfs:domain specl:Requirement`, and `rdfs:domain` is an inference rule rather
  than a constraint, so a reasoner concluded that every design note, decision,
  and persona was a requirement.
- Every declared range and domain is checked against emitted output, derived
  from the vocabulary rather than enumerated, so a new term is covered on
  declaration. The shapes graph is validated against the SHACL specification,
  and every vocabulary term carries a label or a comment.
- The maturity population is read from `rdfs:subClassOf specl:Item` instead of a
  hardcoded list, which had silently omitted `AcceptanceQuery` since 0.6.0 and
  `Persona` since 0.11.0, so neither counted toward any score.
- Item classes are declared pairwise disjoint and separately enforced in the
  shapes. `specl:partOf` and `specl:role` are functional.
- `shapes.ttl` imports the vocabulary, and validation supplies it to the
  processor. A shape consulting the class hierarchy found nothing rather than
  failing, because its SPARQL runs against the data graph.
- The contract page states the conformance requirement: these shapes need SHACL
  Advanced Features, and a processor without them silently applies almost
  nothing rather than erroring.
- Declared ranges on `specl:constrains` and `specl:verifiedBy` are enforced.
  P1 fixed the literal half; nothing compared the emitted object against the
  range, so `constrains: R1` put a requirement where the ontology reserves a
  component.

## 0.10.0 — tagged 2026-08-16

### Ergonomics
- **P12.** `specl-validate diff` writes a changelog stub only with
  `--changelog PATH`. It previously appended to `CHANGELOG.spec.md` in the
  working directory on every invocation and duplicated entries when rerun.
- **P11.** The four unrelated properties called status are documented in a
  table in `docs/SYNTAX.md`.
- The assistant speaks the OpenAI chat-completions shape on one code path,
  configured with `--endpoint` or `SPECL_LLM_ENDPOINT` and defaulting to local
  Ollama. `--api-key` or `SPECL_LLM_API_KEY` is sent as a bearer token only when
  set.
- `specl-assist suggest-annotations` prints pasteable annotation stubs derived
  from the shapes rather than from a model. Every value is a placeholder.
- `--provider` names an endpoint: `ollama`, `claude`, `openai`, `vllm`,
  `llamacpp`. Claude needs no adapter, since Anthropic publishes an
  OpenAI-compatible layer. `max_tokens` is sent unconditionally, being optional
  for some servers and required by others.

## 0.9.0 — tagged 2026-08-16

### Multi-file specifications
- `companion_files` in front matter. Sections merge in declared order and prose
  concatenates, so a split specification translates to the same graph as the
  equivalent single file, apart from provenance.
- Each item names the file it came from and the line within it. Documents are
  identified by path relative to the root, so two files with the same basename
  do not collide.
- A companion that does not exist is refused rather than warned about. A
  companion declaring its own `spec_base` or `spec_id` is ignored with a
  warning.

## 0.8.0 — tagged 2026-08-16

### Measurement as data
- `specl:MaturityAssessment`, a `prov:Activity` recording the score, the
  progress, and a per-class breakdown. `score --history FILE` appends one;
  appending is opt-in so a reporting run accumulates nothing.
- `badge --history` renders the latest recorded assessment rather than the only
  artifact.
- `implementation:` annotation with `not-started`, `in-progress`,
  `implemented`, `verified`, rolled up into a progress figure separate from
  maturity.
- Maturity is priority weighted, deferred since 0.2.0.
- An open issue that is still open is never clean, so a specification cannot
  report full maturity while carrying unanswered questions.

## 0.7.0 — tagged 2026-08-16

### Provenance
- Every item carries `prov:wasDerivedFrom` naming a `specl:SourceDocument` and
  `specl:sourceLine` giving the line it was authored on, prose-derived items
  included. Front matter and comment blocks are blanked rather than removed
  during parsing so the numbering indexes the file as authored.
- The source document is identified by file name rather than by the path given
  on the command line, so a graph does not differ by working directory.
- `--generated-at ISO8601` records a `prov:Activity`. The timestamp is supplied
  rather than read from the clock, so translation stays a pure function of its
  source and output remains byte-identical across runs.

## 0.6.0 — tagged 2026-08-16

### Publication
- `shapes.ttl` declares an ontology IRI and a version IRI. It had neither, so
  UR17's commitment to versioned fetchable locations was unsatisfiable rather
  than merely unmet.
- Both graphs are published at `/specl/ns/1` and `/specl/shapes/1`, addressed by
  graph contract rather than by release, with redirect rules and Pages copies.
- `owl:versionIRI` is checked for agreement with the contract the translator
  emits, across all three artifacts.
- Both graphs stopped declaring a `spec:` prefix bound to the namespace 0.3.0
  retired. Unused in both, and shipped in both.

### Sections and queries
- **P7.** A heading the translator does not recognize warns and names itself
  instead of dropping its content. `sections:` in front matter maps a project
  heading onto a class the vocabulary declares, and `<!--specl: parked-->`
  beneath a heading silences the warning for content authored ahead of a class
  that models it.
- `specl:AcceptanceQuery` under `# Acceptance Queries` with prefix `Q`, and a
  comma-split `gates:` annotation resolving to requirement IRIs. A query gating
  nothing warns; a query gating an undeclared identifier warns like any other
  reference.

## 0.5.0 — tagged 2026-08-16

### Cross-specification references
- **P10.** Front matter is parsed with `yaml.safe_load`. The previous parser
  flattened nested mappings into one dict, so the committed `references:`
  syntax could not be represented at all, and invalid YAML is now rejected
  rather than half-parsed.
- `references:` declares foreign prefixes with a base and a local path. A
  `PREFIX:ID` token in a reference-valued field resolves through it; an
  undeclared prefix warns and stays a literal. A foreign base is held to the
  `spec_base` grammar.
- `dependsOn`, `refines`, and `upstreamOf` between specifications, emitted as
  IRIs to the peer.
- `specl-validate layering` checks cross-specification references against those
  relations. It never touches the network, and an unreadable peer reports
  inconclusive with exit 3 rather than passing.

## 0.4.0 — tagged 2026-08-16

### Commitments as a specification
- `docs/DOWNSTREAM-COMMITMENTS.md` is now a specl specification at
  `specs/commitments/spec.md`, carrying the consumer's own `UR` identifiers, and
  is translated, validated, and scored in CI. Each implemented commitment names
  the test that verifies it, checked against pytest collection.
- `item_prefix` front-matter key, moved forward from 0.6.0, declaring a
  project's own item prefix in place of the reserved one a section requires.
- `specl-validate score` names why a gate failed. It reported "0 violations" for
  a production specification failing on warnings.

### Item lifecycle
- `itemStatus` annotation with `active`, `superseded`, and `withdrawn`, on every
  item class. Absent means active.
- `supersededBy` annotation, resolving to an IRI, so a retired item names its
  replacement and the chain is traversable with `specl:supersededBy+`.
- An item marked `superseded` with no replacement named produces a warning, as
  does a lifecycle value outside the three.
- A retired item is no longer evaluated by the other shapes, so it accumulates
  no warnings about annotations it will never gain.
- A successor must be the same class and belong to the same specification.
- `withdrawn` is the no-successor case; naming a successor on one warns.
- `specl-validate diff` reports reuse of a withdrawn identifier and exits
  non-zero. A withdrawn identifier is permanently reserved, and reuse is only
  visible across two graphs.

## 0.3.0 — tagged 2026-08-16

This entry was written before release and has been **amended in place**. The
original version described a single global instance namespace at
`https://w3id.org/specl/spec#`; that is a defect, not a feature, and shipping it
would have committed permanent identifiers requiring immediate migration. Nothing
external depends on this version, so the entry was corrected rather than
withdrawn.

The scope also grew. Under the break-batching policy (see `docs/ROADMAP.md`),
0.3.0 is one of only two releases permitted to change emitted IRIs, so every
graph-breaking fix travels with it rather than forcing a second migration.

Do not ship until the test suite lands; see `HANDOFF.md`.

### Added

- **Vocabulary at a stable w3id.org namespace.** Generated Turtle uses
  `https://w3id.org/specl/ns#` for the vocabulary, prefix `specl:`. The old
  `https://example.org/ekga/ns#` namespace and `ekga:` prefix are retired.
- **Project-supplied instance namespaces, mandatory.** specl no longer mints
  instance IRIs under its own domain; `https://w3id.org/specl/spec#` is retired,
  not partitioned. A hash-terminated `spec_base` front-matter key is required and
  translation fails without it. A `prefix` key declares the CURIE expansion. See
  `NAMESPACE-MIGRATION.md`.
- **`title:` annotation key** on all item classes, with a description-derived
  fallback materialized into the graph. Without this, no markdown-authored
  decision record could satisfy `DecisionRecordShape`.
- **Warning on unrecognized top-level sections**, failing under `--strict`, plus
  a `<!--specl:prose-->` marker declaring a section intentionally non-normative.
  Previously such sections were dropped silently.
- **`specl-validate diff --ignore-base`** for verifying a migration as an IRI-only change.
- **`specl-migrate iris`** for consumers holding only Turtle.
- **Graph-contract version** in the Turtle header.
- **Test suite**, including golden-file fixtures, a fixture exercising every
  section type, and a structural assertion that every property required at
  Violation severity by any shape is producible by the translator.

### Fixed

- **Object properties emitted as IRIs.** `affects`, `constrains`, and
  `verifiedBy` are declared `owl:ObjectProperty` but were emitted as string
  literals, making the graph inconsistent with its own ontology and reducing
  traceability to string matching. References now resolve against the
  specification base by concatenation, with a parser warning on references that
  do not resolve.
- **Conditional `constrains` and `verifiedBy` shapes.** Both warned
  unconditionally, so a specification declaring no components accumulated
  warnings no authoring could clear. Since all warnings block at `production`,
  this made that status unreachable for such specifications.
- **`score` denominator.** The finding set was built from all focus nodes while
  the denominator counted requirements only.

### Also in this release

- **`specl_tool` spec** — SPECL now evaluates its own maturity. The
  new `specs/specl_tool/spec.md` covers the parser, validator, scorer,
  badge generator, LLM assistant, explorer, and packaging (16
  requirements, all fully annotated). Note that its reported maturity
  covers requirements only, and the spec contains no decisions, open
  issues, or design notes; see `docs/proposals/0001-defects-and-enhancements.md`
  on what that score does and does not measure.
- **Maturity badges auto-committed by CI.** The `spec.yml` workflow
  generates SVG badges for every spec and commits them to
  `static/badges/` on pushes to `main`. Badges are git-tracked and
  referenced in the README via `raw.githubusercontent.com` so they
  render without depending on GitHub Pages.
- **GitHub Pages deployment.** The `pages.yml` workflow publishes the
  ontology (`ns.ttl`), SHACL shapes (`shapes.ttl`), the spec explorer
  (`explorer.html`), committed badges, and a vocabulary landing page
  to `zwelz3.github.io/specl/`. This is the dereference target for
  the w3id.org redirects.
- **Vocabulary landing page** at `static/index.html` documenting all
  SPECL classes, key properties, and namespace URIs. Served as the
  GitHub Pages index.
- **PyPI badge** in the README header (`img.shields.io/pypi/v/specl`).
- **Conda note** after the install section indicating a conda-forge
  recipe is in progress.

### Changed

- **Prefix rename: `ekga:` → `specl:`** across all source files,
  shapes, ontology, explorer, and documentation. The `ekga:` prefix
  was an artifact of the first downstream project; `specl:` matches
  the package name and is semantically correct for a general-purpose
  spec language.
- **Hash namespaces for both vocabulary and instances.** Both
  `specl:` and `spec:` use `#` (not `/`). Hash namespaces resolve
  all terms to a single document, which is the right model for
  specs authored and consumed as a unit. Slash namespace support
  (Schema.org pattern) is tracked as an open issue for a future
  release.
- **GitHub Actions updated to Node 24.** `actions/checkout@v6` and
  `actions/setup-python@v6` (native Node 24), plus
  `FORCE_JAVASCRIPT_ACTIONS_TO_NODE24=true` for actions that have
  not yet released Node 24 versions. Python bumped to 3.12.
- **`pip install specl`** in the README (was `pip install -e .`).

### Deferred

- Multi-file specs via front-matter `companion_files` key.
- `specl-assist suggest-annotations` subcommand.

### Identifiers
- **Breaking.** `spec_base` is required in front matter and every item IRI is
  that base plus the identifier token. The shared
  `https://w3id.org/specl/spec#` namespace is retired and not reassigned; see
  `NAMESPACE-MIGRATION.md`.
- The Specification node is the base without its terminating `#`. `spec_id` is
  optional, emitted as `dct:identifier`, and is not part of any IRI.
- Every graph declares `dct:conformsTo <https://w3id.org/specl/contract/1>`.
- `prefix:` front-matter key carried as `specl:prefix`, reserved for
  cross-specification references in 0.5.0.

### Artifact agreement
- `SUB_RE` is derived from `PROP_MAP` rather than restating it.
- `core.ttl` declarations are checked against emitted predicates in both
  directions, which found `specl:iWant` declared with no authoring path. The
  key is now wired, so a user story can carry the middle clause of its sentence.
- `verifiedBy` claims are checked against the test suite. Fifteen of nineteen in
  specl's own specification named tests that had never existed.
- Each guarantee in `docs/contracts/1.md` names the test that asserts it, and
  both halves of that binding are checked.
- `iWant` annotation key on user stories.

### Validation
- Maturity is computed over every item class rather than requirements only.
  Findings against decisions and open issues used to match no requirement and
  be discarded.
- A specification whose gate fails reports no maturity percentage, and its
  badge reads "failing". A green badge over a failing gate was possible before.
- `specl-validate diff --ignore-base` keys requirements by identifier token, so
  a rebased graph diffs against its original.

### Tooling
- `specl-migrate iris` rewrites a pre-0.3.0 graph onto a declared base for
  consumers holding only Turtle, converting reference properties to IRIs and
  deriving missing titles so the result matches what regenerating would
  produce. Refuses to infer the base and refuses a merged legacy graph, whose
  collisions are not recoverable.

### Traceability
- **Breaking.** `affects`, `constrains`, and `verifiedBy` emit IRIs rather than
  string literals, matching the object-property declarations in `core.ttl`.
- An item reference to an identifier no specification declares warns; the IRI is
  still emitted so the dangling reference is visible.
- External artifacts become typed `specl:Component` and `specl:Test` nodes
  carrying the original value as `dct:identifier`.

### Parser
- Identifier grammar matches the published register: any uppercase prefix, any
  number of dot-separated digit groups. `R1.2.3`, `US1.2`, and `D1.1` translate.
- A top-level bullet that looks like an item and does not parse warns instead of
  being dropped in silence.
- Mixing padded and unpadded ordinals under one prefix warns. They remain
  distinct identifiers and are never merged.
- `Open Questions and Gaps` recognized as a section heading.
- `title:` annotation on every item class, mapping to `dct:title`, with the
  committed fallback derivation materialized into the graph when absent.
- Nested content under an item emits as an `rdf:List` on `specl:detail`.
- `dct:created` emitted only when the specification supplies it.
- Priority-weighted maturity scoring.
- Slash namespace support via `namespace_style: hash | slash`
  front-matter key.

## 0.2.0

Parser extension for structured per-item annotations. Addresses the
core limitation that prototype-status specs could not reach non-zero
maturity without external tooling.

### Added

- **Sub-bullet annotations** under any ID-bulleted item. Sub-bullets
  at two or more spaces of indent with a recognized key produce
  structured RDF triples. Recognized keys: `priority`, `acceptance`,
  `verifiedBy`, `constrains`, `asA`, `soThat`, `owner`, `recommendation`,
  `status`, `rationale`, `affects`. See `docs/SYNTAX.md`.
- **Comma-separated multi-values** on `constrains:` and `affects:`
  sub-bullets. Prose-heavy keys (`acceptance`, `verifiedBy`) do not
  split on commas — use multiple sub-bullets for multiple values.
- **OpenIssue ID prefix `OQ`** (e.g., `OQ1`). Previously open issues
  were auto-slugged from their description; `OQ`-prefixed items now
  produce stable IRIs and accept sub-bullet annotations (`owner`,
  `recommendation`, `status`).
- **DecisionRecord support**. New section `# Decisions` recognized,
  with `D`-prefixed IDs and sub-bullet annotations (`status`,
  `rationale`, `affects`). `status:` is context-sensitive and maps to
  `specl:decisionStatus` for decisions, `specl:resolutionStatus` for
  open issues.
- **Front-matter comment block** `<!--specl ... -->` for
  spec-level metadata that does not belong in YAML front-matter. First
  supported key: `created:` (overrides the default of today's date).
- **`--strict` flag** on `specl-translate` prints parser warnings
  to stderr (unrecognized annotation keys, orphaned sub-bullets,
  prefix mismatches). Warnings are non-fatal.

### Changed

- Turtle output now uses one-property-per-line formatting (added in
  0.1.x, reconfirmed in 0.2.0 for readability and clean git diffs).
- Section `# Open Issues` is now recognized alongside
  `# Open Questions` and `# Open Questions and Gaps (flag for follow-up)`.

### Backward compatibility

Existing specs without sub-bullet annotations produce byte-identical
RDF to 0.1.x (same subject set, same triples). The EKGA reference
spec was used as the golden-file fixture during development.

### Deferred to 0.3.0

- Multi-file specs via front-matter `companion_files` key (Phase 4 of
  the enhancement plan).
- `specl suggest-annotations` subcommand for scaffolding missing
  sub-bullets (Phase 5).
- Priority-weighted maturity scoring (distinguish clean MUSTs from
  clean SHOULDs).

## 0.1.0

Initial release.
