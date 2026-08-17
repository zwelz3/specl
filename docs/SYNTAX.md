# specl markdown syntax

Reference for the spec format consumed by `specl-translate`.

## Front-matter

A spec begins with a YAML block delimited by `---`:

```markdown
---
spec_id: myproject-001
title: My Project
version: 0.1.0
status: prototype
---
```

`status` must be one of `draft`, `prototype`, `review`, `production`.
The status drives the CI gate: Warnings fail the build only at
`production`.

Additional spec-level metadata can go in a `<!--specl -->` comment
block anywhere in the document:

```markdown
<!--specl
created: 2026-01-15
-->
```

## Sections

H1 headings delimit structured sections. Recognized section names and
the class they produce:

| Section | Class | ID prefix |
|---------|-------|-----------|
| `# Intent` | (folds into Specification) | — |
| `# Purpose` | (folds into Specification) | — |
| `# Requirements` | Requirement | `R` |
| `# User Stories` | UserStory | `US` |
| `# Open Issues` / `# Open Questions` | OpenIssue | `OQ` |
| `# Decisions` | DecisionRecord | `D` |
| `# Design Considerations` | DesignNote | auto-hash |
| `# Comments` | Comment | auto-hash |

## Front matter

`spec_base` is required. It is the namespace this specification's items are
identified under, and it must be one the project controls. specl never invents
a base on a project's behalf.

```yaml
---
title: Excel Service
spec_base: https://example.org/specs/excel_service#
prefix: XLSVC
spec_id: xlsvc-001
version: 0.1.0
status: draft
---
```

The base must end in `#`, must carry a path segment rather than being a bare
authority, and must have no fragment beyond the terminator. Slash-terminated
bases are unsupported until a post-1.0 extension. A value failing any of these
is rejected and no graph is written, because the value would have become a
permanent identifier and repairing one silently is the wrong default.

Item IRIs are the base concatenated with the identifier token verbatim, not RFC
3986 relative resolution, so a dotted identifier such as `R2.1` is safe under
any base. The Specification itself is the base without its terminating `#`.

`prefix` is the short name another specification will use to reference this one.
It is carried in the graph from 0.3.0 and unused until cross-specification
references arrive in 0.5.0, so that the value is stable before the feature
depends on it.

`item_prefix` declares the prefix this specification's own item identifiers
carry, in place of the reserved one its section would otherwise require. Two or
more uppercase letters, and never one of `R`, `US`, `OQ`, `D`, `DN`, `C`, `Q`.
It is accepted in every item section, so one numbering sequence can span
requirements and decisions, which is what a register of commitments needs.

Do not confuse it with `prefix`, which is how another specification refers to
this one.

`spec_id` is optional and is emitted as `dct:identifier`. It is not part of any
IRI.

## Splitting a specification across files

```yaml
companion_files:
  - requirements.md
  - decisions.md
```

Paths are relative to the root file. A companion carries sections and no front
matter of its own: one specification has one identity, declared in the root, and
a `spec_base` in a companion would be a second answer to a settled question. It
is ignored with a warning.

Sections merge in declared order, and prose sections concatenate, so a split
specification reads as one and translates to the same graph as the equivalent
single file. The only difference is provenance, which necessarily differs: each
item names the file it came from and the line within that file.

A companion that does not exist is refused rather than warned about. A
specification missing part of itself is a different specification.

Documents are identified by path relative to the root, so a companion in a
subdirectory sharing a basename with the root does not collide with it, and no
identifier depends on the working directory.

## Sections the map does not know

A heading the translator does not recognize warns and names itself, rather than
dropping its content in silence. Two ways to resolve one.

Map it onto a class the vocabulary already declares:

```yaml
sections:
  Constraints: Requirement
```

Or park it, when no class models it yet:

```
# Verification Notes
<!--specl: parked, no class models this yet-->
```

Parking is the pre-adoption path. Author the content in its final shape now, and
adoption becomes deleting the marker rather than rewriting the section.

## Acceptance queries

```
# Acceptance Queries

- Q001 Every persisted record survives a restart.
  - gates: R8, R9
```

`gates` is comma-split and resolves to IRIs, so a query gating an identifier the
specification does not declare warns like any other reference. A query gating
nothing warns too: it verifies nothing.

## Governing a vocabulary term

A requirement often constrains something in an ontology the project implements
rather than a component it builds. Declare the vocabulary and point at the term:

```yaml
vocabularies:
  cga:
    base: https://w3id.org/cagel/ns#
    path: ./vocab/cga.ttl
```

```
- R1.1 Each holon must thread through four named-graph layers.
  - constrains: HolonicDataset
  - governs: cga:Holon, cga:LayerRole
```

