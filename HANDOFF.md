# Handoff

Start here, then [CLAUDE.md](CLAUDE.md) for the invariants, then [GOVERNANCE.md](GOVERNANCE.md) before changing anything the specification promises.

## What specl is

An RDF-native, SHACL-validated specification format. Markdown in, Turtle out, validated against a shapes graph whose severity gate tightens when a specification declares itself production-ready. Four command-line tools translate, validate, score, diff, migrate, and check a SHACL processor for the features these shapes need.

## Where things stand

**1.0.0, released 2026-08-19.** The first published release since 0.2.0: everything between was tagged and not published, under `docs/decisions/0007-internal-releases-until-1.0.md`.

**The contract is contract 2**, declared by `dct:conformsTo` in every emitted graph and described in `docs/contracts/2.md`. Contract 1 remains published and fetchable, and `specl-migrate contract` moves a graph between them. Graphs predating both are covered by `NAMESPACE-MIGRATION.md`.

**Identifiers resolve.** `https://w3id.org/specl/ns`, the versioned vocabulary and shapes copies, both contract descriptions, and specl's own three specifications all dereference through w3id.org.

## What changed at 1.0, and it is not a feature

From this release the author does not change the specification unilaterally. Substantive changes are collected in a window that closes 2027-08-19 and ship together as 2.0; additive changes land whenever they are ready. `GOVERNANCE.md` is the mechanism and `docs/proposals/OPEN.md` is where pending proposals are listed against that shared date.

What is *not* governed matters as much: implementation, ergonomics, documentation, and fixes that bring behaviour into line with what the specification already says. A process that gated defect fixes would obstruct the promises it exists to protect.

## Reading order for the rest

`docs/SYNTAX.md` is the format reference and the longest document here. `LIMITATIONS.md` is what specl does not do, collected for someone deciding whether to adopt. `docs/REMAINING.md` is what is left, with nothing blocking 1.0.

`docs/decisions/` holds ten accepted records. Read `0006-artifact-agreement-strategy.md` before adding any check: it is the inventory of every pair of artifacts that can disagree, and it carries the reasoning about why some of them drifted anyway.

`docs/proposals/` holds the downstream request path. A request arrives archived verbatim as `NNNNa`, is decided in `NNNN`, and mints `UR` identifiers in `specs/commitments/spec.md` only for what is accepted. That register is itself a specl specification, validated and scored in CI.

## What to be careful about

**Every check in this repository compares artifacts to each other.** That is blind to a claim that is wrong outside the container, and several defects reached an adopter that way: repository-relative paths in the README, a Python floor CI never exercised, a publish workflow contradicting a written policy, and text I/O assuming the locale encoding. CI now runs Windows and Linux across three Python versions for that reason. When a claim depends on an environment, test it in that environment.

**A green suite says the artifacts agree, not that any of them is right.** `specl:owner` held a literal for eleven releases while every consistency check passed, because the declaration and the emission agreed and the declaration was wrong.

**The changelog is not a plan.** Entries are written when a release is tagged. The 0.3.0 section was written ahead of the work and read afterwards as a record, and four of its entries describe things that never shipped or were later reversed; one was a promise made to a downstream consumer in exchange for declining their request, which then sat unshipped for eight releases.
