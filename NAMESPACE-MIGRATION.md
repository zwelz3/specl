# Namespace migration

Referenced by the 0.3.0 changelog entry. Describes a different migration than
that entry originally planned: the instance namespace is not moving to a
specl-owned permanent identifier, it is moving to the consuming project.

## Why the original plan changed

The unreleased work moved instances to `https://w3id.org/specl/spec#`, a single
hash namespace shared by every specification authored with specl, by anyone.
Every project would mint `https://w3id.org/specl/spec#R1`.

This repository demonstrates the collision. Translating
`tests/fixtures/excel_service` and `tests/fixtures/pptx_templater` and merging
the results yields 11 shared item IRIs.
The node `spec#R1.1` then carries two descriptions, one about an HTTP POST
endpoint and one about preserving master slides, and is `specl:partOf` both
`spec#xlsvc-001` and `spec#pptxgen-001`.

Under `example.org` this was a latent defect. Under w3id.org, chosen for
permanence, it is an identifier commitment that cannot be walked back.

The principle applied instead: a user's requirements are the user's data. The
vocabulary is specl's artifact and belongs at a permanent community identifier.
Instances are not, and do not.

## Namespaces by version

| Version              | Vocabulary                     | Instances                        |
| -------------------- | ------------------------------ | -------------------------------- |
| 0.1.0 – 0.2.0 (PyPI) | `https://example.org/ekga/ns#` | `https://example.org/ekga/spec/` |
| unreleased `main`    | `https://w3id.org/specl/ns#`   | `https://w3id.org/specl/spec#`   |
| 0.3.0 onward         | `https://w3id.org/specl/ns#`   | project-supplied, required       |

`https://w3id.org/specl/spec#` is retired, not partitioned. The w3id.org
redirects are needed for vocabulary terms only, which narrows what this project
owes indefinitely.

## What a specification must declare from 0.3.0

```yaml
spec_id: xlsvc-001
prefix: XLSVC
spec_base: https://spec.example.org/xlsvc-001#
```

`spec_base` is mandatory. Translation fails without it rather than defaulting,
because a default that is right only for the person who chose it is how the
collision above arose.

Grammar, as specified to downstream consumers:

- Hash termination is required. A value not ending in `#` is rejected; the
  terminator is not appended silently.
- A bare authority with no path segment is rejected.
- A value carrying a fragment beyond the terminating `#` is rejected.
- Slash-terminated bases are unsupported until a post-1.0 extension.

Item identifiers stay bare in the markdown. Namespacing applies to the emitted
IRI. In prose and across specifications, items are written as CURIEs
(`XLSVC:R1.1`), which become legal inside reference-valued annotations at 0.5.0.

## Migrating an existing specification

**If you have the source markdown, regenerate.** Add `spec_base` and `prefix` to
front matter and translate again. This is the supported path.

Verify with `specl-validate diff --ignore-base` against the pre-migration graph. It
normalizes instance IRIs in both graphs before comparison, so a correct migration
reports no difference and any content change stands out. This matters because
0.3.0 changes several dimensions at once: IRIs, two property ranges, a new title
key, and a header field.

**If you hold only Turtle**, use `specl-migrate iris <old.ttl> <new.ttl>
--spec-base <iri>`. It rewrites the legacy namespace into the supplied base and
converts `affects`, `constrains`, and `verifiedBy` from literals to IRIs. It
detects the source scheme by prefix binding and fails rather than guessing when
neither legacy binding is present. Because the retiring namespace conflated
specifications, it refuses to run on a merged graph containing more than one
`specl:Specification`.

## Reference resolution

Resolution is string concatenation onto the base, not RFC 3986 relative
resolution: `base + token`, token verbatim. Dotted identifiers such as `R2.1` are
therefore safe under any base shape, and identifier legality does not depend on
base shape.

A token that does not match the identifier grammar produces a parser warning and
is emitted as a literal rather than being discarded.

## w3id.org setup

The redirects are required for vocabulary terms under
`https://w3id.org/specl/ns#`, resolving to the Pages deployment that serves
`ns.ttl`, `shapes.ttl`, and the vocabulary landing page. No redirect is needed
for instances, since specl no longer mints them.

## Migrating the markdown

`specl-migrate contract old.ttl new.ttl` moves a graph. A project that still has
its source should regenerate instead, and `specl-migrate source spec.md new.md`
prepares it: the annotation keys renamed in contract 2 are rewritten, and
anything needing a judgement is reported rather than guessed.

Two things are deliberately not automated. An `owner` or `role` that names a
person becomes a reference to a declared agent or persona, and choosing how many
distinct people those names represent is not the tool's call: matching on the
string is exactly the fragmentation the change exists to prevent. Design notes
and comments need identifiers, and the numbering belongs to whoever knows what
the notes are about.

The command exits 3 when either applies, listing the values and where to declare
them.
