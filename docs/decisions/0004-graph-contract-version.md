# The Specification node and the emitted graph contract

**Status:** accepted. Applies to 0.3.0. Supersedes an earlier draft that
introduced a separate document node.

## Context

`docs/ROADMAP.md` commits 0.3.0 to emitting a graph-contract version so a
consumer can ask what it is holding. Answering that requires knowing which node
carries it, which turns out to be the same question as what the Specification
node is once every specification has its own base.

Both parts of the answer are fixed until 0.11.0, since a node's IRI and a
property's range may only change in a designated breaking release.

An earlier draft answered by minting a second node, `specl:SpecificationDocument`,
at the base without its terminator, and putting a bespoke
`specl:graphContractVersion` integer on it. Checked against how OWL ontologies
handle the same problem, that answer is wrong in both halves.

## What the precedent is

OWL distinguishes three IRIs. The **ontology IRI** names the intellectual
artifact and is the subject that carries metadata. The **version IRI**, linked by
`owl:versionIRI`, names one snapshot. The **document IRI** is the physical
location a client fetches from, and OWL deliberately gives it no RDF identity.

For a hash namespace the ontology IRI is the namespace minus its terminator.
SKOS asserts `<http://www.w3.org/2004/02/skos/core> a owl:Ontology` while its
terms are fragments under `.../core#`. OBO Foundry ontologies follow the same
shape and place snapshots at dated release paths.

`src/specl/core.ttl` already does this. Its first statement is
`<https://w3id.org/specl/ns> a owl:Ontology`, base minus hash, carrying
`owl:versionInfo`. The pattern the earlier draft declined is the one this
project's own vocabulary uses.

Metadata that a second node was supposed to hold goes on the ontology node under
the precedent. Creation time, creator, prior version, and version string sit
together and are distinguished by predicate rather than by subject. Modularity
is `owl:imports`, one ontology importing others, each with its own IRI, rather
than one ontology spread across several document nodes.

## Decision

**The Specification node is the base without its terminating hash.** For a
specification based at `https://w3id.org/specl/tool/spec#`, the Specification is
`https://w3id.org/specl/tool/spec` and its items are fragments under it. There
is no second node and no `specl:SpecificationDocument` class.

**`spec_id` stops being an identifier component.** It has no structural role
once the base determines the Specification IRI, so it becomes optional and is
emitted as `dct:identifier` when present. Existing values stay meaningful as
labels: `specl-tool-001`, `explorer-001`.

**The contract is declared with `dct:conformsTo`, not a bespoke property.**

```turtle
<https://w3id.org/specl/tool/spec>
    a specl:Specification ;
    dct:conformsTo <https://w3id.org/specl/contract/1> ;
    dct:identifier "specl-tool-001" ;
    dct:title "..." ;
    dct:hasVersion "..." ;
    specl:status "prototype" .
```

`dct:conformsTo` is the standard property for asserting that a resource follows
an established standard, and DCAT profiles use it for exactly this. Naming the
contract with an IRI rather than an integer makes it dereferenceable to a page
saying what contract 1 guarantees, and 0.11.0 emits `contract/2`. This replaces
the `specl:graphContractVersion` datatype property, which the earlier draft
would have added.

**Nothing else is stamped.** No tool version, no timestamp, no host. Exit
criterion 6 for 0.3.0 is that translating twice produces byte-identical output,
and a value that changes with the release or the clock defeats that and every
golden-file comparison the test suite depends on. Provenance is 0.7.0's subject
and attaches to the Specification node.

**Snapshot IRIs are deferred.** The `owl:versionIRI` analogue, a distinct IRI
per released version of a specification, is not emitted in 0.3.0. It is additive
whenever it lands and does not need a breaking release.

## Alternatives

**A separate document node,** as the earlier draft proposed. Rejected. It gives
RDF identity to the document, which is the single thing the precedent declines
to do, and its two supporting arguments do not survive contact with that
precedent. Provenance is not a reason for a second node, since OWL hangs
creation metadata on the ontology node. Two versions on one node is not a
problem, since an ontology carries several version-related properties at once
and RDF distinguishes them by predicate.

**Keeping `spec_id` in the IRI,** so the Specification is `<base>specl-tool-001`.
Rejected. The ordinal identifies nothing once one base means one specification,
and it would sit inside a permanent IRI until 0.11.0. It also leaves the base
without its terminator unoccupied, which invites a second node later.

**A bespoke `specl:graphContractVersion` integer.** Rejected in favor of
`dct:conformsTo`. A standard property a consumer already knows how to query
beats a new one, and an IRI can explain itself while an integer cannot.

**Stamping the contract in a Turtle comment.** Rejected. A comment is not
queryable, and a tool that produces an RDF graph should record its claims in
that graph rather than beside it.

**Splitting the specification across document nodes for 0.9.0 multi-file
support.** Rejected in advance. The precedent handles modularity with
`owl:imports`: one specification importing modules, each with its own base. That
needs no document node.

## Consequences

`core.ttl` gains no class and no property. `shapes.ttl` gains no requirement,
since a hand-authored graph should not be forced to declare conformance.

`specl-migrate iris` maps two things by different rules. Items move by
concatenation, old base plus token to new base plus token. The Specification
node moves from `<legacy base><spec_id>` to the new base without its terminator,
which is not a token substitution and needs its own case in the tool.

One w3id rule is added for `^contract/1/?$`, redirecting to `docs/contracts/1.md`
in this repository. The rule and the page are prerequisites for shipping 0.3.0,
not follow-ups, because the IRI is emitted into every graph. Both are written;
the rule is in `tools/w3id/specl.htaccess` awaiting the upstream pull request.

`docs/decisions/0003-self-spec-instance-base.md` is amended: the bases in its
table now determine the Specification IRI as well as the item IRIs.

Two adjacent gaps are recorded rather than fixed here. `core.ttl` carries
`owl:versionInfo "0.1.0"` while the package is at 0.2.x, which is a fourth
version string in the reconciliation problem 0.3.0 already tracks. And
`shapes.ttl` has no ontology header at all, so the shapes graph is unversioned
and unidentified, which blocks the commitment to publish it at versioned
locations.