`governs` and `constrains` are different claims and stay separate.
`constrains` names a software component and keeps `specl:Component` as its
range, which is what makes it checkable; `governs` names a term in a vocabulary
this project does not own and declares no range at all. Writing a vocabulary
term under `constrains` warns and names the right key.

`governs` never falls through to the identifier grammar, so `governs: R2` is not
a reference to a requirement called R2. An absolute IRI works without declaring
anything.

When a vocabulary declares a local `path`, `specl-validate layering` checks that
each governed term is defined there. That is where a typo hides best, since a
misspelled class name is still a perfectly valid IRI.

A base must end in `#` or `/`, or a term concatenated onto it would run into the
last path segment.

## Cross-specification references

A foreign prefix is declared in the referencing specification's own front
matter. There is no registry: the specification that uses a prefix is the one
that declares it.

```yaml
references:
  SBL:
    base: https://spec.example.org/sibyl#
    path: ../sibyl/spec/sibyl-spec.ttl
dependsOn: SBL
```

A `PREFIX:ID` token in a reference-valued field resolves to that base
concatenated with the identifier. A prefix the specification does not declare
warns and stays a literal, because guessing a base mints a wrong IRI. A foreign
base goes through the same grammar as `spec_base`, since it becomes part of an
IRI this specification emits.

`dependsOn`, `refines`, and `upstreamOf` each name a declared prefix.
`upstreamOf` says the peer is downstream, so referencing its items is a layering
violation.

`specl-validate layering spec.ttl` checks those references. It never touches the
network: a peer is read from its local path or not read at all. Three outcomes,
with distinct exit codes, because a peer nobody could read must never become a
silent pass.

| Outcome | Exit | Meaning |
| --- | --- | --- |
| pass | 0 | every reference points at a declared item in a peer that is not downstream |
| violation | 1 | a reference points into a specification declared downstream |
| inconclusive | 3 | a peer was unreadable, or does not declare the referenced item |

## Bullets and sub-bullets

Items live under structured sections as bullets with an ID prefix:

```markdown
- R1.1 The library MUST do the thing.
  - priority: MUST
  - constrains: ComponentA, ComponentB
  - acceptance: Given X, when Y, then Z.
  - verifiedBy: tests/test_thing.py::test_it
```

Sub-bullets are indented two or more spaces (or a tab) under the parent
bullet. Each sub-bullet matches the pattern `- key: value` where `key`
is one of the recognized annotation keys.

### Multi-value annotations

Two mechanisms, used for different purposes:

### Reference-valued keys

`affects`, `constrains`, and `verifiedBy` are object properties and resolve to
IRIs rather than literals. A value is handled one of three ways.

A token matching the identifier grammar resolves against the base by
concatenation, and warns if no item in the specification declares it. The IRI is
still emitted, so a dangling reference is visible in the graph rather than
silently absent.

A CURIE such as `SBL:D14` is illegal until cross-specification references arrive
in 0.5.0. It warns and stays a literal, because there is no prefix map yet and
guessing one would mint a wrong IRI. A pytest node id such as
`tests/test_a.py::test_b` carries colons and is not a CURIE.

The declared range is enforced. `constrains` points at a `specl:Component` and
`verifiedBy` at a `specl:Test`, so an identifier naming an item in the same
specification warns: resolution tries the identifier grammar first, and
`constrains: R1` would otherwise put a requirement where the ontology reserves a
component.

Anything else names an external artifact and becomes a typed node,
`specl:Component` for `constrains` and `specl:Test` for `verifiedBy`, carrying
the original value as `dct:identifier`. Its IRI is derived from the value,
readable when the value is safe as a local name and hashed when it is not. One
node per artifact however many items reference it.

**Comma-split** (atomic identifier keys: `constrains`, `affects`):

```markdown
  - constrains: HolonicDataset, HolonicStore, Backend
```

produces three separate `specl:constrains` triples.

**Multiple sub-bullets** (prose keys: `acceptance`, `verifiedBy`, or
any key where commas appear naturally in the value):

```markdown
  - acceptance: Given a fresh dataset, when add_holon is called, then iri appears in list_holons.
  - acceptance: Given an existing holon, when add_holon is called again, then the duplicate is rejected.
```

produces two separate `specl:acceptanceCriterion` triples, with commas
inside each value preserved.

## Annotation key reference

