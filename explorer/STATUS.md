# Explorer rewrite: stage record

Tracks the implementation plan stage by stage. `node test/run.mjs` is the
check; `node test/run.mjs --before` also runs the shipped 1.0.0 parser
against the same fixtures for comparison.

## Stage 0. Fixtures and harness: complete

Thirteen fixtures under `fixtures/`, seven produced by `specl-translate`
1.0.0 and six hand-authored (each carries a first-line comment saying so).
`fixtures/README.md` maps each to its requirement.

Before-state, the shipped 1.0.0 parser against the fixture set:

| Fixture | Shipped 1.0.0 |
| --- | --- |
| repeated-predicates | keeps only the last of three criteria |
| detail-list | `detail` is a dangling pointer; sub-bullets dropped |
| local-name-collision | `ex:title` silently overwrote `dct:title` |
| unrecognised-class | widget counted as an item, cannot be listed |
| malformed-statement | damage neither isolated nor reported; partial R2 kept |
| future-contract | contract never read |
| unresolvable-reference | reference rendered as text; nothing resolves |
| alt-labels | `altLabel` collapsed to last value; not filterable |
| no-title | ok (title was never used) |
| zero-requirements | ok |
| no-items | `SourceDocument` counted as an item |
| no-specification | ok |
| five-hundred-items | `SourceDocument` counted; 501 reported |

Ten of thirteen fail. Every failure is silent.

## Stage 1. Parser and model: complete

`explorer.html` carries a tokenizer and statement parser sufficient for the
emitter's Turtle and tolerant of damage. Thirteen of thirteen fixtures pass.

- R2.8: properties keyed by full IRI. `dct:title` and `ex:title` coexist.
- R2.6: every value of a repeated predicate is kept, in order.
- R2.7: `rdf:List` cells are read into `item.details` and consumed; an
  orphan cell is reported.
- R2.3: the contract 2 class set is split into item classes (listed) and
  node classes (resolvable, not listed). `SourceDocument` is no longer an
  item.
- R2.9: anything the model cannot represent lands in `model.report` with a
  kind, a subject and a line: unrepresented class, malformed statement,
  untyped subject, orphan list cell, unknown contract, no specification.
- R2.4: a statement that fails part-way leaves nothing behind. Properties
  accumulate locally and merge only on a clean terminator. A single-quoted
  literal stops at a newline, so an unterminated string cannot swallow the
  next subject.
- R2.10: `dct:conformsTo` is read; contract 2 is known, anything else is
  reported and flagged on the model.

On the explorer's own specification: 111 items in 28 ms, empty report,
R9.4 carries both criteria, R6.2 carries its four sub-bullets.

## Stage 2. Reference index: complete

`buildIndex` produces `resolve`, `isResolvable` and `referrers` over every
subject in the graph. Forward references and backlinks both read from it.
The unresolvable-reference fixture distinguishes an external test IRI
(unresolvable) from a local one (resolvable, with one referrer).

## Stage 3. Selection model: complete

The reported issue. The specification is a pinned row at the head of the
list, exempt from the filter, selected on load; the header title selects it
too. Two tabs, Detail and Raw Turtle, both scoped to the selection, the set
constant for every selection. Raw Turtle offers this item or the whole file
(R7.6); the item block is the item's statements plus the list cells it owns,
in file order (R7.1). Selection never rebuilds the list; only the active row
changes, so keyboard focus survives and the arrow keys work (R4.9). R7.2 and
R8.4 withdrawn.

## Stage 4. Presentation: complete

The page heading is the item's class and identifier (R6.1); the line that
used to repeat both is gone and the IRI takes its place. A title that is a
truncation of the description below it is not repeated as a row; a real one,
as on a persona, is. Title as the sidebar label with the description preview
as fallback (R4.8, R4.2).
A class glyph on every row and in the detail heading, colour secondary
(R3.6, R4.3). Properties in class order, then the rest, with expected-but-
absent properties present as marked rows (R6.1 to R6.3). Provenance as
document and line (R6.8). Highlighting by token class with weight and style
alongside colour (R7.3), emitted one line at a time so a triple-quoted
literal spanning a newline does not leave an element open across the break.
The Raw Turtle view numbers every line with its line in the loaded file, in
both views, marking a break where an item's statements are not contiguous;
the numbers are generated content, so copying the block copies the Turtle
(R7.7). The R2.9 report is a banner at the head of the list
naming each thing not shown, with its line. Unescaped content no longer
reaches `innerHTML` (DEF-10).

FIELDS carries display order only. What counts as expected-but-absent comes
from the grammar, through the same conditions the readiness computation
applies, so the panel and the figure cannot disagree (see the self-review,
SR-1). Without a grammar in the slot, both fall back to the same built-in
table.

## Stage 5. Filter: complete

Matches identifier, displayed label, description, and every SKOS label
(R4.5). A row matched on text it does not display says what matched.

## Stage 6. Navigation: complete

Reference values are controls that select their target; an unresolvable
one is marked (R6.6). A "Referenced by" section groups backlinks by
predicate (R6.7). Selection and tab live in the fragment, including the
whole-file state (R11.1). Back and forward across the trail (R11.2).

