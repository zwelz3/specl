# specl Explorer Improvement Plan

## Scope

This plan covers `explorer.html` as shipped in specl 1.0.0, the reported defect in which the Summary tab addresses a different subject than the tabs beside it, the defects found while verifying that report, and the patterns worth importing from the ODT Operational Console specification (ODTC 0.1.0).

Every change is expressed as a change to the explorer's `spec.md` first. The explorer is the artifact where a specl toolchain visibly declining to use its own method would be most damaging.

## Verification basis

All findings below were reproduced rather than read out of the source.

| Check | Result |
| --- | --- |
| `explorer.html` in the specl 1.0.0 wheel vs the reviewed file | Byte-identical (md5 `4279f0285a3ef6deb72aa4532cc0f6df`) |
| `specl-translate spec.md spec.ttl` on the explorer's own spec | 492 lines, 0 parser warnings |
| Individuals emitted | 47 Requirement, 6 OpenIssue, 5 UserStory, 5 DesignNote, 1 SourceDocument, 1 Specification |
| Explorer parser run against that Turtle | 64 items parsed, 63 renderable in the sidebar |
| `specl-validate score spec.ttl` | Maturity 8% (5/63 items clean, priority weighted), Progress 0% |
| Explorer maturity bar on the same file | 0% |
| Requirements carrying `priority`, `acceptance`, `verifiedBy` or `constrains` | 0 of 47 |
| Proposed changes in Part 4 applied to `spec.md` and re-translated | 0 parser warnings, 0 SHACL violations |
| `specl-validate score` with all of Part 4 applied and no requirement backfill | Maturity 63% (56 of 106 items clean) |
| Warnings remaining after Part 4 | 42 requirements without acceptance criteria, 8 open issues without an owner |

---

## Part 1. The reported scope defect

### Statement

`Detail` and `Raw Turtle` are scoped to the selected item. `Summary` is scoped to the specification. Three tabs of equal visual weight address two different subjects, and nothing in the interface says so.

### Resolution

The `specl:Specification` is a node in the emitted graph exactly as `spec:R1.1` is. The parser already matches both with the same expression and then diverts the specification into a separate variable. The interface is the only place where the specification is not an item, and that is the whole defect.

The resolution is therefore to make it one:

1. A pinned `Specification` group at the top of the item list, holding one row, above the type groups and exempt from the filter.
2. The header title becomes a control that selects that row, so the discovery path proposed as option 1 in the report survives as a second entry point onto one selection state.
3. A `Specification` entry in the field table (title, status, version, identifier, created, intent, purpose), with the count chips and the maturity figure rendered as part of its detail view.
4. That row is selected on load, which also removes the current dead first paint in which a freshly loaded file shows "Select an item from the sidebar to view its detail."

### One correction to the report

The report proposes that other elements then "show just the two applicable tabs," which implies a tab strip whose size changes with selection. A tab strip that grows and shrinks as the user clicks around costs more attention than the third tab does.

Under the resolution above, no conditional tabs are needed. Every selection, the specification included, carries exactly two. Summary stops being a tab and becomes the detail view of one node. The tab set becomes constant rather than variable, which is a stronger outcome than the one the report asked for.

### Consequence for the existing requirements

R7.2 ("when no item is selected, the tab shows the full raw file") loses the state it describes, because there is no longer a no-selection state after load. The whole-file view stays valuable and needs an explicit control instead. See the proposed R7.6.

---

## Part 2. Defects found alongside the reported one

Ordered by consequence.

### DEF-1. Two maturity figures exist for one file

`specl-validate score` reports 8% (priority weighted, over 63 items, using the bundled SHACL shapes). The explorer reports 0% (unweighted, over 47 requirements, using four property names hardcoded in the script). Both render as authoritative. A reviewer who ran the CLI and a reviewer who opened the HTML disagree about the same artifact and neither has a way to tell which figure is canonical.

This is the defect with the widest blast radius, because the maturity bar is the most prominent element in the interface and the one a non-author is most likely to quote.

### DEF-2. The item count is wrong and the extra item is unreachable

`specl:SourceDocument` is parsed into the item list, counted in "64 total items," given its own chip in the Summary, and omitted from the sidebar because its class is absent from the type table. The CLI counts 63. The chip is a figure that cannot be opened, which is the same failure the reported issue describes in a different form.

### DEF-3. Repeated predicates collapse to the last value

`_emit_item` writes one triple per annotation value, so a requirement with three acceptance criteria emits three `specl:acceptanceCriterion` lines. The parser assigns with `props[k]=v`, so the last value wins and the rest are discarded without notice. Finding gaps is the tool's stated purpose (US1); this silently falsifies the evidence for it.

### DEF-4. Sub-bullet content is dropped entirely

Nested bullets become an `rdf:List` of `{iri}-detail-N` cons cells carrying `rdf:first`. Those cells carry no `a specl:Class`, so the parser skips them, and `detail` is absent from the field table in any case. R6.2 in the explorer's own specification is a one-line heading with four sub-bullets carrying all of its content; the explorer renders the heading and nothing else.

### DEF-5. `dct:title` is parsed and never displayed

Every item carries a title. The sidebar shows a 70-character truncation of the description in its place. Titles were added to the format for exactly this purpose.

### DEF-6. Source provenance is discarded

Every item carries `prov:wasDerivedFrom` and `specl:sourceLine`. Neither is shown. "spec.md:60" closes the loop back to the file the author actually edits.

