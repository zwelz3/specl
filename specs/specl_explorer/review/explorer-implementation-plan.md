# specl Explorer implementation plan

## Scope

This plan implements the specification as it stands after review round 3b: 74 requirements, 5 user stories, 5 personas, 7 decisions, 9 design notes and 9 open questions, validating with zero violations at 94% maturity. Everything lands in one release. The sequence below is build order rather than delivery phasing, so nothing here ships to a user until the last stage completes.

Revised on re-review, 30 August 2026. The first version assumed the explorer would be built and hosted through the specl Python package. It does not have to be, and the revision below removes that assumption: the explorer is a static file with its own toolchain, and specl supplies it inputs as files rather than as a runtime. Every place that changed is marked *revised*.

Work items are named by requirement identifier throughout. Where a stage depends on something outside the explorer, the specl-side item is named as `S<n>` and listed in its own section.

## Which release this belongs to

specl's governance since 1.0 splits changes three ways. Additive changes, which leave every existing graph valid, land whenever they are ready. Substantive changes, which cost an adopter a migration, are collected in a window that closes a year after 1.0 and are released together as 2.0. Implementation, ergonomics and documentation are not governed at all.

Classifying this work against that split produces an uncomfortable result.

| Work | Class under specl governance |
| --- | --- |
| The explorer rewrite in full, including every defect in DEF-1 to DEF-10 | Implementation and ergonomics, ungoverned |
| The syntax reference and its generator | Ungoverned, plus an additive introspection surface (S1) |
| `specl explore` compose command | Additive |
| Documented shape for the validation report | Additive, a promise rather than a change |
| Published maturity definition (PR4) | Additive if it documents what `specl-validate score` already computes |
| Hosted distribution channel (PR1, R1.3) | Additive |
| Keeping the explorer in the distribution (R1.6) | No change |

Nothing in this plan touches the graph contract. No emitted IRI moves, `dct:conformsTo` stays at contract 2, and no adopter has a migration to perform. On specl's own terms, none of it requires the 2.0 window.

That matters because of what waiting costs. DEF-3 and DEF-4 lose content silently, DEF-1 reports a figure that contradicts the CLI, and governance states explicitly that a defect fix does not need permission. Holding those behind a window that exists to batch migrations delays them by up to a year for no governance reason.

The recommendation is to take this as a major effort on the 1.x line and reserve the 2.0 window for changes that actually cost a migration. If the release is targeted at 2.0 regardless, for coherence or because the explorer and its self-referential example move together, the sequence below is unchanged; only the tag differs. The target version is a parameter of this plan and not an assumption inside it.

## This is a rewrite

Stages 1 through 4 touch nearly every line of the current file. The parser's output shape changes under R2.8, so every consumer of it changes. The selection model changes under R4.7. The rendering path changes under R4.8 and R3.6. What survives from the shipped file is the drag-and-drop handling, the CSS custom properties, and part of the highlighting expression.

DN5 of the current specification already set this precedent for the previous generation, on the same reasoning. Treating this as a patch series would mean writing renderers against the old property shape and rewriting them one stage later.

The consequence for verification is the reason this matters. A rewrite cannot be checked by diffing behaviour against the previous build, because the previous build is wrong in the specific ways the rewrite exists to fix. The fixture set is the only safety net, which is why it is stage 0 rather than an afterthought.

## Toolchain (revised)

The explorer has no dependency on Python at build time, test time or run time.

**Where it lives.** An `explorer/` directory at the repository root, holding the source file, the fixtures, the harness and the build script. The copy under `src/specl/explorer.html` is a build output that CI places there so the distribution carries it under R1.6; nothing in the package builds it.

**Source.** `explorer.html` itself is the source, not the product of one. R1.5 as amended permits a generation step for embedded reference data and nothing else, so the file is authored directly and the build only fills slots. Each slot is a `<script type="application/json">` element with an identifier: the grammar for the syntax reference, the embedded example, and the optional validation report and score. An empty slot means the capability reports itself unavailable, which is the behaviour R12.1 requires.

**Build.** A single Node script with no dependencies. It reads the slot inputs as files, fills the slots, and writes the built file. The inputs are produced by whatever produces them: the specl CLI in CI, or by hand. The build does not import specl and does not need it installed.

**Harness.** Plain Node with `node:assert`, no dependencies. The parser and index are written so they touch no DOM, and the harness extracts the script from the HTML, evaluates it in a bare context, and runs the fixtures through the resulting functions. The same harness runs the current shipped parser through the fixtures to produce the stage 0 before-state record.

