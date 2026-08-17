# Nested content under an item

**Status:** proposed, implemented ahead of confirmation. Applies to 0.3.0.

## Context

An indented bullet under an item was always read as an annotation, so the format
could not express a nested content list. `R6.2` in `specl_explorer` used one to
enumerate field ordering per type. All four lines parsed as failed annotations
and were discarded, and the requirement reached the graph as a description
ending in a colon.

That was recorded as P18 and deferred on the grounds that the fix is a format
change belonging in a designated breaking release. That reasoning was wrong.
`docs/DOWNSTREAM-COMMITMENTS.md` reserves breaking releases for IRI changes and
property range changes. Adding a property and emitting triples where none were
emitted before is additive and needs no break.

The real obstacle is different and narrower. The motivating lines are
syntactically indistinguishable from mistyped annotations: `Requirement:
description, priority` has the same shape as `priorty: MUST`. Any rule that
admits the first as content admits the second, which would convert a caught typo
into a silent one. That is the defect class this project exists to eliminate, so
the rule has to separate them on something other than shape.

## Decision

**A known annotation key is an annotation at any depth.** `docs/SYNTAX.md`
specifies two or more spaces, so specifications authored at four columns must
keep working. This clause is what makes the change backward compatible: no line
that parses as an annotation today changes meaning.

**Everything else splits on column. Four or more is content, below that is a
probable typo and warns.** Four columns is the second markdown nesting level. An
author indenting that far has already said the line is a child of the annotation
level rather than a member of it. Only lines that warn today change behavior,
and only those at four columns or deeper.

**Nested lines emit as an `rdf:List` of string literals in source order, with
IRI-named cells.** Order is why the content was written as a list, so it has to
survive as structure rather than inside a string.

The cells carry derived IRIs (`<item>-detail-1`, `-2`) rather than blank nodes.
Turtle's `( )` collection syntax produces unlabeled blank nodes whose labels are
regenerated on every parse, and `_req_map` in `validate_spec.py` compares
stringified objects, so a list-bearing requirement reported as modified against
itself on every run. Parsing one file twice produced two different node labels
and a spurious diff. `_req_map` now expands lists, which is the correct fix
regardless, and the named cells mean identity is stable across parses, merges,
and reserialization. Every node in an emitted graph remains an IRI.

**The property is not declared a subproperty of `skos:note`.** The SKOS
documentation-note family is the right precedent for what this property means,
and defining a specialization is the documented SKOS extension pattern, adopted
in this neighborhood by OMG's Commons Annotation Vocabulary, which declares
`dct:description` as `rdfs:subPropertyOf skos:note`. The obstacle is that the
SKOS documentation properties are annotation properties, and OWL DL forbids an
annotation property from carrying property axioms, including subproperty,
domain, and range declarations. Asserting the subproperty alongside
`rdfs:range rdf:List` puts the vocabulary in OWL Full, which is where SKOS
itself sits for the same reason.

The lineage is recorded with `rdfs:seeAlso skos:note` and an `rdfs:comment`
stating why the axiom is absent. A reader looking for the pattern finds it, the
range constraint keeps doing real work, and the vocabulary stays in DL.

`R6.2` in `specl_explorer` is restored to its original nested form and now
translates clean, which is the demonstration that the recovery is real rather
than a reworded description.

## Alternatives

**Fuzzy-matching unknown keys against the known set** to tell a typo from
content. Rejected. It replaces a clear rule with a guess, and the guess is
wrong precisely on the motivating case, where the unknown key is a class name
that resembles nothing in the annotation vocabulary.

**Requiring a marker,** such as a different bullet character for content.
Rejected. It is invisible to a markdown reader and no author would discover it.

**One `specl:detail` literal per nested line.** Rejected on ordering. RDF does
not order multiple objects of one property, and the enumeration this exists to
carry is ordered.

**A single literal holding the lines newline separated.** This was the first
implementation. Rejected because a literal cannot become a list later without a
range change, and a range change waits for a designated breaking release. The
cheap form is only cheap if structure is never wanted.

**`rdf:Seq` with `rdf:_1`, `rdf:_2`.** Rejected. The RDF container vocabulary
has open, weak semantics with no closure, and practice has moved away from it.

**The Ordered List Ontology, with indexed slots.** Rejected. It expresses the
same thing `rdf:List` already expresses, at the cost of a dependency on a
low-adoption vocabulary.

**A bespoke index property on each line node.** Rejected. It reinvents list
traversal in terms no consumer already knows, where `rdf:rest*/rdf:first` is
understood by every RDF tool and by rdflib's `Collection` directly.

**Declaring `rdfs:subPropertyOf skos:note` and accepting OWL Full.** A real
option rather than a bad one. It would let a consumer find specl detail by
querying notes generically across vocabularies, which has more value here than
usual given the downstream consumer federates across sources. Rejected because
the cost is permanent and the benefit is speculative.

**Concatenating nested content into the description.** Rejected. It is what a
human had to do by hand as the workaround, and it loses the distinction between
the requirement's statement and its elaboration.

**Deferring to a breaking release.** Rejected. The change is additive, and the
parser is already being reworked in 0.3.0 for P16 and P7, so folding this in
costs one pass rather than two.

## Consequences

`core.ttl` gains `specl:detail` as an `owl:ObjectProperty` with
`rdfs:range rdf:List`, plus the `rdf:` and `skos:` prefixes. `shapes.ttl` gains
no requirement: nested content is optional everywhere.

`validate_spec.py` expands lists before comparing, so `diff` is correct before
anything emits one.

The property name and its range are the durable pieces. Removing a property or
changing a range is a break, so both hold until 0.11.0.

Nested content attaches to the item, not to the annotation it sits under. A
four-column bullet below a `priority:` annotation is content of the item. That
is a simplification and is stated in `docs/SYNTAX.md` rather than left to be
discovered.

P18 is closed. Specified as R1.8 in `specs/specl_tool/spec.md` before the code
changed.