### DEF-7. The graph contract version is not checked

The specification carries `dct:conformsTo <https://w3id.org/specl/contract/2>`. The explorer neither reads nor reports it. A viewer that silently mis-renders a future contract is worse than one that states it does not recognise the contract it was handed.

### DEF-8. Property keys are resolved by local name

Keys are derived with `pm[1].split(':')[1]`, so `dct:title` and a hypothetical `specl:title` would occupy one slot with the later one winning. No collision exists in contract 2. The mechanism that would produce one silently is already in place.

### DEF-9. Keyboard navigation breaks on first use

`render()` rebuilds the item list on every selection, so DOM focus is destroyed the moment the user presses Enter on a row, and the arrow keys then do nothing. The tab strip declares `role="tablist"` with no `role="tab"` and no `aria-selected`. R10.3 is nominally satisfied and practically is not.

### DEF-10. Unescaped file content reaches `innerHTML`

Item identifiers and the specification title are interpolated into markup without escaping. The risk is low for a locally authored file and is not zero for the stated use case of inspecting Turtle received from elsewhere before feeding it downstream (US3).

---

## Part 3. Patterns adopted from the ODT Operational Console

ODTC specifies a large multi-user surface over a live federated graph. The explorer is a single static file over one translated document. Most of ODTC does not transfer. A specific set of its principles transfers cleanly and cheaply, because both tools present a graph to a reader who did not write it.

### Adopted

| ODTC | Principle | Explorer application |
| --- | --- | --- |
| US2 | An aggregate figure opens the population it counts | Summary chips and the maturity figure become controls that filter the item list to their members |
| R1, R1.1 | Every displayed figure has a retrievable derivation | The maturity figure states what it counted, over what population, with what exclusions |
| R5, R5.1 | A composite score declares its components, weights and their provenance | The explorer stops holding a private definition of maturity (DEF-1) |
| R6 | A metric definition is resolvable at the point of display | The definition is reachable from the figure itself |
| US4 | Contributors to a depressed dimension are ranked by contribution | The maturity figure opens the items that reduce it, worst first |
| DN1 | Truncation is reported as an exact count, a lower bound, or an explicit unknown; silence is excluded | Anything the parser cannot represent is reported in the interface (DEF-2, DEF-3, DEF-4) |
| R20 | An unreachable participant is named and the result marked incomplete | Unrecognised classes and unparsed statements are named rather than logged to the console |
| US22 | Every entity named on a page resolves to that entity's own page | Reference-valued properties render as navigable links |
| US24, R13 | Every view has a stable permalink | Fragment addressing for the selected item and tab |
| US25 | Labels are used in presentation, with the underlying term available on request | `dct:title` becomes the display label; the identifier and IRI stay reachable (DEF-5) |
| US27 | The presentation layer is auditable against the graph | Already satisfied by the Raw Turtle tab; the change is to scope it consistently |
| US78 | A session trail is navigable backward and forward | Back and forward across visited items |
| R3, D5 | Representation is encoded through a channel other than colour alone | Type dots are colour-only today and vanish in greyscale, in print, and for a colour-blind reader |
| R24 | Terms are resolved by IRI, and a prefix collision is disambiguated rather than silently bound | Property keys resolved by full IRI (DEF-8) |
| DN11 | Acceptance criteria state what must be obtainable rather than what must be on screen | Adopted as an authoring rule for the explorer specification itself |

### Not adopted, and why

Federation across peer instances, cost and time budgets on query execution, curation and write-back, authorisation at a service boundary, valid time against transaction time, and confidence derivation all assume a live multi-source system with more than one writer. The explorer reads one static file produced by a deterministic translator. Importing any of that machinery would add specification surface with no referent.

Two have a useful residue. ODTC R2 (every view is a bounded query result) has no analogue at document scale, and its consequence for truncation reporting is adopted above. ODTC US20 and US21 (as-of views and temporal difference) reduce, for a file-based tool, to comparing two versions of one specification, which is proposed below as a later capability rather than a temporal model.

### Adopted as an authoring standard rather than a feature

ODTC carries `priority`, `acceptance` and `rationale` on its requirements, `role`, `capability`, `benefit` and `acceptance` on its stories, a Decisions section with `affects`, and open questions that record a disposition and move to `resolved` with the outcome stated. The explorer specification carries none of these on 47 requirements and has no Decisions section at all, which is why it scores 8%.

ODTC is the reference for the house style. Part 4.6 makes the backfill an obligation rather than an aspiration.

---

## Part 4. Proposed specification changes

Identifiers continue the existing grouping in the explorer's `spec.md`. New material is given in specl syntax and is ready to paste.

### 4.1 Changed requirements

**R3.3** currently reads: *A main panel to the right of the sidebar contains tabbed content (Detail, Raw Turtle, Summary).*

Replace with:

```
- R3.3 A main panel to the right of the sidebar contains exactly two tabs, Detail and Raw Turtle, both scoped to the current selection. The tab set does not vary with what is selected.
  - priority: MUST
  - acceptance: Given any selection including the specification, when the tab strip is inspected, then the same two tabs are present and both address the selected item.
  - rationale: A tab strip whose membership changes with selection costs the reader more attention than a constant third tab would. Making the specification selectable removes the need for a variable tab set rather than creating one.
```

**R4.6** currently reads: *Clicking a sidebar item selects it, highlights the row, and updates the main panel. The selection must persist across tab changes.*

Append the default-selection obligation:

