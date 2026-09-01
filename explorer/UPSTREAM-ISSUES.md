# Upstream issues against specl

Found during the explorer rewrite. Each is written as an issue body so it can
be submitted as-is after this round of development. Numbered in the order
found; the stage that found it is noted.

## UP-1. Angle-bracketed absolute IRI in a reference key is not treated as an IRI

Found at stage 0, building the `unresolvable-reference` fixture. specl 1.0.0.

```
- R1 Must be verified by something outside this graph.
  - verifiedBy: <https://example.org/tests/nothing-here>
```

emits

```
spec:R1 ... specl:verifiedBy spec:test-2122f9f5 .
spec:test-2122f9f5 a specl:Test ;
    dct:identifier "<https://example.org/tests/nothing-here>" .
```

The same value without angle brackets emits `specl:verifiedBy <https://example.org/tests/nothing-here>` with no minted node. Both spellings are plausible from an author who knows Turtle; only the bare one does what they meant, and the bracketed one keeps the brackets inside the identifier literal. Either strip the brackets and treat the value as an IRI, or warn that the bracketed form is taken literally.

## UP-2. The score's population excludes withdrawn items and does not say so

Found at stage 1, comparing counts. `specl-validate score` reports 109 items for a graph carrying 111 item-class individuals. The two missing are the requirements carrying `itemStatus: withdrawn`. The exclusion is correct. It is not stated in the score output, the README, or anywhere a consumer could read it, so a second tool computing over the same graph gets 111 and the two disagree.

This is the same class of defect as the explorer's own maturity figure (DEF-1), from the other side. Relevant to the published maturity definition (S3): R5.7 in the explorer specification requires a displayed figure's definition to state its exclusions, and the definition cannot say what the CLI does not publish.

## UP-3. No machine-readable statement of the grammar

Found at planning, needed by stage 9. The annotation key map, the context-sensitive keys, the reference-valued keys and their ranges, the section-to-class map with prefixes, the mappable classes, the prose sections, the front-matter keys and the section markers are module-level data in `spec_to_rdf.py`. Per-class expectations are `sh:message` strings in `shapes.ttl`. A consumer wanting the grammar has to import the module. Requested: a CLI subcommand (or a committed, CI-regenerated artifact) emitting all of it as one JSON document stamped with the specl version and graph contract. The explorer's syntax reference is generated from it; an editor or highlighter (OQ9 in the explorer specification) would want the same document.

## UP-4. The validation report shape is undocumented

Found at planning, needed by stage 8. `specl-validate validate --json` emits `{status, results: [{severity, focus, path, message}]}`. The shape is exactly what a consumer needs and nothing says it is stable. Requested: document it as a consumed interface, so the explorer (and anything else) can attribute findings to items by focus node without coupling to an internal detail.

## UP-5. Repeated predicates carry no order in the graph, and the emitter has one

Found at stage 1. An item with several `acceptance:` lines emits several `specl:acceptanceCriterion` triples. The markdown order is meaningful to the author (first criterion, second criterion) and the graph cannot express it, so any consumer reading through an RDF library gets an arbitrary order. The explorer's parser preserves file order because it reads the Turtle text directly, which is a property of the parser rather than of the graph. Not necessarily a defect; worth a line in the downstream commitments stating that emission order is source order and that consumers reading the graph through a library should not rely on it.

## UP-6. `specl-validate score` has no machine-readable output

Found at stage 7. `score` prints text. The explorer has a slot for a supplied score (R5.6, so the header shows the CLI's figure rather than its own), and the only way to fill it today is to parse the printed lines. The `validate` subcommand already has `--json`; `score` should have the same, emitting the dictionary `score_graph` already builds (`score`, `clean`, `total`, `subscores`, `progress`, `gate_failed`, `status`, `violations`, `warnings`).

## UP-7. A validation report does not say which graph it is about

Found at stage 8. `validate --json` emits `{status, results}`. Nothing in it identifies the specification it was run against, so a consumer handed a report and a graph separately cannot tell whether they belong together. The explorer currently detects the case where no result's focus resolves in the loaded graph and reports it, which catches a wrong report and misses a stale one. Requested: the specification IRI (and, if cheap, a hash of the graph) in the report header.

## UP-8. Shape expectations live only in SHACL; the grammar generator has to reverse them

Found at stage 9, a sharper form of UP-3. The generator in `explorer/build/grammar.py` recovers per-class expectations by walking `shapes.ttl` and parsing the SPARQL text of `sh:target` selects with regular expressions to find the class and the conditions (`FILTER EXISTS { ?any a ... }`, status filters). That works for the current shapes and will break the first time a target is written differently. If specl owns the grammar artifact (UP-3), it can state the conditions as data beside the shapes rather than leaving a consumer to recover them from SPARQL text.
