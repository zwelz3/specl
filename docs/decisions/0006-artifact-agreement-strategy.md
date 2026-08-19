# Keeping artifacts from disagreeing

**Status:** accepted, partly implemented. Applies from 0.3.0 onward.

## Context

Every defect this project has spent a release fixing had one shape. P1: the
ontology declared object properties and the emitter wrote literals. P2: the
shapes required a property the translator could not produce. P16: the
commitments register published a grammar the parser did not implement. P17: the
translator stamped a value no golden file could hold. The version strings: four
copies at three different numbers. The w3id rules: a redirect to a file the build
never produced. The self-specification: fifteen of nineteen verification claims
naming tests that had never existed.

None of these is a hard bug. Each is two artifacts that stopped agreeing, with
nothing comparing them. Fixing them one at a time is what 0.3.0 did. This record
is about not needing to do it again.

The problem is structural rather than careless. A specification language
necessarily has many artifacts describing the same thing: a vocabulary, a shapes
graph, a parser, a syntax reference, a commitments register, a contract page, and
a specification of itself. Each exists for a different reader. Duplication across
them is not a mistake to be eliminated everywhere; it is the cost of serving
those readers, and the job is to make the duplication either impossible or
visible.

## Decision

**Every pair of artifacts that could disagree is assigned a tier, and no pair is
left unassigned.** Adding an artifact means placing it in the inventory below.

**Tier 1, derive.** One artifact is generated from the other, so drift cannot
occur. Preferred wherever the derived form is mechanical.

**Tier 2, compare.** Both are authored independently and a test compares them
mechanically. The comparison runs against real output rather than a restated
list, so the check cannot itself go stale.

**Tier 3, bind.** Where an artifact is prose that cannot be compared, each claim
names the test that asserts it, and both halves are checked: no claim without a
test, no named test that does not exist.

**The changelog was never in this inventory, and it should have been.** A downstream adopter found that its 0.3.0 section claims a shape change that never shipped, and the disposition declining their alternative cited that claim as done. Four entries in that section are false. Most changelog prose cannot be checked mechanically, which is exactly why it was left out and exactly why it drifted: an artifact excluded because it is hard to verify is an artifact nothing verifies. The partial tier above is honest rather than complete, and the process rule in `RELEASING.md` carries the rest.

**A check derived from an artifact beats a check that names its parts.** Every
range check written before `tests/test_ontology.py` named one property, so the
next property added was unchecked by construction, and two were. Derive the
assertion from the declaration and a new term is covered the moment it exists.

**Every check in this inventory compares artifacts to each other, and that is
blind to a claim that is wrong outside the container.** Four defects reached an
adopter this way: repository-relative paths in the README, a Python floor CI
never exercised, a publish workflow contradicting a written policy, and text I/O
assuming the locale encoding. None was a disagreement between artifacts, so
nothing here could have found any of them. Where a claim depends on an
environment, the check has to run in that environment; that is why CI now runs
Windows and installs from a clean clone.

**A check must fail loudly when its own extraction breaks.** A checker that
silently stops checking is worse than no checker, because it reports success. The
subcommand extraction in `tools/check_docs.py` fails when it finds nothing, and
the same rule applies to anything added here.

## Inventory

| Pair | Tier | Held by |
| --- | --- | --- |
| `SUB_RE` keys, `PROP_MAP` | 1 | `SUB_RE` is built from `PROP_MAP` at import |
| shapes graph, translator output | 2 | `tests/test_shapes_coverage.py` |
| `core.ttl` declarations, emitted predicates | 2 | `tests/test_drift.py`, both directions |
| every declared range and domain, emitted output | 2 | `tests/test_ontology.py`, derived from the vocabulary |
| item class list, the vocabulary | 1 | read from `rdfs:subClassOf specl:Item` at import |
| `shapes.ttl`, the SHACL specification | 2 | `meta_shacl` validation in `tests/test_ontology.py` |
| `verifiedBy` claims, the test suite | 2 | `tests/test_drift.py` against pytest collection |
| version strings in four files | 2 | `tools/check_docs.py` |
| w3id redirect targets, the tree and the Pages build | 2 | `tools/check_docs.py` |
| documentation references, code and paths | 2 | `tools/check_docs.py` |
| roadmap exit criteria, behavior | 2 | `tests/test_exit_criteria.py` |
| contract page guarantees, behavior | 3 | `verified-by` comments, checked both ways |
| `SECTION_MAP`, the section table in `docs/SYNTAX.md` | unassigned | see below |
| `PROP_MAP`, the annotation table in `docs/SYNTAX.md` | unassigned | see below |
| explorer field map, the vocabulary | 2 | `tests/test_explorer.py`, both directions |
| changelog claims, behaviour | 3, partial | `Breaking` entries carry `verified-by`; the rest is prose nothing can check |
| assistant prompts, the shapes they target | unassigned | deferred beyond 1.0; see `docs/ROADMAP.md` |
| commitments register, behavior | 2 and 3 | `specs/commitments/spec.md`, `verifiedBy` checked in `tests/test_drift.py` |

## What is not covered yet

Three pairs remain unassigned, and naming them is the point of the inventory.

The two tables in `docs/SYNTAX.md` restate `SECTION_MAP` and `PROP_MAP` in prose.
Both are tier 2 candidates: parse the markdown table, compare to the map. The
`iWant` gap found while writing this record is exactly what that check would
catch, and it was found only because the vocabulary happened to declare a
property nothing could produce.

*Closed.* The commitments register became a specl specification in 0.5.0. Its
clauses are items carrying the consumer's own request identifiers, and
`verifiedBy` binds each implemented one to a test that
`tests/test_drift.py` checks exists. See
`docs/decisions/0008-commitments-as-a-specification.md`. Three pairs remain unassigned: the section table and the annotation table in
`docs/SYNTAX.md`, and the assistant's prompts, which assert what a good
specification looks like while nothing compares them to the shapes they exist to
help satisfy.

## Alternatives

**Eliminate duplication entirely, generating documentation from code.** Rejected.
The syntax reference, the commitments register, and the contract page each exist
for a reader the code does not serve, and generated prose serves none of them
well. Tier 1 is preferred where the derived form is mechanical, which is a
narrower set than it first appears.

**A single check that diffs everything.** Rejected. Each pair disagrees in its
own way, and one check covering all of them would fail with a message nobody can
act on.

**Rely on review.** Rejected on evidence. Every defect in the list above survived
review, several of them across two releases.

## Consequences

The inventory is the deliverable, more than any individual check. A pair absent
from it is a pair nobody has thought about, which is the state every defect in
this record started from.

Two findings arrived while implementing this. `specl:iWant` was declared in the
vocabulary with no authoring path, so a user story could not carry the middle
clause of its own sentence; it is now wired and appears in the syntax table.
Fifteen of nineteen `verifiedBy` claims in specl's own specification named tests
that had never existed. Those claims are repointed at real tests where coverage
exists and removed where it does not, so the specification now understates its
verification rather than overstating it.