```
- R4.6 Clicking a sidebar item selects it, highlights the row, and updates the main panel. The selection persists across tab changes, and the specification row is selected when a file finishes loading.
  - priority: MUST
  - acceptance: Given a loaded file, when the interface first paints, then the specification row is selected and the Detail tab shows its content, and when another row is selected and the tab is changed, then the selection is unchanged.
  - rationale: Defaulting to the specification removes the empty-detail state that currently follows a successful load, in which the tool asks the reader to make a selection immediately after being given a file.
```

**R7.2** currently reads: *When no item is selected, the tab shows the full raw file.* This state no longer occurs. Replaced by R7.6 below.

**R8** as a group is retitled from "Summary Tab" to "Specification View." R8.1 through R8.3 are retained with their content addressed to the specification's detail view. R8.4 ("must render regardless of whether a sidebar item is selected") is withdrawn, since the specification view is now reached by selecting the specification.

### 4.2 New requirements

Parsing and fidelity:

```
- R2.6 A predicate appearing more than once on a subject must be retained as an ordered collection of all its values, and every value must be rendered.
  - priority: MUST
  - acceptance: Given an item carrying three values for one predicate, when its detail view is opened, then three values are shown for that property.
  - rationale: The translator emits one triple per annotation value. Assigning each value over the last discards content the reader has no way to know was there, and it does so in the properties the maturity figure is computed from.

- R2.7 Values held as an rdf:List of derived cons cells must be resolved and rendered in list order as part of the owning item.
  - priority: MUST
  - acceptance: Given an item carrying specl:detail, when its detail view is opened, then every rdf:first value in the list is shown in order under the item that owns the list.
  - rationale: Sub-bullets carry the substance of any item whose top line is a heading. A viewer that drops them renders such an item as an empty label.

- R2.8 Properties must be keyed by the full IRI the prefix resolves to, not by the local name of the term.
  - priority: MUST
  - acceptance: Given two terms from different namespaces sharing a local name, when both are present on one subject, then both are retained and each is attributed to its namespace.
  - rationale: Keying by local name makes a namespace collision resolve silently to whichever term was parsed last. No collision exists under the current contract, which is the reason to fix the mechanism before one does.

- R2.9 Any statement, class or property the parser cannot represent must be reported in the interface with a count and the subjects concerned, and must not be discarded silently.
  - priority: MUST
  - acceptance: Given a file containing statements the parser does not recognise, when it is loaded, then the interface reports how many were not represented and which subjects they belong to.
  - rationale: A viewer that quietly renders a subset of a file teaches the reader that what is on screen is the file. Reporting the shortfall costs one line of interface and is the difference between an incomplete view and a misleading one.

- R2.10 The graph contract version declared by dct:conformsTo must be read and reported, and a contract the explorer does not recognise must be stated as unrecognised before the content is rendered.
  - priority: MUST
  - acceptance: Given a file declaring a contract version the explorer does not implement, when it is loaded, then the declared version is displayed and the rendering is marked as possibly incomplete.
  - rationale: The contract version exists so that a consumer can tell whether it understands what it is holding. A consumer that ignores it converts a detectable mismatch into a silent misreading.
```

Presentation and navigation:

```
- R3.6 Item type and item status must be conveyed through a channel other than colour alone wherever they are displayed.
  - priority: MUST
  - acceptance: Given the interface rendered in greyscale, when a list containing several item types is displayed, then the type of each item remains distinguishable.
  - rationale: The type indicator is currently a coloured dot and nothing else, which conveys nothing in greyscale, in print, or to a reader who does not distinguish those hues. The specification already requires the colours to be themeable tokens, which is the wrong half of the problem to have solved.

- R4.7 The specification must appear as a selectable row in a pinned group at the head of the item list, above the type groups and exempt from the text filter.
  - priority: MUST
  - acceptance: Given a loaded file, when the item list is rendered, then a specification row is present at the head of the list, and when a filter term matching no part of the specification is entered, then the row remains present.
  - rationale: The specification is a node of the graph like every other node. Presenting it as a tab rather than an item was the only place in the interface where that was not true, and it is the source of the scope confusion the tab arrangement produced.

- R4.8 Where an item declares dct:title, the title must be used as its display label, with the identifier shown alongside and the full IRI reachable from the item.
  - priority: MUST
  - acceptance: Given an item carrying a title, when it is shown in the list and in the detail view, then the title is the label displayed and the identifier and IRI are both obtainable.
  - rationale: Titles are emitted on every item for this purpose. Displaying a truncation of the description in their place discards a field the format supplies and produces a worse label than the one available.

- R4.9 Changing the selection must not rebuild the item list, and keyboard focus must survive selection.
  - priority: MUST
  - acceptance: Given focus on an item row, when that row is selected by keyboard and an arrow key is then pressed, then focus moves to the adjacent row.
  - rationale: Rebuilding the list on selection destroys the focused element, so the arrow-key navigation the specification requires stops working at the first keyboard selection.

- R6.6 A property whose value is a reference to another item in the graph must render as a control that selects the referenced item, and a reference that resolves to nothing must be marked as unresolved rather than rendered as text.
  - priority: MUST
  - acceptance: Given an item carrying a reference-valued property, when the value is selected, then the referenced item becomes the current selection; and given a reference with no corresponding subject in the loaded graph, when the item is displayed, then the value is marked unresolved.
  - rationale: Reference-valued properties are IRIs under the current contract. Rendering them as inert text presents a graph as a set of disconnected records and leaves the reader without the one capability the format exists to provide.

- R6.7 An item's detail view must list the items that reference it, grouped by the property through which the reference is made.
  - priority: SHOULD
  - acceptance: Given an item referenced by two others, when its detail view is opened, then both referring items are listed under the property that names it.
  - rationale: Forward references answer what an item depends on. The question asked more often of a requirement is what depends on it, and the graph already contains the answer.

- R6.8 An item's detail view must state the source document and line it was derived from.
  - priority: SHOULD
  - acceptance: Given an item carrying prov:wasDerivedFrom and specl:sourceLine, when its detail view is opened, then the source document identifier and the line number are shown.
  - rationale: The reader who finds a defect in the explorer fixes it in the markdown. Carrying the line number removes a search from every such correction.

- R7.6 The Raw Turtle tab must offer the whole file as an alternative to the selected item's statement block, and must state which of the two is displayed.
  - priority: MUST
  - acceptance: Given a selected item, when the whole-file view is chosen, then the complete file as loaded is displayed and the view identifies itself as the whole file rather than the item.
  - rationale: The whole-file view was previously reached by having no selection, which the default selection in R4.6 removes. The view is worth keeping and now needs a control of its own.
```

