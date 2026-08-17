![specl](./static/logo-sm.png)

# specl

> **Contributors and agents:** start with [HANDOFF.md](HANDOFF.md), then
> [CLAUDE.md](CLAUDE.md). Before changing anything that alters emitted output,
> read [docs/DOWNSTREAM-COMMITMENTS.md](docs/DOWNSTREAM-COMMITMENTS.md); a
> consumer has already authored against several behaviors specified there.

[![spec maturity](https://raw.githubusercontent.com/zwelz3/specl/main/static/badges/specl_tool.svg)](https://github.com/zwelz3/specl/blob/main/specs/specl_tool/spec.md)

RDF-native, SHACL-validated specifications for spec-driven AI development.

Specs are authored in markdown with stable IDs (`R1.2`, `US3`), translated to RDF, validated against a tiered SHACL shapes graph, and scored for maturity. Designed to be the durable source of truth that AI coding agents read before they write.

## How changes are decided

From 1.0 the author does not change the specification unilaterally.

Additive changes, which leave every existing graph valid, land whenever they are
ready. Substantive ones, which cost you a migration, are collected in a window
that opens when 1.0 ships and closes a year later, and are released together as
2.0. A substantive objection from a registered adopter blocks. Implementation,
ergonomics, and documentation are not governed at all, so a defect fix does not
need permission.

See [GOVERNANCE.md](GOVERNANCE.md) and `docs/proposals/OPEN.md` for what is
currently collected. Register as an adopter if you want to be notified.

## Concepts

A **specification** is one or more markdown files with front matter declaring
`spec_base`, the namespace its items are identified under. specl never invents
that namespace: identifiers are permanent, and a tool that guesses at them is
guessing at something you cannot take back.

An **item** is an identified thing inside a specification. Eight classes:
requirements, user stories, open questions, decision records, design notes,
comments, acceptance queries, and personas. Each is a bullet with an identifier,
optionally annotated with sub-bullets. An item's IRI is the base concatenated
with its identifier, so `R1.2` in one specification can never collide with
`R1.2` in another.

**Reference-valued annotations resolve to IRIs, not strings.** `affects: R8`
points at a requirement, `constrains: engine` at a component, `role: P1` at a
declared persona. Traceability is graph traversal rather than string matching,
which is the reason for the RDF.

**Three measurements, deliberately separate.** Maturity is how completely a
specification is written, derived from SHACL findings and weighted by priority.
Progress is how much is built, rolled up from per-item `implementation:` status.
Verification coverage is not modelled yet and is named as absent rather than
implied.

**The graph contract** is what a consumer pins. `dct:conformsTo` names it in
every emitted graph, and it changes only in a release designated for breaking
changes. See [docs/contracts/2.md](docs/contracts/2.md).

## Requirements

Python 3.11 or newer. `rdflib`, `pyshacl`, and `PyYAML`, all installed with the
package.

SHACL validation needs nothing extra. `pyshacl` is a required dependency, so
`specl-validate` works the moment the package is installed, and it refuses to
run rather than report a misleading pass if the processor it finds does not
apply the features these shapes need.

It matters if you validate with **your own** SHACL processor, in a Java
pipeline or an existing quality-gate service. These shapes use SPARQL-based
targets and constraints, which SHACL makes an optional feature, and a processor
without them does not error: it silently applies almost nothing, so a
specification full of defects validates clean. The vocabulary must also be
available to the processor, because shapes that consult the class hierarchy run
their SPARQL against the data graph.

Check your processor rather than assume:

```bash
specl-validate conformance                 # checks the bundled processor
specl-validate conformance --export ./conf # fixture, shapes, vocabulary, expectations
```

The exported fixture carries one defect of each kind with the findings a
conforming processor produces. A processor lacking Advanced Features reports
none of the seven.

specl is a command-line tool rather than a library. The modules under
`src/specl/` have no supported public API and their signatures change between
releases; drive it through the commands below.

## Install

Install from the repository. PyPI carries 0.2.0 and will carry only 0.2.0 until
1.0; see `docs/decisions/0007-internal-releases-until-1.0.md`.

```bash
pip install git+https://github.com/zwelz3/specl
```

`pip install specl` returns 0.2.0, which predates the 0.3.0 corrections: item
IRIs collide across specifications, decision records cannot pass their own gate,
reference-valued properties carry literals instead of IRIs, and every graph is
stamped with the time it was translated. It is outdated rather than dangerous
and stays on PyPI for anyone pinned to it.

## Quick start

```bash
# Translate a spec to Turtle
specl-translate spec.md spec.ttl

# Validate with explanations
specl-validate validate spec.ttl --explain          # shapes default to the bundled ones

# Maturity score
specl-validate score spec.ttl

# Badge, linked to the specification's own IRI
specl-validate badge spec.ttl --out badge.svg   # prints the markdown snippet

# Diff two versions (--changelog PATH to record; --ignore-base across a rebase)
specl-validate diff old.ttl new.ttl

# Badge
specl-validate badge spec.ttl --out badge.svg

# LLM gap interrogator (any OpenAI-compatible endpoint; local Ollama by default)
specl-assist gaps spec.ttl --provider claude --api-key $ANTHROPIC_API_KEY

# Consistency check
specl-assist check spec.ttl --provider claude --api-key $ANTHROPIC_API_KEY
```

## Severity tiers

SHACL shapes are split two ways so specs can evolve:

- **Violations** — structural. Always fail. A spec that violates these is broken.
- **Warnings** — production-readiness. Accumulate during prototyping, block only when `specl:status "production"`.

The gate reads status from the spec itself, so no CI reconfiguration is needed as the spec matures.

## Namespaces

SPECL uses permanent w3id.org identifiers so IRIs survive hosting changes:

| Prefix | URI | Purpose |
|--------|-----|---------|
| `specl:` | `https://w3id.org/specl/ns#` | Vocabulary (classes, properties) |
| `spec:` | `https://w3id.org/specl/spec#` | Spec instances (requirements, stories) |

Both use **hash namespaces** (`#`). This means every term in a namespace resolves to a single document — one HTTP request returns the full ontology or the full spec. This is the right choice when terms are defined together and make sense as a unit (the way SHACL uses `https://www.w3.org/ns/shacl#`).

The alternative is **slash namespaces** (`/`), where each term is its own URL and can return its own document. This is the pattern Schema.org uses (`https://schema.org/Person`, `https://schema.org/Organization`) so each concept has a dedicated page. SPECL may support slash namespaces in a future release for specs that want per-element hosting — see the roadmap in the SPECL spec.

## Layout

```
specl/
├── src/specl/          # Python package
│   ├── spec_to_rdf.py      # markdown -> Turtle
│   ├── validate_spec.py    # validate / diff / score / badge
│   ├── spec_assistant.py   # LLM gap interrogator + consistency checker
│   ├── shapes.ttl          # tiered SHACL shapes
│   ├── core.ttl            # specl-core ontology stub
│   └── explorer.html       # lightweight read-only spec viewer
├── specs/
│   ├── specl_tool/         # SPECL tool itself (dogfood)
│   └── specl_explorer/     # spec explorer component
├── tests/fixtures/         # example specs used as the test corpus
├── tools/                  # repository checks and the w3id redirect source
├── docs/decisions/         # accepted decisions
├── .github/workflows/      # CI validation
└── .pre-commit-config.yaml
```

## Spec explorer

Open `src/specl/explorer.html` in a browser and drop a generated `spec.ttl` file to browse requirements, user stories, and open issues. Read-only, zero build, no server.

## Authoring

Write specs in markdown under `specs/<name>/spec.md`. Use ID-bulleted lists for requirements (`R1.1`), user stories (`US1`), and open issues. The spec file itself carries YAML frontmatter with `spec_id`, `title`, `version`, and `status`. See `specs/specl_explorer/spec.md` for the reference example.

## Assistant providers

The assistant speaks the OpenAI chat-completions shape, which every provider
below accepts, so there is one code path rather than one adapter per vendor.

```bash
specl-assist gaps spec.ttl shapes.ttl --provider claude --api-key $ANTHROPIC_API_KEY
specl-assist gaps spec.ttl shapes.ttl              # local Ollama, the default
specl-assist gaps spec.ttl shapes.ttl --endpoint https://gateway.example/v1/chat/completions
```

`--provider` accepts `ollama`, `claude`, `openai`, `vllm`, and `llamacpp`.
Anthropic publishes an OpenAI-compatible layer, so Claude needs a URL rather
than an adapter. `--endpoint` overrides it, and `SPECL_LLM_ENDPOINT` and
`SPECL_LLM_API_KEY` cover the environment case. A bearer token is sent only when
one is configured.

`suggest-annotations` calls no model at all. It reads the shapes.

## Fitting it into a workflow

**Author, translate, validate.** Keep `spec.md` beside the code it specifies.
Translate on every change and validate the result. `--fail-on-warning` turns
parser warnings into a failure once a specification is clean enough to hold that
line.

**Gate in CI.** This repository's own `.github/workflows/spec.yml` is the worked
example: translate with `--fail-on-warning`, validate with `--json` for a
machine-readable report, score, and commit a badge. The severity gate is driven
by the specification's own `status`, so a `draft` specification fails only on
violations while a `production` one fails on warnings too. A specification
tightens by changing one word in its front matter rather than by changing the
pipeline.

**Commit the Turtle, or do not.** Committing it makes `specl-validate diff`
between revisions trivial and makes the graph reviewable in pull requests.
Regenerating it in CI keeps the repository smaller. Translation is deterministic
either way, so the choice has no correctness consequence.

**Track direction, not just state.** `specl-validate score --history
history.ttl` appends each assessment as a `prov:Activity`. A single maturity
number answers nothing about whether a specification is converging; a series
does.

**Retire, do not delete.** Mark an item `itemStatus: superseded` and name its
replacement with `supersededBy:`. Identifiers are permanent, `diff` reports
reuse of a withdrawn identifier as a failure, and a reader following a chain
lands somewhere that explains itself.

**Split when it gets long.** `companion_files` merges several markdown files into
one specification, and each item's provenance still names the file and line it
came from.

**Across several specifications.** Declare foreign prefixes under `references:`
with a base and a local path, then reference `SBL:D14` from a requirement.
`specl-validate layering` checks those references against declared upstream and
downstream relations, never touches the network, and reports inconclusive rather
than passing when a peer cannot be read.

**With an agent.** The specification is the durable artifact an agent reads
before writing code, and the shapes are what tell it what is still missing.
`specl-assist suggest-annotations` prints pasteable stubs for the gaps and calls
no model to do it.

## Deferred features

See `docs/ROADMAP.md` for the release train through 0.11, including cross-specification references, provenance, multi-file specifications, and the conditions for declaring 1.0.