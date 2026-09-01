# specl explorer

A single-file, dependency-free viewer for the Turtle that `specl-translate`
emits. Open `dist/explorer.html` in a browser and drop a `spec.ttl` on it,
or press the button to load the embedded example, which is this explorer's
own specification.

Nothing here needs Python. specl produces inputs as files; the explorer's
build, tests and runtime are plain HTML, CSS and JavaScript plus Node with
no packages.

## Layout

| Path | What |
| --- | --- |
| `explorer.html` | The source. Authored directly; four empty JSON slots. Loads and works as-is, without a grammar or example. |
| `dist/explorer.html` | The built file: slots filled. This is what is hosted, released and packaged. |
| `build/build.mjs` | Fills the slots from files. `--grammar`, `--example`, `--report`, `--score`, `--autoload`. |
| `build/check-example.mjs` | R9.4: fails if the embedded example differs from the emitted graph. |
| `build/compose.mjs` | One command from a `spec.md` to a self-contained explorer that opens on it with its findings. Shells out to the specl CLI for the inputs. |
| `build/grammar.py` | Generates `build/grammar.json` from the installed specl's translator tables and shapes. The interim form of UP-3. |
| `build/grammar.json` | The grammar artifact: sections, keys, expectations, the score definition. Regenerate when specl changes. |
| `fixtures/` | Stage 0 fixtures. Hand-authored ones say so on their first line and must not be regenerated. |
| `test/run.mjs` | The harness, 54 checks. Extracts the script from the HTML and runs it in a bare Node context. |
| `test/dom.smoke.mjs` | Optional. Drives a real DOM through the interface; needs jsdom. |
| `test/mobile.smoke.mjs` | Optional. The narrow-screen stylesheet and pane switching, with `matchMedia` deleted. |
| `test/package.json` | Dev-only. jsdom for the two smoke tests; nothing else in the tree has a dependency. |
| `test/explorer-1.0.0.html` | The shipped 1.0.0 file, for `run.mjs --before`. |
| `ci/explorer.yml` | The workflow. Goes to `.github/workflows/`. |
| `STATUS.md` | Stage record against the implementation plan. |
| `UPSTREAM-ISSUES.md` | Issues against specl found during this work, written to be submitted. |
| `explorer-self-review.md` | A review of this work: seven findings, six fixed, one recorded. |

## Commands

```
node test/run.mjs                                   # harness, no dependencies
node test/run.mjs --before                          # also run the shipped 1.0.0 parser for comparison
cd test && npm install && npm run smoke             # optional DOM smoke test (jsdom)
cd test && node mobile.smoke.mjs                    # optional narrow-screen check
node build/build.mjs --grammar build/grammar.json --example fixtures/explorer-spec.ttl \
     --report fixtures/explorer-spec.report.json --out dist/explorer.html
node build/check-example.mjs dist/explorer.html fixtures/explorer-spec.ttl
node build/compose.mjs path/to/spec.md --out review.html   # needs specl on PATH
python3 build/grammar.py > build/grammar.json                # needs specl installed
python3 fixtures/make_fixtures.py --spec path/to/explorer/spec.md   # regenerate generated fixtures
```

## Slots

The built file differs from the source only in four `<script type="application/json">` elements:

| Slot | Content | Absent means |
| --- | --- | --- |
| `slot-grammar` | `build/grammar.json` | Syntax reference unavailable; readiness uses a built-in table matching specl 1.0.0 |
| `slot-example` | `{title, version, autoload, turtle}` | No example offered from the empty state |
| `slot-report` | `specl-validate validate --json` output for the example | Findings unavailable; readiness is an estimate |
| `slot-score` | A score object (`{score, clean, total, ...}`) | Readiness computed here from the report or estimated |

Anything that can write JSON into these elements can compose the explorer.

## Reading it

The specification is the first row in the list and is selected when a file
loads; the header title selects it too. Every selection carries the same two
tabs; a page is headed by the item's class and identifier, and the Raw
Turtle view numbers lines as they are numbered in the file. Counts on the specification view open the items they count. A reference
value is a control that selects its target; an unresolvable one is marked.
Selection and tab live in the fragment, so an address restores a view.

On a narrow screen the page shows one pane at a time: the list, or the
selection. An "items" control in the tab strip returns to the list; selecting
a row shows it. A chip narrows the list and switches to it, with a bar above
saying what is shown and a "show all" to clear it. Back and forward walk views, so going back from
an item returns to the list you reached it from. The layout is a stylesheet
decision alone; the script never asks how wide the screen is.

Dark, light and follow-the-system are one control in the header. Dark is the
default and the choice is not persisted.

## What the figure in the header means

With a report loaded, the maturity figure is computed under `specl-validate score`'s definition: every item of an item class, retired items excluded, MUST 4 / SHOULD 3 / COULD 2 / WONT 1 / default 2, clean when no result names it and an open issue is resolved or deferred. Without a report, each item is checked against the shape expectations in the grammar and the figure is labelled an estimate. The definition is one click away from the figure. Every route applies the same gate rule the CLI does: a Violation, or a Warning
at status production, means no figure rather than a low one. On the explorer's
own specification all three routes agree.

What the panel marks as missing comes from the same expectations, through the
same conditions, so an item is never called clean while its own panel flags a
gap. Retired items are excluded from the figure and get their own chip, so the
counts on screen add up to the total.