Measurement:

```
- R5.6 The explorer must not compute a maturity figure under a definition of its own. Where a score produced by specl-validate accompanies the file, that figure must be displayed. Where none accompanies it, the explorer must compute the published definition, or must label the figure as an unverified estimate and state the definition it used.
  - priority: MUST
  - acceptance: Given a file accompanied by a score report, when the header is rendered, then the figure displayed equals the figure the report carries; and given a file with no report, when the header is rendered, then the figure is labelled as an estimate and its definition is obtainable.
  - rationale: The explorer currently reports zero for a specification the CLI scores at eight percent, using a different population, a different property set and no weighting. Two authoritative-looking figures for one artifact is worse than one figure with a stated limitation, and the reader has no way to discover which is canonical.

- R5.7 The definition of any figure the explorer displays must be resolvable from the point at which the figure appears, stating what is counted, over what population, and with what exclusions.
  - priority: MUST
  - acceptance: Given any displayed figure, when its definition is requested, then the count, the population and the exclusions are returned.

- R5.8 Every aggregate figure must open the population it counts.
  - priority: MUST
  - acceptance: Given any count or ratio displayed by the explorer, when it is selected, then the item list is filtered to the items the figure counted.
  - rationale: A figure that cannot be opened is a claim the reader has to take or leave. The per-type chips and the maturity ratio are both currently dead ends, and both already know their own membership.

- R5.9 Where a figure reports a shortfall, the items contributing to that shortfall must be obtainable in order of contribution.
  - priority: SHOULD
  - acceptance: Given a maturity figure below one hundred percent, when its contributors are requested, then the items reducing it are listed with the property each is missing, ordered by contribution.
  - rationale: The figure states that work remains. Ordering the contributors states where to start, which is the only action the figure supports.
```

New groups:

```
## R11 Addressing and Navigation

- R11.1 The current selection and tab must be encoded in the document fragment, and opening a fragment must restore that selection and tab against the same file.
  - priority: SHOULD
  - acceptance: Given a selected item and tab, when the address is copied and opened again against the same file, then the same item and tab are restored.
  - rationale: A reviewer citing a requirement currently has to describe where to click. Fragment addressing is local to the document and does not weaken the offline guarantee.

- R11.2 Visited selections must be navigable backward and forward.
  - priority: SHOULD
  - acceptance: Given a sequence of selections, when backward navigation is invoked, then the prior selection and tab are restored.
  - rationale: Following a reference under R6.6 is only useful if returning from it is one action.

## R12 Findings

- R12.1 The explorer must accept a validation report produced by specl-validate alongside the Turtle, and must not implement shape evaluation of its own.
  - priority: SHOULD
  - acceptance: Given a validation report loaded alongside a specification, when it is present, then findings are attributed to items by focus node; and given no report, when the interface is rendered, then findings are reported as unavailable rather than as absent.
  - rationale: The validator already emits severity, focus node, path and message as JSON keyed by IRI. Reimplementing SHACL in the browser would produce a second definition of conformance, which is the failure R5.6 exists to prevent.

- R12.2 An item carrying findings must indicate this in the item list, and must present its findings in its detail view.
  - priority: SHOULD
  - acceptance: Given an item with one or more findings, when the list is rendered, then the item is marked, and when its detail view is opened, then each finding's severity, path and message are shown.
  - rationale: This is the change that moves the tool from displaying what an author wrote to showing what remains to be fixed, which is the reason a reader opens it a second time.
```

### 4.3 New decisions

The specification currently has no Decisions section. The following records the choices this plan makes, so that a later reader finds the reasoning rather than the outcome alone.