| Key | RDF property | Classes | Multi-value |
|-----|--------------|---------|-------------|
| `priority` | `specl:priority` | Requirement | single |
| `title` | `dct:title` | all item classes | derived from the description when absent |
| `acceptance` | `specl:acceptanceCriterion` | Requirement, UserStory | multiple sub-bullets |
| `verifiedBy` | `specl:verifiedBy` | Requirement | multiple sub-bullets |
| `constrains` | `specl:constrains` | Requirement | comma-split |
| `capability` | `specl:capability` | UserStory | single |
| `itemStatus` | `specl:itemStatus` | all item classes | `active`, `superseded`, `withdrawn` |
| `supersededBy` | `specl:supersededBy` | all item classes | item reference, resolves to an IRI |
| `role` | `specl:role` | UserStory | identifier of a declared persona |
| `prefLabel` | `skos:prefLabel` | Persona | single |
| `altLabel` | `skos:altLabel` | Persona | multiple sub-bullets |
| `benefit` | `specl:benefit` | UserStory | single |
| `owner` | `specl:owner` | any item | identifier of a declared agent |
| `recommendation` | `specl:recommendation` | OpenIssue | single |
| `status` | `specl:resolutionStatus` or `specl:decisionStatus` | OpenIssue / DecisionRecord | single |
| `rationale` | `specl:rationale` | DecisionRecord | single |
| `affects` | `specl:affects` | DecisionRecord | comma-split |

### The four things called status

`status` is the most overloaded word in the format, and the four uses are
unrelated. Documented rather than split, because splitting the annotation key
would rename properties in every existing specification and only a designated
breaking release may do that.

| Where | Property | Values | Question it answers |
| --- | --- | --- | --- |
| front matter | `specl:status` | `draft`, `prototype`, `review`, `production` | how strictly should this specification be gated |
| `status:` on a `D` item | `specl:decisionStatus` | `proposed`, `accepted`, `superseded`, `rejected` | where is this decision in its lifecycle |
| `status:` on any other item | `specl:resolutionStatus` | `open`, `in-review`, `resolved`, `deferred` | has this question been answered |
| `itemStatus:` on any item | `specl:itemStatus` | `active`, `superseded`, `withdrawn` | is this item still live |

A fifth, `implementation:`, deliberately avoids the word: it maps to
`specl:implementationStatus` and answers how much is built.

`decisionStatus:` and `resolutionStatus:` are accepted directly from 0.11.0 and
are preferred: they say which property they mean, so a bullet moved between
sections does not silently change what it asserts. `status:` remains accepted and
still resolves by class, because removing it would break every existing
specification for no gain.

## Backward compatibility

Sub-bullets are entirely optional. A spec with no sub-bullets produces
exactly the same RDF it would have in specl 0.1.x. Teams can
adopt annotations incrementally.

## Parser warnings

Every translation prints parser warnings to stderr with no flag
required: unrecognized annotation keys, sub-bullets with no parent,
ID prefix mismatches. Translation still succeeds and the output file
is written, because reading the emitted graph is how the cost of a
dropped line is seen.

`specl-translate spec.md spec.ttl --fail-on-warning` writes the
output and then exits non-zero if anything warned. CI and the
pre-commit hook use it, so a warning in a published specification
fails the build.

`--strict` is accepted for compatibility. It selected the warning
printing that is now unconditional, so it changes nothing.

A warning is worth reading rather than silencing.

## Agents

An owner is accountable for something, so it is an entity rather than a name:

```
# Agents

- AG1 The platform team, accountable for storage decisions.
  - prefLabel: Platform team

# Open Questions

- OQ1 Whether to embed the store.
  - owner: AG1
```

`specl:Agent` is a subclass of `prov:Agent`, and `specl:owner` has `prov:Agent`
as its range, so an agent declared in another vocabulary resolves too. As with
`role:`, the value is an identifier and a name in that position warns.

## Personas

A role is an entity many stories share, so it is declared once and referenced by
identifier:

```
# Personas

- P1 The person who reconciles invoices at month end.
  - prefLabel: Finance clerk
  - altLabel: accounts clerk

# User Stories

- US1 As a finance clerk, I want invoices as PDFs, so that I can archive them.
  - role: P1
```

`role:` takes an identifier, never a name. Minting a persona from the surface
string would make `finance clerk` and `Finance Clerk` two personas with nothing
reporting it, and fragmentation you cannot see is worse than a reference you
have to declare. A name in that position warns, and so does an identifier no
persona declares.

Surface forms live on the persona as `skos:prefLabel` and `skos:altLabel`, so
wording varies without the identity moving.

`capability` and `benefit` remain literals by decision rather than oversight.
They are prose specific to one story, not entities anything else refers to.

## Retiring an item

An identifier is never reused and an item is never deleted. Retiring one means
marking it and naming its replacement:

```
- R1 The original requirement.
  - itemStatus: superseded
  - supersededBy: R2
- R2 The replacement.
```

`supersededBy` is an item reference and resolves to an IRI like `affects` does,
so a supersession pointing at an identifier the specification does not declare
warns. An item marked `superseded` with nothing named warns too: the reader is
otherwise left with a retired identifier and no way to find what took its place.

