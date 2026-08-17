# Handoff

Start here. Then [CLAUDE.md](CLAUDE.md) for the invariants, then
[docs/DOWNSTREAM-COMMITMENTS.md](docs/DOWNSTREAM-COMMITMENTS.md) before touching
anything that changes emitted output.

## What specl is

An RDF-native, SHACL-validated specification format. Markdown in, Turtle out,
validated against a shapes graph whose severity gate tightens when a
specification declares itself production-ready. A CLI translates, validates,
scores, diffs, and renders badges. An optional local-LLM assistant suggests
annotations.

## Where things stand

**Published:** 0.2.0 on PyPI, under the retired `example.org/ekga` namespaces.

**On `main`:** the 0.3.0 work, unreleased. It moves to w3id.org namespaces,
renames `ekga:` to `specl:` and `spec:`, adds the `specl_tool` self-spec, and
adds badge and Pages CI.

**Not shipped, and should not ship as originally written.** The 0.3.0 headline
feature is a single global instance namespace at `https://w3id.org/specl/spec#`.
Every specl user everywhere would mint `spec#R1`. This repository already
demonstrates the collision: translate the `excel_service` and `pptx_templater`
fixtures under `tests/fixtures/`, merge
them, and 11 item IRIs are shared, with `spec#R1.1` carrying both a description
about an HTTP endpoint and one about preserving master slides, `partOf` both
specifications. Under `example.org` that was latent. Under w3id.org, chosen for
permanence, it is a commitment that cannot be walked back.

The 0.3.0 CHANGELOG entry has been **amended in place** rather than withdrawn,
since nothing external depends on it. Its scope grew: it now also absorbs the
object-property fix, the title key, the score denominator, and a test suite,
because those are graph-breaking or gate-blocking and the break-batching policy
says they travel together.

**Repository inconsistencies to reconcile before release:** `pyproject.toml` and
`src/specl/__init__.py` both declare `0.2.0` while the CHANGELOG describes 0.3.0
as shipped, and `NAMESPACE-MIGRATION.md` is referenced by the CHANGELOG but has
only now been written.

**There is no test directory.** This is the structural gap behind at least one
critical defect.

## What happened recently

specl was used to author a downstream specification, which exposed defects that
self-use had not. Three matter most, and each is a different kind of failure.

**P1, wrong output.** `affects`, `constrains`, and `verifiedBy` are declared
`owl:ObjectProperty` in `core.ttl` and emitted as string literals. A decision
annotated `affects: R8` produces the string `"R8"`. The graph contradicts its own
ontology and the traceability question the tool exists to answer can only be
resolved by string matching.

**P2, an unsatisfiable gate.** `DecisionRecordShape` requires `dct:title` at
Violation severity; no annotation key produces `dct:title`. Every
markdown-authored decision record fails validation unconditionally. This survived
two releases because none of the five self-specs uses a `# Decisions` section:
specl is dogfooded only on the paths that work.

**P3, permanent collision.** Above.

The full analysis of fourteen items is
`docs/proposals/0001-defects-and-enhancements.md`.

Decisions made while answering are in `docs/decisions/`. Two are accepted:
`0001-cli-surface.md`, which ships the IRI migration tool as a fourth console
script rather than under a new umbrella `specl` command, and
`0002-documented-gaps-registry.md`, which unifies every documentation exception
into one registry. `0003-self-spec-instance-base.md` is accepted: it fixes the instance bases and
moves the three example specifications to `tests/fixtures/`.
`0004-graph-contract-version.md` is accepted: the Specification node is the base
without its terminator and the contract is declared with `dct:conformsTo`. Both choose values a designated breaking release is
required to change, which is why they are settled before implementation rather
than during it.

The downstream consumer then raised seventeen requests, most of them for
*specified behavior* rather than features. All were answered:
`docs/proposals/0002-downstream-request-disposition.md`. The answers are binding
and are registered in `docs/DOWNSTREAM-COMMITMENTS.md`.

## The four things most likely to trip you up

**1. Pre-1.0 does not make graph changes cheap.** See invariant 1 and 2 in
CLAUDE.md. The version number covers the API surface; the emitted graph is a data
contract with its own version and its own policy.

**2. A downstream consumer has already authored against unbuilt features.** Its
acceptance query set is written in the exact shape `specl:AcceptanceQuery` takes
at 0.6.0, including the prefix and the `gates:` annotation. Changing the section
name, the prefix, or the annotation key breaks a document written on an answer
this project gave.

**3. The self-specs are not adequate coverage.** They avoid decisions entirely
and declare no components, so two whole shape families and one item class go
untested. A change that translates and validates all five self-specs cleanly may
still be broken. There is no Makefile or task runner in this repository;
`.github/workflows/spec.yml` invokes `specl-translate` and `specl-validate`
directly, per spec, and that workflow is the closest thing to a build.

**4. Several requests were declined on reasoning worth preserving.** No namespace
registry, no per-item shape suppression, no prefixed identifiers in source. Each
decline has an argument in the disposition. Re-granting one later without
addressing the argument is a reversal, not an improvement.

## Redirects are owned here and hosted elsewhere