```
# Decisions

- D1 The specification is presented as an item in the list rather than as a tab in the panel.
  - title: The specification is an item
  - status: accepted
  - rationale: It is a node of the emitted graph like any other node, and the interface was the only place it was treated otherwise. Making it selectable removes the mixed-scope tab strip without introducing a tab set that varies with selection.
  - affects: R3.3, R4.6, R4.7, R8.4

- D2 The explorer does not hold a definition of maturity. It displays the figure the toolchain produces, or labels its own as an estimate.
  - title: One definition of every figure
  - status: accepted
  - rationale: Two independently computed figures for one artifact, both rendered as authoritative, is a defect in the toolchain rather than in either tool.
  - affects: R5.6, R5.7, R12.1

- D3 Anything the explorer cannot represent is reported. Silent omission is excluded.
  - title: Silence is excluded
  - status: accepted
  - rationale: Repeated predicates, list-valued details and unrecognised classes are currently dropped without notice, so the reader cannot distinguish a sparse specification from an incompletely rendered one.
  - affects: R2.6, R2.7, R2.9, R2.10

- D4 Type and status are encoded through shape or text with colour as a secondary channel.
  - title: Encoding is not colour alone
  - status: accepted
  - rationale: The current dots carry no information in greyscale, in print, or for a reader who does not distinguish the hues, and the specification's existing requirement that the colours be themeable addresses the wrong half of the problem.
  - affects: R3.6, R4.3

- D5 The explorer remains a single self-contained read-only file. Capabilities requiring evaluation, network access or a build step are supplied to it rather than implemented in it.
  - title: Single file, supplied inputs
  - status: accepted
  - rationale: Offline operation from removable media is a stated use case. Every capability added under this plan is either pure presentation of the loaded graph or the presentation of an artifact the CLI already produces.
  - affects: R1.1, R10.4, R12.1

- D6 The syntax reference is generated from the toolchain rather than written alongside it.
  - title: The reference is generated
  - status: accepted
  - rationale: The annotation key set already drifted once inside the translator when it was held as two copies. A reference maintained by hand is a third copy, in a different repository artifact, with no test that would catch the divergence.
  - affects: R13.1, R13.2

- D7 The explorer generates specl source and does not interpret it.
  - title: Emit, do not parse
  - status: accepted
  - rationale: Interpreting markdown in the browser is a second implementation of the translator's grammar, which OQ2 was resolved against. Emitting it requires only the key tables the syntax reference already carries. The asymmetry is what makes composition affordable and round-trip editing not.
  - affects: R13.5, R13.6
```

### 4.4 New design notes

```
- DN6 Acceptance criteria in this specification state what must be obtainable rather than what must be on screen. Where a criterion says a value is reported or returned on request, an implementation satisfies it by making the value reachable; where a criterion requires something to be visible without being asked for, it says so.

- DN7 Several capabilities depend on one structure: an index from IRI to item, built once at parse time. Reference navigation (R6.6), backlinks (R6.7), finding attribution (R12.2) and unresolved-reference marking all read from it. Building it as a distinct step rather than as a side effect of rendering is what keeps those capabilities from each carrying their own resolution logic.

- DN8 The explorer and specl-validate must not disagree about a number. Where the CLI computes a figure, the explorer displays that figure or states that it is estimating. Where the CLI computes nothing, the explorer's figure carries its own definition. This is the same obligation the format places on a specification: a number whose derivation is not recoverable is not evidence.

- DN9 The ODT Operational Console specification is the reference for authoring style in this specification: priority and acceptance on every requirement, rationale where a requirement encodes a judgement, decisions recorded with what they affect, and open questions that record their disposition when they close.
```

### 4.5 Open question dispositions

```
- OQ2 Whether to support loading the companion spec.md alongside the .ttl for side-by-side reading.
  - recommendation: Resolved as no. A markdown parser in the explorer would be a second implementation of the translator and would diverge from it. The need it addresses is met instead by carrying prov:wasDerivedFrom and specl:sourceLine into the detail view (R6.8), and by a CLI command that inlines the Turtle into a copy of the explorer.
  - status: resolved

- OQ4 Whether to show SHACL validation results inline by also loading a shapes.ttl.
  - recommendation: Resolved as yes, with the mechanism inverted. Shapes are not evaluated in the browser. The explorer consumes the JSON report specl-validate already emits, keyed by focus node. Specified as R12.1 and R12.2.
  - status: resolved

- OQ6 Export of the current view.
  - recommendation: Resolved. Fragment addressing (R11.1) covers sharing and a print stylesheet covers the paper case. A dedicated export path is not added.
  - status: resolved

- OQ1 Slash namespaces.
  - recommendation: Unchanged, and out of scope here. This is a question for the specl format rather than for a viewer of its output.
  - status: open

- OQ3 Mermaid rendering.
  - recommendation: Unchanged. Deferred.
  - status: open

- OQ5 Light theme.
  - recommendation: Unchanged, with one addition: D4 requires encoding that does not rest on colour, which removes the theme's ability to break the type indicator.
  - status: open

- OQ7 Is the attesting reader (P5) a distinct persona from the reviewer (P2)? Both read a specification they did not write and both need every item reachable. What separates them is that P5 must be able to assert that the presentation matches the file, which P2 may take on trust.
  - recommendation: Gated on implementation. If the raw view and the reporting of anything the parser could not represent are built for everyone, then P5 asks for nothing P2 does not already have, and it collapses. Keep the persona until those two capabilities exist and then test whether any requirement still names P5 alone.
  - status: open

- OQ8 Does authoring belong in the explorer, and if so how much of it?
  - recommendation: Composition yes, editing no, in this artifact. The explorer may emit source under D7 and R13.6. Editing an existing specification requires parsing markdown in the browser, which is the second grammar implementation D7 excludes, and validating what was authored requires an evaluator the single file cannot carry. Authoring in full belongs in a served mode where the toolchain is present, which is a separate artifact sharing this one's presentation rather than an extension of it. See Part 8.
  - status: open
```

### 4.6 Backfill obligation on the existing requirements