**Inputs from specl, as files.** The graph (`spec.ttl`), the validation report (`report.json`), the score, and the grammar. The first three exist today. The grammar is S1 below, revised to be a JSON artifact rather than a Python accessor.

**Hosting.** The built file on the GitHub Pages site the repository already publishes. The release artifact is the same file. R1.3's identity check is a byte comparison in CI between the pages copy, the release asset and the packaged copy.

**Compose.** The compose command in S4 is defined by the slot contract rather than by a language: anything that can write JSON into the named slots can compose the explorer. A specl CLI subcommand is the obvious host because it already has the translator, validator and scorer in hand, but the inlining itself is a few lines any tool can carry.

## Stage 0. Fixtures and harness

Nothing else starts until a specification exists that exercises the conditions the current build fails on. The explorer's own specification is the demonstration under R9.4 and is not adequate as a test: it contains no unresolvable reference, no unrecognised class, no alternative labels, and no contract mismatch.

The fixture set covers, at minimum:

| Condition | Requirement | Source |
| --- | --- | --- |
| Three values on one predicate | R2.6 | Generated |
| Sub-bullets producing an `rdf:List` | R2.7 | Generated |
| Two terms from different namespaces sharing a local name | R2.8 | Hand-authored |
| A class the explorer does not represent | R2.9 | Hand-authored |
| A malformed statement among valid ones | R2.4 | Hand-authored |
| A contract version the explorer does not implement | R2.10 | Hand-authored |
| A reference resolving to nothing in the graph | R6.6 | Generated, absolute IRI |
| A persona whose `skos:altLabel` differs from its title | R4.5 | Generated |
| An item carrying no title | R4.2 | Hand-authored |
| A specification with zero requirements | R5.5 | Generated |
| A specification with no items | R9.3 | Generated |
| A file with no specification individual | R9.2 | Hand-authored |
| 500 items | R10.1 | Generated |

Hand-authored fixtures must carry a comment stating that they are deliberately not translator output, or the next person to see them will regenerate them and delete the condition under test.

Exit criterion: every fixture loads in the current build and the failure each one provokes is recorded. That record is the before state the rewrite is measured against.

## Stage 1. Parser and model

Lands R2.3, R2.4, R2.6, R2.7, R2.8, R2.9, R2.10.

R2.8 goes first within the stage, because keying properties by full IRI changes the data structure every later stage reads. R2.6 and R2.7 change the shape of a property value from a scalar to a collection, which is the second structural change and belongs in the same pass.

R2.9 is the stage's own reporting surface and needs somewhere to render before the interface is rebuilt. A placeholder banner is sufficient at this point; it acquires its final form in stage 4.

Exit criterion: the stage 0 fixtures load, and for each one the parsed model contains what the file contains. Every condition the parser cannot represent appears in the R2.9 report rather than in the console.

## Stage 2. The reference index

Lands DN7.

An index from IRI to item, built once after parsing. Reference navigation, backlinks, unresolved-reference marking and finding attribution all read from it, and building it as a distinct step is what keeps those four from each carrying their own resolution logic.

Exit criterion: for the fixture containing an unresolvable reference, the index distinguishes a reference that resolves from one that does not, before any interface consumes it.

## Stage 3. The selection model

Lands R3.3, R4.6, R4.7, R4.9, R7.6, and R8.2 and R8.3 as the specification view. Withdraws R7.2 and R8.4.

This is the reported issue and the change that motivated the review. It depends on stage 1 only for the specification being available as an item alongside the others.

R4.9 belongs here rather than with the presentation work because the defect it fixes is a property of how selection is applied. Rebuilding the list on selection is what destroys focus, and the selection model is where that decision is taken.

Exit criterion: every selection including the specification presents the same tab set, both tabs address the selected item, a loaded file paints with the specification selected, and a keyboard user can select a row and then move to the adjacent one.

## Stage 4. Presentation

Lands R3.6, R4.2, R4.3, R4.8, R6.1, R6.2, R6.3, R6.5, R6.8, R7.3, and the final form of the R2.9 report.

R4.8 and R4.2 together replace the description preview with the title, which is the change a reader notices first. R3.6 and R4.3 remove the reliance on colour, which is verified by rendering in greyscale rather than by inspection.

Exit criterion: the interface is legible with no colour applied, every item shows its title, absent properties are marked as absent, and provenance resolves to a document and a line.

