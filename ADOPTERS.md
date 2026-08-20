# Registered adopters

Who is notified when a specification change is proposed, and whose sustained objection blocks ratification. See [GOVERNANCE.md](GOVERNANCE.md).

Registering costs nothing and commits you to nothing. Open an adopter registration issue; it is transcribed here and then closed, because a registry belongs in the repository rather than in issue search. Ask to be removed at any time and the row goes.

| GitHub | Using specl for | How | Constraints worth knowing |
| --- | --- | --- | --- |
| *none yet* | | | |

## Why this is a file

Every other register here is one: the commitments in `specs/commitments/spec.md`, the decisions in `docs/decisions/`, the open proposals in `docs/proposals/OPEN.md`. A registry that lives in a GitHub issue filter is diffable by nobody, reviewable in no pull request, and unavailable to anything that does not have API access.

It also has to be enumerable at proposal time. Silence counts as assent, which is only defensible if every person whose assent is being inferred was told, and that means reading a list rather than remembering one.

## The constraints column

The most useful thing an adopter records. Air-gapped operation, a SHACL processor other than pyshacl, identifiers already published, graphs already distributed: these are what turn an abstract breaking change into a known cost for a named party. Two of the four defects fixed before 1.0 were found because a downstream consumer had stated a constraint that made the defect matter.
