# A graph view in the spec explorer: cost against benefit

## What was measured

`@g3-toolkit/core` 1.0.0 and `@g3-toolkit/react` 1.0.0 from npm, installed with their peers and bundled with esbuild in production mode. Graph shapes measured with the explorer's own parser and index over two real specifications.

| Bundle | Minified | Gzipped |
| --- | --- | --- |
| `@g3-toolkit/core` with the RDF adapter, SHACL, k-hop, shortest path, components, centrality | 129 KB | 31 KB |
| Cytoscape alone | 444 KB | |
| `core` + React + react-dom + Cytoscape + the view layer | 2,216 KB | 703 KB |
| The explorer as it stands today | 186 KB | 47 KB |

`core` is ESM-only with seven runtime dependencies (graphology, dagre, d3-force, d3-hierarchy, expr-eval, simple-statistics, graphology-communities-louvain). `react` adds eight peers: React, react-dom, Cytoscape, cytoscape-fcose, zustand, ECharts, vis-timeline, vis-data.

## What the specification graph actually looks like

The question a graph view answers is whether the structure is worth seeing. Excluding `partOf`, `rdf:type`, `conformsTo`, `wasDerivedFrom` and list cells, which say the same thing about every item:

| | Nodes | Semantic edges | Edges per node | Isolated | Largest component |
| --- | --- | --- | --- | --- | --- |
| specl explorer spec | 114 | 25 | 0.22 | 78 (68%) | 7 |
| ODT console spec | 157 | 95 | 0.61 | not measured in detail | |

The explorer's own specification has 25 semantic edges of two kinds, `affects` (20) and `role` (5). Its median degree is zero, 68% of items connect to nothing, and it falls into 89 components of which 78 are single nodes. The ODT console specification is better connected at 0.61 edges per node, and almost all of that is `role` on user stories, which is a five-way fan from the personas rather than a web.

A node-link canvas over this is 78 dots in a field with a small constellation to one side. There is no cluster structure for Louvain to find, no long path for path analysis to trace, and nothing a force layout can reveal that the "Referenced by" section does not already state exactly.

## Cost

**The single-file constraint is the binding one, not the size.** R1.1 requires no external runtime dependency, R1.5 forbids a bundler, transpiler or module loader, and D5 states that capabilities requiring a build step are supplied to the explorer rather than implemented in it. Every route to a Cytoscape canvas breaks at least one:

- Inline the 2.2 MB bundle into the HTML. One file, no network, and it needs a bundler to produce, so R1.5 goes. The file becomes twelve times its current size and the reader waits on 2.2 MB of parse before first paint, which is the property R1.4 was restated to protect.
- Load from a CDN. R1.1 and R10.2 go, and with them the air-gapped case and P5.
- Ship a second file beside the explorer. R1.1 goes, and the attestable single artifact with it.

**The parser problem returns.** `core` reads RDF through `SparqlAdapter` or an ingest path; the explorer holds a parsed model of its own. Feeding one from the other means a second representation of the same graph kept in step, which is the class of duplication D2 and D7 exist to prevent.

**A React island in a file with no framework.** The explorer is imperative DOM with no state library. Mounting a React tree with zustand beside it gives two state models to keep consistent, on the tab strip, the selection and the fragment.

## Benefit, honestly stated

For the specifications this tool reads, a canvas would show what the detail view already says. The capabilities in `core` that would genuinely add something are not the ones that need a canvas:

- **k-hop neighbourhood** around a selection. Real value: what does this decision touch, and what touches those. At a maximum degree of 4 this is a handful of nodes.
- **Shortest path** between two items. Answers "how does D2 reach R5.6" without clicking through.
- **Components and isolates.** 78 items in the explorer's own specification are connected to nothing. That is a finding about the specification, and nothing in the tool currently says it.

All three are graph algorithms over 114 nodes and 25 edges. Each is under thirty lines against the index that already exists. None needs a layout engine, a canvas, or a library.

## What is worth doing

**In the explorer, no dependency.** Three additions worth their weight:

1. An "isolated" chip beside clean and not clean: items that neither reference nor are referenced by anything, excluding the structural predicates. This is the gap-finding the tool exists for and it needs no drawing.
2. A neighbourhood section on the detail view: the items within two hops, grouped by direction. The forward and backward lists already exist; this joins them and goes one step further out.
3. A path lookup in the filter bar: two identifiers, the chain between them or a statement that none exists.

Together they deliver the discovery value at roughly 100 lines and no change to R1.1, R1.5 or D5.

**Outside the explorer, g3-toolkit properly.** The served mode already proposed under OQ8 is where a Cytoscape view belongs: a bundler exists, React is affordable, and the toolchain is present. That mode is also where a graph view earns its keep, because it can hold a specification family rather than one document. Cross-specification `dependsOn`, `upstreamOf` and `refines` over several specifications is a graph with structure worth laying out, and it is exactly what `specl-validate layering` checks with no viewer.

**One piece of `core` is worth borrowing on sight.** `ShaclValidator`, `reportFromValidationResults`, `reportFocusNodes`, `severityOverlays` and `summarizeValidation` cover the same ground as the explorer's R12 findings work and the readiness estimate. Not to embed, but as a second implementation to check the explorer's estimate against: if g3 and specl and the explorer all agree on a graph, that is stronger evidence than the explorer agreeing with specl alone.

## Recommendation

No graph view in the single-file explorer. The constraint that forbids it is the same one that makes the artifact worth having, and for specifications this sparse the view would show less than the text does.

Add the three graph-derived capabilities above with no dependency. Put the Cytoscape view in the served mode, aimed at specification families rather than single documents, where the structure justifies the layout and the build step is already paid for.

If a canvas is wanted for a single specification anyway, the cheapest honest route is a separate g3-toolkit application that reads the same `spec.ttl`, kept out of the explorer entirely. That costs nothing the explorer has to carry and can be as heavy as it likes.
