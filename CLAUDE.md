# Working rules

Invariants for any session on this repository. Read [HANDOFF.md](HANDOFF.md)
first for state, then [docs/DOWNSTREAM-COMMITMENTS.md](docs/DOWNSTREAM-COMMITMENTS.md)
before changing any emitted behavior.

## Invariants

1. **specl has two compatibility surfaces, and semver covers one.** The API
   contract (CLI, entry points, markdown syntax) breaks cheaply pre-1.0. The
   graph contract (the IRIs minted, the triples emitted, each property's range)
   is a data migration for every user. Never treat a change to emitted triples as
   an ordinary change because the version is pre-1.0.

2. **Graph-contract breaks travel only in designated releases.** 0.3.0 and 0.11.0
   are the only releases permitted to change emitted IRIs or a property's range.
   A break that becomes necessary mid-train waits for the next designated
   release. Without this, a long 0.x train means "migrate every release."

3. **Do not change behavior listed in `docs/DOWNSTREAM-COMMITMENTS.md` without
   checking it first.** Those answers were given normatively so a consumer could
   author against them, and the consumer did. Changing one is a migration for
   someone else, not a design revision.

4. **A changelog entry written before the work is a plan, not a record.** 0.3.0's
   headline feature, a single shared instance namespace at
   `https://w3id.org/specl/spec#`, was the defect rather than the fix, and the
   entry was amended before it shipped. Four other entries in that section were
   never caught the same way and describe things that never happened. Write
   entries at tag time; `RELEASING.md` says so.

5. **Dogfood the broken paths, not only the working ones.** A Violation-severity
   shape that no markdown-authored decision could satisfy survived two releases
   because no self-specification used a `# Decisions` section. Any new item class
   needs a specification that exercises it, and
   `tests/test_exit_criteria.py` now asserts that every section type and
   annotation key is used somewhere in the corpus.

6. **A Violation-severity shape must be satisfiable through the primary authoring
   path.** Assert this structurally: every property any shape requires at
   Violation severity must be producible by the translator. This belongs in the
   test suite, not in review.

7. **Never emit an object property as a literal.** `core.ttl` declares
   `specl:affects`, `specl:constrains`, and `specl:verifiedBy` as
   `owl:ObjectProperty`. Emitting them as strings makes the graph contradict its
   own ontology and reduces traceability to string matching. When adding a
   property, decide its range first and emit accordingly.

8. **Do not mint instance IRIs for a project into a namespace it does not
   control.** A user's requirements are the user's data, and the translator
   never invents a base on their behalf. The vocabulary is specl's artifact and
   lives at w3id.org; a user's instances do not. This is a prohibition on
   placing someone else's items in this project's namespace, not on a project
   using a namespace it owns: specl's own two specifications are based under
   `https://w3id.org/specl/tool/spec#` and
   `https://w3id.org/specl/explorer/spec#` for exactly that reason. See
   `docs/decisions/0003-self-spec-instance-base.md`.

9. **Answering is a deliverable.** A substantial share of what downstream needs is
   specified behavior, not code: grammars, resolution algorithms, semantics of a
   feature not yet built. Publishing an answer early lets a consumer author
   forward-compatibly. Do not defer a question to the release that implements it
   when stating the answer costs nothing.

10. **No network access at validation time.** Shapes and vocabulary resolve from
    the installed package. The layering check reads a local path. A validator
    that fetches is non-deterministic in CI and unusable in restricted
    environments.

## Known defects, unfixed as of this writing

All are analyzed in `docs/proposals/0001-defects-and-enhancements.md` with
evidence. Summarized here so a session does not rediscover them.

All fourteen defects from the 0.3.0 review round are closed, along with P19 and
P18 found later. `docs/proposals/0001-defects-and-enhancements.md` holds the
analysis and the corrections made to it; `docs/ROADMAP.md` records which release
each landed in and why.

Do not read that list as current state. It was left standing here for eight
releases, still saying "P14. No tests" against a suite of 315, which is the same
drift this project spends its checks preventing.

**What is actually open** is in `docs/ROADMAP.md`: three of the five 1.0
criteria, the ontology review findings, component identity across
specifications, and the agent integration work deferred past 1.0. Nothing there
requires a graph break; the two designated breaks are spent.

## Keeping artifacts in agreement

Every pair of artifacts that could disagree is assigned a tier in
`docs/decisions/0006-artifact-agreement-strategy.md`: derived so drift is
impossible, compared by a test, or bound claim-by-claim to a test where the
artifact is prose. Adding an artifact means adding it to that inventory. A pair
absent from it is a pair nobody has thought about, which is the state every
defect in the 0.3.0 review round started from.

`tools/check_docs.py` verifies that documentation agrees with the code:
referenced repository paths exist, referenced `specl-*` commands are declared in
`[project.scripts]`, referenced `specl-validate` subcommands are registered, and
no document invokes a bare `specl` umbrella command. It runs in CI.

Referencing something unimplemented is allowed and often necessary, since
downstream consumers author against announced behavior. It must be declared in
`tools/documented-gaps.toml` with the record that authorizes it, and the checker
verifies that record exists. That requirement is the whole mechanism:
`specl migrate-iris` reached three documents because nobody had decided it
existed.

The registry is the only exception route for repository content. There is no
proximity heuristic and no keyword that suppresses a finding from prose; see
`docs/decisions/0002-documented-gaps-registry.md` for why the earlier one was
removed. `EXCLUDE` and `FOREIGN_PATHS` in the checker cover documents received
from elsewhere, whose references describe another repository.

When adding a check, prefer one that compares two artifacts over one that
inspects a single artifact. Every defect in this round was a disagreement, not
an error.

## Things that look like defects and are not

- **The `specl:` and `spec:` prefix split is correct.** A vocabulary term and an
  instance of it have different lifecycles. What was wrong is the base `spec:`
  expands to, not the prefix itself.
- **Bare item IDs in the markdown bullet position are correct.** Namespacing
  belongs on the emitted IRI. A prefixed identifier in source was requested
  downstream and declined.
- **Warnings accumulating at `draft` is the design.** They are
  production-readiness signals. What was wrong is that some of them were
  unclearable at any amount of authoring effort.

## Style

Section headings are sentences. No em-dashes for sentence flow. State material
impersonally in documentation. Do not estimate work in days.

11. **A green suite says the artifacts agree, not that any of them is right.**
    `specl:owner` was declared a datatype property and emitted a literal for
    eleven releases while every consistency check passed, because the
    declaration and the emission agreed and the declaration was wrong. When a
    check derives one artifact from another, it cannot see a shared mistake.

12. **Claims about the environment need testing in that environment.** Every
    check here compares artifacts inside one container, and several defects
    reached an adopter through that blind spot: repository-relative paths in
    the README, a Python floor CI never ran, a publish workflow contradicting a
    written policy, and text I/O assuming the locale encoding. CI runs Windows
    and Linux across three Python versions because of the last one.

13. **From 1.0, the specification is not yours alone to change.**
    `GOVERNANCE.md` governs the graph contract, the authoring syntax, and the
    commitments register. It deliberately does not govern implementation,
    ergonomics, documentation, or defect fixes, because a process that gated
    those would obstruct the promises it protects.