47 requirements carry a description and nothing else. This is why the specification scores 8%, and it is the reason a newcomer's first encounter with the toolchain is a red bar on the flagship artifact.

With everything in 4.1 through 4.9 applied, the specification translates with no parser warnings, validates with zero violations, and scores 63%. Two warning classes remain:

| Warning | Count |
| --- | --- |
| Requirement should have at least one acceptance criterion | 42 |
| Open issue should name an accountable agent via specl:owner | 8 |

The requirement backfill is mechanical for most of the 42, since each already states a testable condition in prose. The eight open issues need an owner, which is an accountability decision rather than an annotation and is left open here; `owner` is reference-valued, so an Agents section is the place for it if the owners are not the personas already declared.

Three worked requirement examples, in the house style ODTC establishes:

```
- R1.1 The explorer must be a single self-contained .html file with no external runtime dependencies (no CDN scripts, no fonts, no network calls).
  - priority: MUST
  - acceptance: Given the built file, when it is loaded with network access blocked, then it renders and functions with no failed requests.

- R5.2 A maturity score must be computed under the definition R5.6 establishes, over the population that definition names.
  - priority: MUST
  - acceptance: Given a loaded specification, when the maturity figure is displayed, then it matches the figure specl-validate score reports for the same graph, or is labelled as an estimate under R5.6.

- R7.1 When an item is selected, the tab shows that item's Turtle statement block, extracted from the raw text by locating the subject IRI and taking characters through the next statement terminator.
  - priority: MUST
  - acceptance: Given a selected item, when the Raw Turtle tab is opened, then the block displayed begins at that subject and ends at its terminator, and includes any derived cons cells belonging to it.
```

The third example carries a substantive correction rather than an annotation: the current extraction stops at the first terminator and therefore excludes the `rdf:List` cells that hold an item's sub-bullets, so the raw view of R6.2 omits the same content the detail view omits under DEF-4.

### 4.7 Personas

The specification has no Personas section, which is why five user stories cannot satisfy the shape requiring `role` to name a declared persona. The readership is already enumerated in the story text; this states it once.

```
# Personas

- P1. A specification author who writes the markdown, runs the translator, and uses the explorer to find what their own specification is missing before anyone else reads it. Knows the syntax unevenly and is the reader most likely to be looking something up while working.
  - title: Specification author

- P2. A reviewer reading a specification they did not write, who needs to reach any item's full statement and judge whether the set is coherent, whether its decisions are recorded, and where it is thin.
  - title: Reviewer

- P3. An integrator, human or automated, consuming the emitted graph, who needs to confirm that what the translator produced matches what a downstream tool expects before it is consumed.
  - title: Downstream integrator

- P4. A programme or engineering lead who consumes the judgement a specification supports rather than its individual items, and who needs to know how far that judgement can be relied on and what would improve it.
  - title: Programme lead

- P5. A reader who must be able to state that what the interface showed them is what the file says, and who has no tooling of their own to check it against.
  - title: Attesting reader
```

P5 is defined by an obligation rather than by an environment. An auditor working from removable media on a locked-down machine is the case that motivated it, but a persona defined by where someone sits generates no capability that a persona defined by what they must be able to assert does not. Whether P5 survives contact with an implementation is raised as OQ7 below, on the pattern ODTC uses for its own OQ1.

### 4.8 Story completion

The five existing stories carry a description and a priority. Completing them closes fifteen of the sixty-nine remaining warnings and gives the personas something to be referenced by.

```
- US1 As a specification author, I open the explorer, drop my spec.ttl, and immediately see which requirements are missing acceptance criteria so I know where to focus.
  - role: P1
  - capability: Per-item reporting of absent properties, aggregated into a figure that opens the items producing it
  - benefit: Revision effort is directed by what the specification is missing rather than by rereading it
  - acceptance: Given a loaded specification, when the maturity figure is opened, then the items reducing it are listed with the property each is missing.
  - priority: MUST

- US2 As a reviewer, I filter the sidebar by a keyword to find all requirements touching one subject, click through each one, and read their full detail without opening the markdown file.
  - role: P2
  - capability: Text filtering across identifier, title and description, with full item detail on selection
  - benefit: A specification can be reviewed without the source or a toolchain
  - acceptance: Given a filter term, when it is entered, then every item whose identifier, title or description contains it is listed, and when one is selected, then every property it carries is shown.
  - priority: MUST

- US3 As a downstream integrator, I open the explorer to verify that the emitted Turtle matches what I expect before feeding it to another tool.
  - role: P3
  - capability: Raw serialisation for any item and for the whole file, alongside the rendered presentation of the same content
  - benefit: The presentation layer is checkable against the graph rather than trusted
  - acceptance: Given a selected item, when its raw statement block is displayed, then it contains every property the detail view rendered and any derived nodes the item owns.
  - priority: MUST

- US4 As a programme lead, I read the maturity figure to gauge how close a specification is to production-ready without asking its author.
  - role: P4
  - capability: A single reported figure with its definition and its contributors reachable from where it appears
  - benefit: A judgement about a specification's state is formed from a stated definition rather than an impression
  - acceptance: Given the maturity figure, when its definition is requested, then what is counted, over what population, and with what exclusions is returned.
  - priority: MUST

- US5 As an attesting reader with no development tools installed, I open the explorer from removable media and read the specification in full.
  - role: P5
  - capability: Complete offline operation from a single file, with every item and the whole source reachable
  - benefit: A specification can be read and attested to in an environment that permits no installation
  - acceptance: Given a machine with no network access and no specl installation, when the file is opened from removable media, then every item in the loaded specification is reachable and the raw source is displayable.
  - priority: MUST
```