## Stage 5. Filter

Lands R4.5.

Depends on stage 1 for SKOS labels being parsed and on stage 4 for the row having a defined shape to attach matched text to. The third criterion, showing the text that caused a match where the row does not display it, is the part that needs the row to exist first.

Exit criterion: a term appearing only in an alternative label lists the item, and the row states why.

## Stage 6. Navigation

Lands R6.6, R6.7, R11.1, R11.2.

Depends on stage 2 for the index and stage 3 for the selection model. R11.2 depends on R11.1, since a trail entry is a selection and tab, which is what a fragment encodes.

Exit criterion: every reference-valued property in the explorer's own specification reaches its target in one action, an unresolvable one is marked, a copied address restores the same selection and tab, and returning from a followed reference is one action.

**A release could be cut here.** At the end of stage 6 the tool fixes every verified defect except DEF-1, resolves the reported issue, and is a materially better artifact than the shipped one. Stages 7 onward add capability and depend on decisions taken outside the explorer. If the target version question above resolves toward not waiting, this is the natural boundary.

## Stage 7. Measurement

Lands R5.2, R5.6, R5.7, R5.8, R5.9, R6.4, R8.1.

Gated on S3. The explorer cannot stop holding its own definition of maturity until there is a published one to defer to.

R5.8 admits two mechanisms, opening the population in the item list or reporting its members. The item list already narrows under stage 5, so opening is cheaper for counts and reporting is the natural form for R5.9's ranked contributors. Both are permitted and the criterion tests obtainability rather than the route.

Exit criterion: the figure in the header equals the figure the CLI reports for the same graph, or states that it is estimating and names its definition. Every count reaches the items behind it. The contributors to a shortfall are obtainable in order of contribution.

## Stage 8. Findings

Lands R12.1, R12.2.

Gated on S2. Depends on stage 2, since findings attach to items by focus node.

Exit criterion: with a report supplied, items carrying findings are marked in the list and their findings appear in the detail view. With no report, findings are reported as unavailable rather than as absent.

## Stage 9. Syntax reference

Lands R1.5 as amended, R13.1, R13.2, R13.3, R13.4.

Gated on S1. Independent of stages 2 through 8, so it can proceed in parallel with them if that suits, but it is placed here because R13.3 shows which keys the selected item's class accepts and which it lacks, which needs the detail view from stage 4 and the absence markers from R6.3.

Exit criterion: every annotation key the translator accepts appears in the reference, no key it does not accept appears, the reference states the specl version and contract it was generated from, and it renders with no network access.

## Stage 10. Composer

Lands R13.5, R13.6.

Depends on stage 9 for the tables. R13.5 is a constraint on the implementation as a whole and is verified by inventory rather than by behaviour.

This is the stage most exposed to OQ8. If the open question resolves against composition in this artifact, the stage is dropped and nothing before it is disturbed, which is why it sits here rather than earlier.

Exit criterion: the implementation contains no parser for specl markdown, and a composed item emits markdown carrying the section heading, the identifier prefix and the keys its class accepts, marked as unvalidated.

## Stage 11. Packaging, distribution and the embedded example

Lands R1.3, R1.4 as amended, R1.6, R9.4. Depends on S4, S5, S6.

The embedded example is this specification's own emitted graph, so it must be produced after every other stage has settled the specification it is generated from. Producing it earlier means producing it twice.

R1.3 and R1.6 read as being in tension and are not. R1.3 permits the explorer to leave the Python distribution; R1.6 requires a command that composes the explorer to resolve a local copy without a fetch. If the compose command lands, the distribution stays the simplest way to satisfy R1.6, so the practical outcome is that the file remains in the package and the hosted channel is added beside it. No consumer of the current package path breaks.

Exit criterion: the explorer is obtainable from every published channel, the files are identical, a reader with no toolchain can obtain one, the compose command works with no network egress, and the embedded example matches the current emitted graph.

## Carried requirements

Eighteen requirements are unchanged by the review and are named in no stage above, because the stages are organised around what changed. A rewrite reimplements them all, so they are assigned here rather than left to be noticed at the end.

