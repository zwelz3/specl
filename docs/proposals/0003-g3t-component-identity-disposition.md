# Disposition: g3-toolkit component identity request

Request as received: `docs/proposals/0003a-g3t-component-identity-as-received.md`, from the g3-toolkit track, 2026-08-18.

Four questions, answered in order. The short version: the capability g3t needs ships now, the abbreviation for it still waits for 2.0, and the framing that separated those two was wrong in this repository's own documents.

## What the request got right that the roadmap had wrong

`docs/ROADMAP.md` described the component map as expected to break things, on the grounds that a project adopting it moves every component IRI it has. That is true of a project that has already minted local hashed nodes. It is not a property of the feature.

The map is an abbreviation. Underneath it, a shared component is an IRI that several specifications name, and if a project writes that IRI in full there is nothing to abbreviate yet and nothing to move later. Adopting the map afterwards replaces `constrains: https://g3t.example/components#geometry-document` with `constrains: geometry-document` and resolves to the same IRI, so no node moves and no consumer migrates.

The deferral was therefore protecting against a migration that only exists for projects which start by minting locally. The request found this by asking whether the timing could change, and the honest answer is that the timing was never the constraint.

## Q1. Can the component map land before the g3t family is drafted?

**The map, no. What it provides, yes, and it has shipped.**

Absolute IRIs are now accepted in reference-valued keys. `constrains` and `verifiedBy` previously matched a CURIE or fell through to minting a node, and an absolute IRI matched neither branch: it was hashed into a local `component-<digest>`, discarding the identity the author supplied. It is now used as written.

Three specifications naming `https://g3t.example/components#geometry-document` produce one node. Verified against a three-specification family before this was written: one component node, one test node, three requirements reaching the component by traversal.

This is additive. Nothing that parsed before parses differently, except a value that was being silently hashed and is now honoured, which no project can have depended on.

The map itself stays in 2.0, because it is front-matter syntax and a governed change, and because there is now no urgency: a project using absolute IRIs today loses nothing by waiting for the shorthand.

## Q2. Should g3-toolkit be the design partner?

**Yes, and the request has already done most of it.**

The roadmap says the design needs a real multi-specification project, and naming a real exposure list is the part that could not be invented: a geometry document consumed by four areas, a metrics module supplying gates to several, and a test suite legitimately named by both specifications it spans. That third case is the one that would have been missed, because a test spanning an integration looks like a duplicate rather than a shared entity.

What is useful before 2.0 is not more argument but evidence: how verbose absolute IRIs turn out to be in practice, how many distinct shared entities the family actually has once counted, and whether the map wants one namespace per project or per category. Those are answerable by drafting the family and reporting, which g3t is going to do anyway.

## Q3. Are the two interims sanctioned?

**The CURIE interim works, is not sanctioned, and now warns.**

A prefix declared under `references:` does resolve in `constrains`, exactly as the request suspected, because the CURIE branch precedes node minting. It also pins `specl-validate layering` to inconclusive with exit 3 forever, because layering reads a declared reference as a peer specification and a component namespace is not one. Confirmed rather than reasoned about: the probe returned `SHARED: peer not readable at <no path declared>` and exit 3.

Leaving that discoverable was the wrong state. A `constrains` or `verifiedBy` value resolving against a reference that declares no path now warns and names the absolute IRI as the alternative.

**The absolute IRI interim is the sanctioned answer, and is no longer an interim.** See Q1.

## Q4. Is duplication the accepted answer?

**No.** It was the accepted answer for as long as there was no alternative, and there is one now. The capability inventory should record shared entities by their IRI rather than as duplications to be migrated later.

## What this costs

Verbosity. `constrains: https://g3t.example/components#geometry-document` is long, and a family naming a dozen shared components will feel it. That is the whole reason the map exists, and it buys nothing else.

One thing to watch and report: an absolute IRI is unchecked. A typo in one is a valid IRI naming a node nothing else references, exactly like the vocabulary-term case, and `specl-validate layering` has no path to check it against. If the family accumulates enough of them for that to bite, the map should carry a path the way `vocabularies:` does, so a declared component namespace can be validated. That is a design input for 2.0 and worth recording as it happens rather than at the end.

## Commitments minted

`UR23` and `UR24` in `specs/commitments/spec.md`. The map itself is not committed, because it is 2.0 work whose shape is still open.

## Corrections noted in passing

Both were raised by the request and both were right.

`LIMITATIONS.md` said shared personas and agents have the same spec-local minting property. They do not: `role:` and `owner:` are reference-valued, so a CURIE against a declared base already yields one node per entity, and the sentence read as though no path existed.

`docs/SYNTAX.md` described cross-specification references as arriving in 0.5.0, in the future tense, five releases after they arrived.