### 4.9 Bundled syntax reference

The reasoning behind these is in Part 8.

```
## R13 Syntax Reference

- R13.1 The explorer must carry a reference to the specl source syntax, reachable from any selection, covering the recognised section headings and the item class each produces, the annotation keys and the property each maps to, which keys take a reference rather than a literal, the recognised front-matter keys, and the markers that park or exempt a section.
  - priority: MUST
  - acceptance: Given any selection, when the reference is opened, then the sections, classes, annotation keys, reference-valued keys, front-matter keys and section markers the translator recognises are all listed.
  - rationale: The reader most likely to be looking the syntax up is the author who is at that moment looking at what their specification is missing. Requiring them to leave for a separate document to find the key that fixes it is the point at which the correction does not get made.

- R13.2 The reference must be generated from the translator's own tables and the bundled shapes when the explorer is built, and must state the specl version and graph contract it was generated from.
  - priority: MUST
  - acceptance: Given the built explorer, when the reference is inspected, then every annotation key the translator accepts is present, no key the translator does not accept is present, and the version and contract the reference was generated from are stated.
  - rationale: The translator's own source records that this key set was once held as two hardcoded copies, and that adding a key to one and not the other made a valid annotation parse as unknown. A hand-maintained reference is a third copy of the same set, with the same failure and a slower path to discovering it.

- R13.3 Where an item is selected, the reference must indicate which annotation keys the item's class accepts and which of those the item does not carry.
  - priority: SHOULD
  - acceptance: Given a selected item, when the reference is opened, then the keys its class accepts are distinguished from the rest, and those absent from the item are marked.
  - rationale: This is the same information the detail view already renders as "not set" placeholders, expressed as the syntax needed to fill them. Connecting the two makes the reference part of the correction rather than a document beside it.

- R13.4 The reference must be held in the single file and must not require a network request or a second document.
  - priority: MUST
  - acceptance: Given a machine with no network access, when the reference is opened, then it renders in full.

- R13.5 The explorer may generate specl source. It must not interpret it.
  - priority: MUST
  - acceptance: Given the explorer's implementation, when it is inventoried, then it contains no parser for specl markdown, and any source it produces is offered to the user rather than loaded back into the graph it holds.
  - rationale: A markdown parser in the browser is a second implementation of the translator's grammar and will diverge from it, which is the reason OQ2 was resolved as it was. Emitting source requires only the key tables the reference already carries, so the two directions have different costs and are governed separately.

- R13.6 The explorer must be able to compose a new item of a selected class and emit it as markdown, with the emitted text marked as unvalidated until the translator has processed it.
  - priority: SHOULD
  - acceptance: Given a selected class, when an item is composed and emitted, then the markdown produced carries the section heading, the identifier prefix and the annotation keys that class accepts, and states that it has not been validated.
  - rationale: Composition is string assembly over tables the file already holds. It supplies most of what authoring assistance is wanted for without the explorer holding any state the graph does not.
```

**R1.4** currently caps the file at 30 KB uncompressed. The file is 13.6 KB today, and the capabilities in this plan (a reference index, findings, navigation, the syntax reference, the composer) will exceed the cap. The cap should be restated as the constraint it was standing in for:

```
- R1.4 The explorer must remain one file with no build step, no bundler, and no external runtime dependency, and must render its first view without waiting on anything it does not already contain.
  - priority: MUST
  - acceptance: Given the built file, when it is opened with network access blocked, then it renders with no failed requests and no deferred load.
  - rationale: The byte cap was a proxy for keeping the tool dependency-free and instantly loadable. Stated as a number it now forbids capabilities that cost nothing against the property it was protecting.
```

---

## Part 5. Changes requested of specl itself

These sit outside the explorer's specification and are the changes with the largest effect on whether the explorer is ever opened.

### 5.1 Publish the explorer at a URL

R1.3 ships the explorer as package data inside the Python distribution, so seeing the tool requires installing the thing the tool exists to demonstrate. It is a single file with no network calls; hosting a copy costs nothing and takes nothing away from R10.4. The offline copy stays in the package.

### 5.2 Ship an example specification inside the file

The empty state currently instructs the reader to drop a file. A reader who has none leaves. An embedded example behind a "load example" control turns the first thirty seconds into a demonstration instead of an instruction.

### 5.3 Add a command that produces a self-contained artifact

A command that translates, validates, scores, and writes a copy of the explorer with all three inlined removes the translate-then-drag sequence and produces a single file that can be sent to a reviewer who will never install anything. In controlled environments that property is worth more than the tool itself, and it is what makes R12.1 usable in practice rather than in principle.

### 5.4 Reconcile the score definition

R5.6 requires one definition of maturity. Which definition is a specl decision rather than an explorer decision. The CLI's shape-based, priority-weighted figure over all item types is the better of the two and should be published as the definition, with the explorer's fallback documented as an approximation of it.

### 5.5 Bring the flagship specification up to the standard

Part 4.6. The first specification most readers see should be the one that demonstrates the practice.

---

## Part 6. Sequencing

Grouped by dependency rather than by effort.

**First group, defects that lose content.** R2.6, R2.7, R2.9, R2.10, and the R7.1 correction. These change what the tool shows to be a true account of the file. Nothing else in the plan is worth doing while the tool is quietly dropping content.