Stage 6 is the plan's cut line. Every verified defect except DEF-1 is
fixed. The specification view shows counts as class filters; the readiness
ratio and the maturity figure are stage 7 and the view says so.

## Stage 7. Measurement: complete, with fallbacks

Three routes to one figure, each stating its definition (R5.7) and each
applying specl-validate's gate rule, so a graph carrying a Violation (or a
Warning at status production) shows no figure here either, rather than one
the CLI would withhold. Routes: a supplied
score is shown as supplied; a supplied validation report is used to compute
the figure under `specl-validate score`'s definition (population, retired
exclusion, priority weights, unresolved-issue rule, all read from the
installed 1.0.0 source and recorded in the grammar); with neither, each item
is checked against the grammar's shape expectations and the figure is
labelled an estimate. On the explorer's own specification the three routes
agree exactly with the CLI: 94%, 100 of 109, the same nine contributors.
The header bar uses named thresholds (R5.4). Counts open their populations
(R5.8); the shortfall lists its contributors heaviest first with what each
lacks (R5.9); an item shows whether it is clean and why (R6.4). The
specification view reconciles: total items, retired (with a chip that opens
them), then clean and not clean of the counted remainder.

Conditional expectations (`constrains` only when the graph declares a
Component, `verifiedBy` only when it declares a Test or AcceptanceQuery,
`supersededBy` by status) follow the graph, which is what makes the estimate
match the CLI rather than approximate it.

## Stage 8. Findings: complete, with the report as input

A report from `specl-validate validate --json` is accepted from the slot or
dropped alongside the graph (R12.1). Rows carry a finding count; the detail
view lists severity, path and message (R12.2). With no report, findings
report themselves unavailable. A report naming no subject in the loaded
graph is reported as not matching rather than silently applying nothing.

## Stage 9. Syntax reference: complete, from a generated grammar

`build/grammar.py` reads the installed specl's translator tables and shapes
and emits `build/grammar.json`, stamped with the specl version and contract
(R13.2). The build embeds it (R13.4). The drawer shows front matter,
sections and prefixes, markers, the item form, every annotation key with its
property and whether it takes a reference, and per-class expectations
(R13.1); with an item selected, its class opens and each expectation is
marked present, absent, or not applying (R13.3).

## Stage 10. Composer: built, then withdrawn

The drawer composed an item of a chosen class as markdown carrying the
section heading, the identifier prefix and the keys its class expects. On
use it was the wrong help: a viewer that cannot translate, validate or
score what it emits hands the author text nothing has checked. R13.6 is
withdrawn, OQ8 resolves as no authoring in this artifact, and the code is
gone. R13.5 stands and governs anything that would emit source later; the
file still contains no markdown interpreter and the harness still checks
for the regex shapes one would need.

## Stage 11. Build and distribution: built, channels pending

`build/build.mjs` fills the four slots from files; `build/check-example.mjs`
is the R9.4 guard and fails on a one-byte divergence; `build/compose.mjs`
goes from any `spec.md` to a self-contained explorer that opens on it with
its findings attached (the shape of S4, shelling out to the specl CLI).
`ci/explorer.yml` is the workflow: specl produces the inputs, Node builds
and checks, the packaged copy is placed rather than built (R1.6), and a
tagged build compares channels (R1.3) once the hosted URL exists (PR1).

The example is this specification's own graph, version stated, offered from
the empty state (R9.4). Composed with the ODT Operational Console
specification as a proof: 156 items, 17 findings attached, autoloads.

## Stage 12. Non-functional: proxy checks pass; browsers pending

Checked without a browser: R10.1 (500 items parsed, listed, detailed and
scored in 50 ms, after replacing the per-token slicing with sticky regexes;
was 293 ms), R10.2 and R1.1 (no external resource, fetch, socket or
navigation anywhere in the file), R1.5 (no import, require, export or
module type in the script), R3.5 (every colour literal is a token at
`:root`), R7.4 (highlighting is a function in the file).

Still yours: R1.2 in Chromium, Firefox and Safari over `file://`; R10.3 with
no pointer end to end; R10.4 from removable media.

## Mobile

One breakpoint at 720 px. The header becomes two rows (title with the
status badge; maturity beside the buttons) through wrapper rows that are
`display:contents` on desktop, so the wide layout is unchanged. Below the
header the page is one natural scroll rather than nested scroll regions,
showing one pane at a time: the list, or the selection. An "items" control
in the tab strip returns to the list with focus on the active row;
selecting an item shows it. The empty state offers an "Open a spec.ttl"
button because the file control lives in the hidden pane. 44 px targets,
16 px inputs so iOS does not zoom on focus, wrapped labels, stacked
definition lists, a full-width drawer, icon-only back and forward, dynamic
viewport height and safe-area padding. `test/mobile.smoke.mjs` checks the
stylesheet and the pane switching under a simulated narrow screen.
Rendering, touch scrolling and the sticky tab strip need a device.

