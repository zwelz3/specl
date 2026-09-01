# Review of the explorer work

A review of what I built in this session, against the standard I applied to
the 1.0.0 explorer. Findings are ordered by consequence and each was
reproduced, not inferred. Identifiers are `SR-n` to keep them out of the
`DEF-` and `UP-` namespaces already in use.

## SR-1. The panel contradicts itself about 74 of 109 items

The detail view marks a property "not set" in warning colour when the
property is in a hardcoded `EXPECTED` table for that class. The readiness
computation decides the same question from the grammar, honouring the
conditions the shapes carry. The two disagree.

On the explorer's own specification, R1.1 is reported clean by the chip at
the top of its own panel and simultaneously shows three amber "not set"
markers, for `priority`, `verifiedBy` and `constrains`. The readiness
figure is right: the graph declares no `Component` and no `Test`, so the
conditional shapes for `constrains` and `verifiedBy` do not apply, and
`priority` carries an `sh:in` with no `sh:minCount`, so its absence is not
a finding. The detail view marks all three anyway. 74 items of 109 are
called clean while flagging at least one missing property.

This is DEF-1 rebuilt in a new place: one screen, two definitions of what
an item needs, both presented as fact. It is the defect this whole exercise
existed to remove, and I reintroduced it.

The cause is that stage 9 was specified to replace `FIELDS` and `EXPECTED`
with the grammar and did not. `detailRows(m, it)` never receives the
grammar. The drawer (R13.3) reads the grammar and is correct; the detail
view beside it does not.

Fix: `detailRows` takes the grammar, derives `expected` from
`expectationsFor(grammar, cls)` filtered through `conditionHolds`, and
`FIELDS` keeps only display order. `EXPECTED` is deleted.

## SR-2. The counts on the specification view do not reconcile

The first chip row reads "111 items". The second reads "100 clean" and "9
not clean". They differ by the two withdrawn requirements, which are
excluded from the readiness population and belong in no state chip, so
tapping "clean" and "not clean" in turn shows 109 of the 111 the row above
claims.

This is DEF-2, the count I criticised the old tool for, in a subtler form:
every figure is individually defensible and the row does not add up.

Fix: state the exclusion where it is visible, not only inside the
definition disclosure. "111 items, 2 retired" and a chip that opens the
retired pair, or the state chips labelled "of 109 counted".

## SR-3. I shipped source changes I could not account for

At 00:00 UTC, `assemble.py` and `dom.js` gained a header restructured into
two rows, a one-page-scroll mobile layout, and an "Open a spec.ttl" button.
I did not write them. I reviewed them, judged them better than mine, kept
them, and said so; I did not stop.

For a handoff package that is the wrong call. The right one was to stop,
establish what wrote them, and either re-derive the change deliberately or
revert it. A package whose provenance I cannot fully vouch for is a weaker
artifact than one that is slightly worse and fully accounted for. The
manifest checksums what is in the box; it says nothing about who put it
there.

I still cannot identify the author. The most likely explanation is a
delegated agent sharing the container.

## SR-4. Three wrong diagnoses before the drawer

The phone reports took four rounds. I proposed a `matchMedia` mismatch, a
touch-device viewport, and a pane-switching bug, and shipped a fix for each
before finding that a hidden `<aside>` was being displayed by the rail's
own rule.

Two of those fixes are worth keeping on their merits: the layout no longer
depends on `matchMedia`, and the tab strip is hidden before load. The
`(pointer:coarse) and (max-width:1100px)` trigger is not; it was added to
chase a hypothesis that turned out to be wrong, and it now means a tablet
in landscape gets the phone layout. It should be reverted unless it is
wanted for its own sake.

The method failure is what matters. I had jsdom, computed styles were one
call away, and I asked about attributes instead. The check that would have
found it in the first round is the one I added in the fourth.

## SR-5. Invalid ARIA in three places

- The `☰ items` button sits inside `role="tablist"`. A tablist may contain
  only tabs. Move it outside the strip, or drop the tablist role and treat
  the two tabs as ordinary buttons.
- `#list` is `role="listbox"` but its `role="option"` rows are nested in
  `.group` wrappers, so the listbox owns no options. Either flatten, or use
  `aria-owns`, or drop to a plain list with `aria-current`.
- The tabs carry no `aria-controls` and `#panel` no `aria-labelledby`, so
  the relationship the roles assert is not expressed.

R10.3 says keyboard accessible and the keyboard works. The roles claim more
than the structure delivers, which is worse than claiming nothing.

## SR-6. A selector that fails on Safari before 16.4

Focus after a chip tap uses `.item:not(.pinned .item)`. A complex selector
inside `:not()` is Selectors 4; Safari shipped it in 16.4. On older Safari
the whole selector is invalid, `querySelector` returns null, and focus does
not move. R1.2 names Safari without a floor.

Fix: `#list .group:not(.pinned) .item`.

## SR-7. Smaller things

- `readiness()` runs up to three times per render, over every item. At 500
  items that is measurable and needless; compute once per render and pass it.
- The DOM pushes `rejected-file` and `report-mismatch` entries onto
  `model.report`, which is otherwise the parser's output. Drop five bad
  files and the banner lists five. Session notices belong in their own list.
- Findings are skipped for the Specification node. The current shapes put
  three Violation-severity constraints on it, so a specification missing a
  title would have its finding computed and never displayed.
- `STATUS.md` still says the `FIELDS` and `EXPECTED` tables are built in
  "for now" and that stage 9 replaces them. Stage 9 did not. The record is
  inaccurate on exactly the point SR-1 is about.

## What holds up

The parser and the index are the strongest part: thirteen fixtures, every
1.0.0 failure closed, damage isolated and reported rather than skipped. The
readiness computation reproducing `specl-validate score` exactly on a real
specification, through three independent routes, is the result I would keep
if I could keep one. The build, the identity guard and `compose.mjs` do what
they claim, and the ODT composition is real evidence rather than a
demonstration on a toy.

## Order to fix

SR-1 and SR-2 before the handoff moves; they are the class of defect the
work was commissioned to remove and they are cheap. SR-6 with them, one
line. SR-5 next. SR-3 is a decision for you rather than a fix. SR-4 is
recorded so the lesson survives the commit. SR-7 whenever.