**Second group, the reported issue.** R3.3, R4.6, R4.7, R7.6, R8 retitling, D1. Self-contained once the parser is honest, and the change the report asked for.

**Third group, cheap imports from ODTC.** R3.6, R4.8, R4.9, R5.7, R5.8, R6.8, and the escaping fix. Each is small and independent; together they account for most of the difference between the current tool and one a non-author can use.

**Fourth group, the graph becomes navigable.** DN7's index, then R6.6, R6.7, R11.1, R11.2. This is the group that answers why the format is RDF.

**Fifth group, measurement.** R5.6, R5.9, D2, and the specl-side decision in 5.4. Sequenced after the rest because it depends on a decision taken outside the explorer.

**Sixth group, findings.** R12.1, R12.2, and the packaging work in 5.1 through 5.3.

**Later.** Multi-file loading for a specification family, since layering exists in the CLI and has no viewer, and a two-file comparison fed by `specl-validate diff`, which is what ODTC's temporal capabilities reduce to at document scale.

## Part 7. Acceptance for the plan as a whole

- The explorer's own specification translates with no warnings, validates with no violations, and scores above the threshold the reconciled definition sets.
- The figure in the header and the figure from the CLI agree on any file, or the header states that it is estimating.
- Loading a file that exercises repeated predicates, list-valued details, an unrecognised class and an unresolvable reference produces four visible reports and no console-only messages.
- Every count in the interface opens the items it counted.
- Every reference-valued property in the explorer's own specification reaches its target in one action.

---

## Part 8. The syntax reference, and how far authoring should go

### The reference is a build artifact, not a document

The syntax the translator accepts is already data in the translator: the annotation key map, the context-sensitive keys, the reference-valued keys and their declared ranges, the section-to-class map with its identifier prefixes, the classes a project may map a custom heading onto, the prose sections, the front-matter keys, and the markers that park or exempt a heading. What each class is expected to carry is data in the bundled shapes, as the message on each shape.

Generating the reference from those two sources at build time costs a short script and makes one class of error impossible. The alternative is a hand-written cheat sheet, which is a second statement of a set that already exists in code, maintained by whoever remembers to. The translator's own source records what happens: the key set was once held as two hardcoded copies, and adding a key to one and not the other made a valid annotation parse as an unknown key. The comment recording that fix says the pattern was derived rather than restated so that drift would be impossible rather than merely detectable. A cheat sheet written by hand restores exactly the condition that comment was written to close.

Generation also produces something a written document cannot. Because the reference knows which keys each class accepts, it can be shown against the selected item: these are the keys a Requirement takes, these are the ones this requirement does not carry. That is the same information the detail view already renders as "not set" placeholders, expressed as the syntax that would fill them. The reference stops being documentation beside the tool and becomes part of the correction path, which is the difference between a reader looking something up and a reader fixing something.

Placement is a drawer or overlay reachable from any selection rather than a tab, because R3.3 now fixes the tab set at two and scopes both to the selection. The reference is scoped to neither.

### Authoring: composition is affordable, editing is not

Authoring divides into two operations with very different costs, and the division is not where it first appears.

Emitting source is string assembly over tables the file will already hold once the reference is generated. Choosing a class, filling the keys it accepts, and producing a correctly shaped bullet requires no grammar beyond the key list. It is cheap, it composes with the reference, and it is worth doing.

Interpreting source is a parser. Loading an existing `spec.md` to edit it means implementing the front matter, the section map, the identifier grammar, the sub-bullet annotation form, the detail lists, the parked and prose markers, and the reference resolution rules, in JavaScript, in a file with no build step. That is a second implementation of the translator, and it will diverge, because nothing tests it against the first. OQ2 was resolved against exactly this reasoning for reading `spec.md` alongside the Turtle. Editing it is the same decision with more surface.

There is a further problem that effort does not describe. The explorer holds a graph produced by a past translation. If it also holds edits that have not been translated, it holds two descriptions of one specification with no way to reconcile them, because reconciliation is a translation and the file cannot perform one. Every figure the tool reports would then be computed over the older of the two states while the interface displays the newer. The plan spends Part 4 removing one instance of the tool reporting a number whose derivation the reader cannot recover; in-file editing would introduce a larger one.

So composition is in scope and editing is not, and the boundary is stated as a rule rather than as a scope note: the explorer may generate specl source and must not interpret it. That is D7, and it is what makes the question decidable for capabilities nobody has thought of yet.

### Where full authoring belongs

Authoring is not too ambitious. It is in the wrong artifact.

Part 5.3 proposes a command that produces a self-contained copy of the explorer with the graph, the validation report and the score inlined. A served variant of that command is the natural home for authoring: the toolchain is present, so an edit can be translated by the real translator, validated by the real shapes and scored by the real definition, with the view re-rendered from the result. No second grammar, no second definition of any figure, and no divergence, because every derived thing is derived by the tool that owns it.

That gives two modes with one presentation layer and a clean split. The distributed single file is read-only, offline, and attestable, which is what P3 and P5 need. The served mode is an authoring surface, which is what P1 needs and what P1 is currently leaving the tool to get. The capability boundary falls exactly where the dependency boundary already falls, which is usually a sign the split is real rather than imposed.

The order matters. The served mode is worth building after the file is honest about what it is showing and the reference exists, because both are inputs to it. Nothing in this plan needs to change to accommodate it later, which is the point of settling D7 now.
