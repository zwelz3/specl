# Governance

From 1.0, the author does not change the specification unilaterally. This is
what that means in practice, written before it binds anyone so that an adopter
can read it while deciding whether to adopt.

## What is governed

**Governed, and subject to the process below:**

- The graph contract: emitted IRIs, property ranges and domains, class
  semantics, and anything `docs/contracts/` describes as a guarantee.
- The authoring syntax: section headings, the identifier grammar, annotation
  keys and what they mean.
- The commitments in `specs/commitments/spec.md`, which a second party has
  already authored against.

**Not governed, and changed at the author's discretion:**

- Implementation, performance, internal structure, and test coverage.
- Command-line ergonomics: new flags, output formatting, error wording.
- Documentation, except where it states a governed guarantee.
- Fixes that bring behavior into line with what the specification already says.
  A defect is not a change of contract, and requiring consensus to honour an
  existing promise would make the process an obstacle to keeping it.

When it is unclear which side something falls on, it is governed. The cost of an
unnecessary comment period is two weeks; the cost of an unannounced contract
change is a consumer's migration.

## Two kinds of change, handled differently

**Additive changes land whenever they are ready.** A new annotation key, a new
class, a new shape, a new property: anything that leaves every existing graph
valid and every existing identifier where it was. These are recorded in the
changelog and, where they set a guarantee, in a decision record. They do not
wait for anything, because nobody has to migrate.

**Substantive changes are collected and released together.** A change to an
emitted IRI, a property's range or domain, or a guarantee that stops holding.
Each one costs every consumer a migration, so they arrive in one designated
release rather than trickling. That is the same batching that governed 0.3.0 and
0.11.0; from 1.0 the difference is that the author no longer decides the contents
alone.

When it is unclear which kind something is, it is substantive. Being wrong in
that direction delays a change; being wrong in the other direction breaks a
consumer who was not expecting it.

## The collection window

**A window opens on the day a major release ships and closes one year later.**
Every proposal raised inside it shares that one closing date. The date is
absolute rather than per proposal: a shared deadline is something an adopter can
put in a calendar, and a rolling one is something nobody can plan around.

Inside the window, proposals are raised, discussed, revised, objected to, and
withdrawn. Nothing substantive ships.

**At the closing date the window locks.** No further substantive change enters
that release. What has been collected is implemented and shipped as the next
major version, and a new window opens the day it does.

**A proposal arriving in the last sixty days rolls to the next window.** Not a
penalty; a proposal that nobody has had time to object to has not been agreed to,
and admitting it would make the deadline the only thing that mattered rather than
the discussion.

**Silence at the closing date is assent,** for proposals that were open long
enough to be seen. That is why the window is a year: specl is aimed at
organisations that review their tooling annually, and a change should appear in
at least one review cycle of every adopter who has one.

## How a change is made

1. **Propose.** Open an issue using the specification change template. It states
   what changes, who it affects, whether it breaks the graph contract, and what
   migration it would need.
2. **Announce.** The author notifies every registered adopter on the issue, and
   lists the proposal in `docs/proposals/OPEN.md` against the current window's
   closing date. Silence only counts as assent if the people whose assent
   matters were told, and a register nobody can find is not telling them.
3. **Land it, or collect it.** An additive change is implemented once it is
   agreed and ships in the next ordinary release. A substantive one waits for
   the window to close.
4. **Objections, any time before the lock.** A substantive objection from a
   registered adopter blocks until it is withdrawn or addressed. Substantive
   means it says what breaks or what is wrong, not that it prefers otherwise.
   Objections are not counted or outvoted; with a user base this size, counting
   would be theatre. An unresolved objection at the closing date drops the
   proposal to the next window rather than shipping it over the objection.
5. **Ratify.** A decision record names who commented, what changed in response,
   and any objection raised and how it was resolved. The record is the artifact;
   the issue is the discussion.

## Open proposals are visible in the repository

`docs/proposals/OPEN.md` lists everything collected for the next major release,
with the window's closing date at the top. A shared deadline only helps if it
can be found without having watched the discussion, which is the whole reason
the register exists rather than a label on some issues.

## Who is consulted

Anyone may comment. **Registered adopters** are those who have opened an adopter
registration issue, and they are the ones whose objection blocks and whose
notification is required. Registering costs nothing and is not a commitment to
keep using specl.

With no registered adopters, the period still runs and the decision record notes
that none were registered. The process does not become a formality that is
skipped when inconvenient, because the habit of skipping it is what it exists to
prevent.

## What a major release owes

Every designated release ships with a migration path, as `specl-migrate` does
for both prior contracts. A collected change that turns out to have no mechanical
migration is a change to reconsider rather than to ship with instructions.

The contract version increments once per major release, not once per change in
it, so a consumer pins one number and migrates once.

## Expedited changes

A change may skip the window only when leaving the behavior in place
would cause a consumer active harm: a security defect, or emitting a graph that
is wrong in a way that corrupts downstream data. The author documents the
expedited change in a decision record within seven days, listing what harm was
imminent and why waiting was not possible.

An expedited change remains open to objection until the current window closes,
on the same terms as a proposal. If an objection is sustained, the change is reverted or
amended; shipping first does not settle it.

Convenience, schedule pressure, and the author's confidence are not grounds, and
neither is a change having missed the window. Missing a deadline is what the next
window is for, and reclassifying a late change as urgent is the failure mode that
would empty this document of meaning.

## Amending this document

Governed by the process it describes.