Absent `itemStatus` means active. A chain of any length is traversable with
`specl:supersededBy+`.

A retired item is still emitted and still readable, and the shapes stop
evaluating it, so it accumulates no warnings about annotations it will never
gain. A successor must be the same class and belong to the same specification;
following a chain should not land the reader somewhere answering a different
question.

`withdrawn` is the no-successor case: struck rather than replaced, so naming a
successor on a withdrawn item warns. A withdrawn identifier is permanently
reserved. Reuse is only visible across two graphs, so `specl-validate diff`
reports it and exits non-zero.

## Nested content

An indented bullet naming a known annotation key is an annotation at
any depth. Anything else at four or more columns is nested content,
and anything else below that warns as a probable typo.

```
- R6.2 Type-specific fields must render in a sensible order:
    - Requirement: description, priority, acceptance criterion
    - UserStory: description, as a, I want, so that
```

Those lines emit as an `rdf:List` of literals on `specl:detail`, in
source order:

```turtle
spec:R6.2 specl:detail spec:R6.2-detail-1 .
spec:R6.2-detail-1 rdf:first "Requirement: ..." ; rdf:rest spec:R6.2-detail-2 .
spec:R6.2-detail-2 rdf:first "UserStory: ..."   ; rdf:rest rdf:nil .
```

It is an ordinary RDF list, so `specl:detail/rdf:rest*/rdf:first`
retrieves every line and rdflib's `Collection` reads it directly. The
cells carry derived IRIs rather than blank nodes, so identity survives
parsing, merging, and reserialization.

`specl:detail` follows the SKOS documentation-note pattern and carries
`rdfs:seeAlso skos:note`. It is not a subproperty of `skos:note`,
because that property is an annotation property and OWL DL forbids
annotation properties from carrying the range axiom this one needs.

Content attaches to the item rather than to the annotation it sits
under, so a four-column bullet below a `priority:` annotation is still
content of the item.

## Pinning the vocabulary and shapes

Both graphs are published at versioned locations addressed by graph contract
rather than by release:

| Current | Versioned |
| --- | --- |
| `https://w3id.org/specl/ns` | `https://w3id.org/specl/ns/1` |
| `https://w3id.org/specl/shapes` | `https://w3id.org/specl/shapes/1` |

The contract changes only in a designated breaking release, so there are two of
each across the whole run to 1.0. `owl:versionIRI` carries the contract and is
what a consumer pins; `owl:versionInfo` tracks the package version and is
informational.

Pinning the contract is not byte pinning. A contract 1 document gains classes
and properties in most releases, which the batching policy permits: what it may
not do is change an IRI or a property's range. A consumer needing exact bytes
should vendor a copy.

## Provenance

Every item records the document and line it was authored on:

```turtle
spec:R1.1 prov:wasDerivedFrom spec:source-e9e453bf ;
    specl:sourceLine 19 .
```

The line indexes the file as authored. Front matter and comment blocks are
blanked rather than removed during parsing so the numbering survives.

The source document is identified by file name rather than by the path given on
the command line, so a graph does not differ because it was translated from a
different working directory.

`--generated-at ISO8601` records a `prov:Activity` with that timestamp. It is
supplied rather than read from the clock. Translation is a pure function of its
source, and a translator that reads the clock produces different bytes on every
run, which breaks the byte-identical guarantee and every golden file with it.
The same reasoning applies to anything else derived from the environment rather
than from the source.

## Measurement

Three different questions, deliberately separate.

| Concept | Question | Source of truth |
| --- | --- | --- |
| Maturity | How completely is this specified? | SHACL findings per item |
| Progress | How much of it is built? | `implementation:` per item |
| Verification coverage | How much is demonstrated? | not yet modelled |

`implementation:` takes `not-started`, `in-progress`, `implemented`, or
`verified`. Progress rolls up from items rather than being declared for the
specification, which is what makes it honest. Marking something built changes
progress and does not change maturity.

Maturity is priority weighted: a clean MUST contributes more than a clean COULD,
and an unclean MUST costs more than an unclean WONT. An open issue that is still
open is never clean, so a specification cannot report full maturity while
carrying unanswered questions.

`specl-validate score --history history.ttl` appends the assessment as a
`specl:MaturityAssessment`, a `prov:Activity` carrying the score, the progress,
and a per-class breakdown. Appending is opt-in, so a run that only reports does
not accumulate a log. `badge --history` renders the latest recorded assessment
rather than scoring afresh.

## Shapes

Every subcommand that takes a shapes graph defaults to the one bundled with the
package, so `specl-validate validate spec.ttl` works from an install with no
checkout. Pass a path to use your own.
