<!--specl: parked, a verbatim archive of a document received from elsewhere-->

# Request to specl — component identity for a multi-specification project

From: the g3-toolkit track, 2026-08-18.
Concerns: `LIMITATIONS.md`, "One entity across several specifications becomes
several nodes", and `docs/ROADMAP.md`, "Multi-specification projects and
component identity", deferred to 2.0.

## Intake

This is a request as received, not a disposition. It is written to enter
specl's existing downstream-request path: recorded alongside
`docs/proposals/0002a-downstream-requests-as-received.md`, decided in the
disposition proposal, and given `UR` identifiers in `specs/commitments/spec.md`
only if and as accepted. Disposition is specl's call, so nothing here is
pre-formatted as a commitment.

## When the answer is needed

Before Step 3 of the g3-toolkit specification brief, which is drafting the
parent specification. Steps 1 and 2, the identifier plan and the capability
inventory, proceed regardless and are where the exposure list below will be
counted precisely. A decision arriving after Step 3 costs g3t a migration
rather than a design choice; a decision of "no" arriving before it costs
nothing at all.

## What prompted this

g3-toolkit is about to become a specification family: a parent specification
plus per-package peers, with `g3t-routing-001` joining as the first peer. The
family structure itself works on 0.11.0 as shipped. `references:`,
`dependsOn`, `upstreamOf`, and `specl-validate layering` all do what the
family needs, and item-to-item references across specifications resolve
correctly against a declared foreign base.

One thing does not work, and it is the one recorded as deferred.

## The specific exposure

`constrains` and `verifiedBy` mint their nodes under the referencing
specification's own base. In a family split by package, most components are
named by exactly one specification and never hit this. A minority are named by
several:

- The geometry document, produced by layout and consumed by rendering, hit
  testing, metrics, and the Cytoscape emission path.
- The metrics module, which supplies quality gates to more than one area.
- The test suite, since a test exercising an integration is legitimately named
  by both specifications it spans.

Those become two or three unrelated nodes each, and traceability across the
family becomes string matching, which is what the RDF was there to replace.

Personas and agents are not part of this request. `role:` and `owner:` are
reference-valued and resolve a `PREFIX:ID` token against a declared base, so
declaring them once in the parent and referencing them from peers already
gives one node per entity. `LIMITATIONS.md` states that shared personas and
agents have the same spec-local minting property, which is true only of the
naive approach and reads as though no path exists. That sentence is worth
qualifying.

## The question, and it is a timing question

The roadmap says the fix is likely a front-matter map from a component name to
a project-controlled IRI, in the manner of `references:`, that the mapping
mechanism itself is additive, and that what breaks is a project adopting it
after the fact, because doing so moves every component IRI it has.

g3-toolkit has published no component IRIs. Its family has not been written.
`g3t-routing-001` exists but is unreleased, still carries a placeholder
`spec_base`, and is being reworked to join the family regardless.

So for this project the migration cost of that feature is currently zero, and
it rises the moment the family is drafted. This is the cheapest moment in the
whole timeline to adopt it, and it will not come again.

The roadmap also says the feature should be designed against a real
multi-specification project rather than invented, and that fixing it properly
needs such a project to exist. That project now exists and is asking.

## What is requested, in priority order

**Q1. A decision on whether the component map can land before the g3t family
is drafted.** Not a request to break the batching policy: the roadmap
describes the mapping mechanism as additive, and the breaking part is the
migration a project with existing IRIs would face. g3t has none. If the answer
is yes, g3t drafts against it and pays nothing. If no, g3t proceeds without it
and accepts a 2.0 migration, which is a defensible answer and should be given
plainly rather than left open.

**Q2. Whether g3-toolkit should be adopted as the design partner for the
feature.** The roadmap names the absence of a real multi-specification project
as the reason the design cannot be settled. g3t can supply the shape of the
problem before it writes the specifications, which is more useful than
supplying it afterwards: the exposure list above is derived from a real
package structure rather than a hypothetical one, and the family split is
still adjustable if the design wants it adjusted.

**Q3. Whether any interim is sanctioned.** Two candidates, and the request is
for a ruling rather than a preference:

- A CURIE in `constrains` or `verifiedBy` resolving against a prefix declared
  under `references:`. The resolution path appears to accept this today, since
  the CURIE branch precedes the node-minting branch, but `references:` is
  documented as naming peer specifications, and a prefix pointing at a
  component namespace is not a peer. If this works and is not intended to,
  saying so is more useful than leaving it discoverable.
- An absolute IRI in the same position. This does not currently work: the
  `http`-prefixed branch sits inside the vocabulary path, and `CURIE_RE` does
  not match a URL, so an absolute IRI falls through to being minted as a
  hashed local node. If accepting absolute IRIs in reference-valued keys is
  additive, it may be a smaller change than the full map and enough to hold
  the line until 2.0.

**Q4. If none of the above, confirmation that duplication is the accepted
answer for now**, so the g3t inventory can record each duplicated entity
deliberately rather than treating it as a defect to be reported repeatedly.

## What g3t will do either way

Proceed. Blocking a specification family on a 2.0 feature costs more than the
duplication does, and the exposure is a minority of components rather than
most of them. The family will be split by package specifically to keep it
that way, and each duplicated entity will be listed in the capability
inventory so the count is known rather than discovered during a migration.

The request is for a decision with a date attached, not for the feature.