**The defect behind the phone reports was not the layout.** The syntax
drawer was an `<aside hidden>`, and the rail's `aside{display:flex}` rule
overrode the browser's `[hidden]{display:none}`, since author rules win
over user-agent rules whatever their specificity. The drawer therefore
rendered at all times as an empty, fixed, panel-coloured element over the
page: the right 560 px on desktop, the whole screen on a phone. That is the
"empty rail" with content "underneath". Fixed three ways: `[hidden]
{display:none !important}` at the top of the stylesheet; rail rules scoped
to `main>aside`; the drawer is a `<div>`. The smoke tests now assert
computed `display`, not the attribute, for every element that starts
hidden, which would have caught it.

Back and forward walk views rather than selections: a trail entry records
the item, the tab, which pane is showing and how the list was narrowed, so
going back from an item reached through a chip returns to that narrowed
list rather than to the previous item on the same pane. Typing in the
filter box does not push an entry; discrete navigations do.

The syntax reference renders front matter as a table of key, whether it is
required, and what it does, rather than a run of code spans that wrapped
into a block of text on a phone.

The stylesheet alone decides which pane a narrow screen shows: with no
class on `<main>` it shows the selection, and `mode-list` shows the rail.
The script sets or clears that one class and never consults `matchMedia`,
after a report from a phone in which the rail and the selection were both
visible, stacked, which is what happens when a viewer's `matchMedia`
disagrees with its stylesheet or is missing. The mobile smoke test now
runs with `window.matchMedia` deleted. A static empty state is in the
markup so a render with scripts blocked still says what to do.

Chips open the population they count on a phone as well as beside it: a
class or clean/not-clean chip narrows the rail and switches to it, with
focus on the first row and a bar above the list saying what is shown and
offering "show all". The maturity figure is a control that reaches the
contributors on the same pane. On a wide screen the pane switch is a
no-op, since the rail is already beside.

Before a file is loaded the tab strip and its "items" control are hidden,
so the only pane reachable is the empty state with its buttons; the empty
state carries a real file input inside a label (a proxied click on an input
in a hidden pane is ignored by iOS Safari), and the rail explains itself if
it is the pane on screen. Both file controls accept `.ttl` and `.json`,
several at once.

A print stylesheet (the other half of OQ6's resolution) prints the
selected item alone, links with their fragment, and every colour through
the tokens.

## Themes

Dark by default, light, and follow-the-system, each one block of token
declarations, switched by a control in the header and not persisted
(R3.7, resolving OQ5). Nothing outside the token blocks knows which is
applied, which is what R3.5 bought. The harness asserts all three blocks
declare the same token set.

## Verification

`node test/run.mjs`: 54 checks, all passing: 13 parser, 12 view model, 12
for stages 7 to 10, 8 non-functional proxies, 7 self-review regressions, 3 for R6.1 and R7.7. On a
checkout where the generated inputs are absent it names them and the command
that produces each, rather than failing on a stack trace.
`node test/mobile.smoke.mjs`: optional, jsdom; the mobile stylesheet and pane switching.
`node test/dom.smoke.mjs`: optional, jsdom; drives the source file through
selection, keyboard, backlinks, trail, raw toggle, filter, header and the
report banner, then the built file through the example, the header figure,
the chips as filters, findings, the drawer and the composer. Passing.

## Findings against specl

Eight, in `UPSTREAM-ISSUES.md`, written as issue bodies for Zach to submit.
UP-1 and UP-2 were found at stage 0 and 1; UP-3 to UP-5 at planning and
stage 1; UP-6 to UP-8 at stages 7 to 9. None is opened from here.

## Self-review

A review of this work is in `explorer-self-review.md`. SR-1 (the panel
contradicting the figure on 74 of 109 items), SR-2 (counts that did not
reconcile), SR-4 (a touch-device breakpoint added while chasing a wrong
diagnosis), SR-5 (invalid ARIA), SR-6 (a selector older Safari rejects) and
SR-7 (readiness computed three times per paint) are fixed, each with a
regression check in the harness. SR-3, unattributed edits to the source
during this session, is a decision rather than a fix and is recorded there.

## Not verifiable without a device or a browser

- R1.2: `dist/explorer.html` over `file://` in Chromium, Firefox and Safari.
- R10.3: keyboard only, load to export.
- R10.4: from removable media, no network, no specl installed.
- Rendering, touch scrolling, the sticky tab strip, safe-area insets.
- R1.3 channels: the hosted copy and the release asset, once they exist.

## Watch items

- The built file is about 186 KB, most of it the embedded example (85 KB) and
  the grammar (13 KB). R1.4 as restated is about dependencies and load,
  not bytes, and first paint is unaffected; worth knowing before someone
  asks why a viewer is that size.
- `specl-validate score`'s definition is read out of the 1.0.0 source and
  restated in `build/grammar.json`. If specl changes the population, the
  weights or the clean rule without changing the shapes, the estimate drifts
  silently. UP-2 and UP-6 ask specl to publish it; until then, the check is
  that the estimate still equals the CLI on the explorer's own spec, which
  the harness asserts.
- The grammar generator recovers shape conditions from SPARQL target text
  (UP-8). It is correct for 1.0.0's shapes and fragile against restated
  ones. Regenerating after a specl upgrade and rerunning the harness is
  the check.