Every specl IRI that resolves does so through rules in another repository.
`tools/w3id/specl.htaccess` is the source of truth for them and
`tools/w3id/README.md` records the update procedure, what is pending, and why a
pending rule does not block development. The doc checker verifies that every
redirect target pointing back at this project exists or is built.

## The doc check passes, and the mechanism behind it

`python3 tools/check_docs.py` is green and runs in CI. It compares documentation
against the code: referenced paths exist, referenced `specl-*` commands are
declared, referenced `specl-validate` subcommands are registered, and no
document invokes a bare `specl` umbrella command that has never existed.

Anything a document may legitimately name before it exists is declared in
`tools/documented-gaps.toml`, and every entry cites the record that authorizes
it. That registry is the only exception route for this repository's own content;
`docs/decisions/0002-documented-gaps-registry.md` records why the earlier
proximity heuristic was removed rather than tightened. Do not add a suppression
that lives in prose.

## What to do next

Work `docs/ROADMAP.md` in order. The near-term shape:

0. **The test suite exists now.** `pytest -q` from the repository root, wired
   into CI. Goldens under `tests/golden/` capture current behavior including its
   defects, which is what makes the P16 and P3 diffs legible when they land;
   regenerate with `tools/refresh_goldens.py` and read the diff as the review.
   Eleven tests are xfail and each names the defect that turns it green, so the
   suite reports progress rather than only regressions.

**Read `docs/decisions/0006-artifact-agreement-strategy.md` before adding an
artifact.** It carries the inventory of every pair that could disagree and how
each is held together, plus the three pairs still unassigned.

**What is left is in `docs/REMAINING.md`,** compiled from the roadmap, the
agreement inventory, and the commitments register. Three of the five 1.0
criteria are open and two of those cannot be closed by writing code.

**Releases are tagged, not published.** From 0.3.0 to 1.0 nothing goes to PyPI;
see `docs/decisions/0007-internal-releases-until-1.0.md`. "Ships" means tagged
everywhere in these documents. PyPI carries 0.2.0, which predates every 0.3.0
correction, and the README says so rather than leaving someone to find out after
installing.

**0.3.0 is tagged.** Every roadmap item in the release has landed: P1,
P2, P3, P13, P14, P16, P17, the nested-content work from 0005, `specl-migrate
iris`, `diff --ignore-base`, and the version reconciliation. Eight of the nine
exit criteria are executable in `tests/test_exit_criteria.py` and pass. The
ninth moved: the w3id pull request now gates the downstream embargo rather than
the tag, because no installed copy of 0.3.0 will exist and an IRI is an
identifier whether or not it resolves.

1. **The suite that step 0 describes was written first for a reason.** P1
   changes emitted triples and a golden comparison is the only cheap way to
   confirm nothing else moved. `tests/fixtures/maximal/` exercises every section
   type, so the dogfooding gap that hid P2 cannot recur, and
   `tests/test_shapes_coverage.py` carries the structural assertion that every
   Violation-severity required property is emittable. That assertion currently
   fails on P2 by design.
2. **Then 0.3.0** in full: P3, P1, P2, P13, plus the documentation deliverables
   the commitments register already fixes the content of.
3. **Then the additive run**, 0.4.0 through 0.10.0, in dependency order.

0.3.0 is the urgent one. Every specification authored before it acquires
identifiers that will need migrating, and the cost of delay compounds rather than
staying flat.

## Deliberately not done

- **Verification coverage from ingested test results.** Worth doing, deferred
  because it introduces a dependency on test-runner output formats.
- **Per-term stability tiers.** Deferred to 0.11.0; assigning stability to a
  vocabulary still gaining classes would record an assurance that cannot be
  honored.
- **The assistant's provider coupling.** `spec_assistant.py` hardcodes an Ollama
  URL. Scheduled for 0.10.0, low priority, and the local-only default should
  survive the change.

## Layout

| Path                              | Contents                                          |
| --------------------------------- | ------------------------------------------------- |
| `src/specl/spec_to_rdf.py`        | Markdown to Turtle translator.                     |
| `src/specl/validate_spec.py`      | SHACL validation, gate, score, badge, diff.        |
| `src/specl/core.ttl`              | Vocabulary.                                        |
| `src/specl/shapes.ttl`            | Shapes graph, two-tier severity.                   |
| `src/specl/spec_assistant.py`     | Local-LLM annotation assistant.                    |
| `specs/`                          | Five self-specs. Not adequate coverage; see above. |
| `docs/SYNTAX.md`                  | Markdown grammar reference.                        |
| `docs/DOWNSTREAM-COMMITMENTS.md`  | Behavior already specified to a consumer.          |
| `docs/ROADMAP.md`                 | Release plan through 0.11 and 1.0 criteria.        |
| `docs/proposals/`                 | The defect analysis and the request disposition.   |
| `NAMESPACE-MIGRATION.md`          | Legacy bases and migration procedure.              |

## One framing worth carrying

The defects found in this round share a shape. In each case an artifact asserted
something the code did not do: the ontology declared object properties that were
emitted as literals, the shapes required a property the translator could not
produce, the CHANGELOG described a release that was not published, and a
docstring claimed a registry drove behavior that a build variable drove.

None of these is a hard bug. Each is a disagreement between two artifacts that
nothing checked. The test suite in 0.3.0 should be aimed at that class of
disagreement first, because it is where this project's defects actually live.