| Requirement | Stage |
| --- | --- |
| R2.1 file input and drag-and-drop, R2.2 parser sufficiency, R2.5 raw text retained | 1 |
| R7.1 item statement block, including the derived nodes the old extraction dropped | 3 |
| R3.1 header, R3.2 sidebar, R3.4 independent scrolling, R3.5 tokens at `:root` | 4 |
| R4.1 grouped list with counts, R4.4 natural sort within a group | 4 |
| R5.1 title, version and status in the header | 4 |
| R7.4 highlighting by an inline function, R7.5 monospace with horizontal scroll | 4 |
| R9.1 empty state, completed at stage 11 when the embedded example exists | 4 |
| R5.3 figure and bar, R5.4 colour thresholds as named constants | 7 |

R8.2 and R8.3 are in stage 3 as content of the specification view. R8.3's counts become obtainable at stage 7 under R5.8, so the requirement is satisfied across two stages and only fully verified at the second.

## Stage 12. Non-functional verification

Verifies R1.1, R1.2, R10.1, R10.2, R10.3, R10.4.

These are properties of the finished file and cannot be verified before it exists. R10.1 uses the 500-item fixture. R10.2 is verified by observing a full session including load, filter, selection, navigation, reference and export. R10.3 is verified by operating the tool from load to export with no pointer.

Exit criterion: all six hold on the built file in Chromium, Firefox and Safari, from removable media, with network access blocked.

## specl-side work

Each item is named by the stage it gates.

**S1. Grammar as a JSON artifact (revised).** Gates stage 9. The grammar is currently module-level data in the translator: the annotation key map, the context-sensitive keys, the reference-valued keys and their declared ranges, the section-to-class map, the mappable classes, the prose sections, the front-matter keys and the section markers. Per-class expectations are the messages on the bundled shapes. specl emits all of this as one JSON document, stamped with the specl version and contract, through a CLI subcommand or as a committed artifact regenerated in CI. The explorer's build consumes the JSON and never reaches into Python. R13.2 then holds because the JSON is regenerated from the same tables the translator runs on.

**S2. Documented shape for the validation report.** Gates stage 8. `specl-validate validate --json` already emits severity, focus, path and message per result. Documenting that shape turns it into something the explorer may consume; leaving it undocumented means the explorer is coupled to an internal detail.

**S3. Published maturity definition.** Gates stage 7, and D2 is unimplementable without it. The shape-based, priority-weighted figure over all item classes is the better of the two candidates and should be published as the definition, with the explorer's offline fallback documented as an approximation of it.

**S4. The compose command (revised).** Gates stage 11. Translates, validates, scores, and writes a copy of the explorer with the results in its slots. Lives in the specl CLI because that is where the translator, validator and scorer already are; the composition itself is the slot contract from the toolchain section and is not specific to that host. Resolves the explorer locally under R1.6.

**S5. Distribution channels (revised).** Gates stage 11. The built file on the existing GitHub Pages site, as a release asset, and in the distribution. A CI check that the three are byte-identical for a release.

**S6. Build wiring for the self-reference (revised).** Gates stage 11. In CI, in order: translate the explorer's specification, validate it, score it, run the Node build with those outputs as slot inputs, then compare the embedded example against the graph just emitted and fail on divergence. The circularity is real, since the file contains a graph describing the file, and the comparison is what keeps it honest. The Python steps produce files; the build consumes them; neither knows about the other.

## Open decisions that gate work

| Decision | Gates | Consequence if unresolved |
| --- | --- | --- |
| S3, the published maturity definition | Stage 7 | Stage 7 does not start; DEF-1 stays open |
| OQ8, how far authoring goes | Stage 10 | Stage 10 is dropped, nothing else moves |
| OQ9, whether specl wants a shared parser | Nothing in this plan | Stage 1 proceeds with the parser this artifact needs |
| OQ7, whether P5 collapses into P2 | Nothing until stage 12 | Tested at stage 12, when the raw view and R2.9 reporting both exist |
| Owners for nine open questions | Nothing | Nine warnings remain; the specification does not reach clean |

The last row is the only outstanding item in the specification itself. It is an accountability decision rather than a drafting task.

## Definition of done

- The specification translates with no parser warnings and validates with no violations, and the only remaining warnings are the open-question owners if those are still undecided.
- Every stage exit criterion holds.
- Every stage 0 fixture produces the behaviour its requirement states, and the hand-authored fixtures still carry their comments.
- The header figure and the CLI figure agree on any file, or the header states that it is estimating.
- The embedded example matches the emitted graph, and the build fails if it stops matching.
- The file is obtainable from every published channel and the copies are identical.
- The six non-functional properties hold in three browsers, offline, from removable media.
