![specl](./static/logo-sm.png)

# specl

[![PyPI](https://img.shields.io/pypi/v/specl)](https://pypi.org/project/specl/)
[![spec maturity](https://zwelz3.github.io/specl/badges/specl_tool.svg)](https://zwelz3.github.io/specl/explorer.html)

RDF-native, SHACL-validated specifications for spec-driven AI development.

Specs are authored in markdown with stable IDs (`R1.2`, `US3`), translated to RDF, validated against a tiered SHACL shapes graph, and scored for maturity. Designed to be the durable source of truth that AI coding agents read before they write.

## Install

```bash
pip install specl
```

> **conda** — a conda-forge recipe is in progress. Track it at [zwelz3/specl#issues](https://github.com/zwelz3/specl/issues).

## Quick start

```bash
# Translate the specl_explorer spec to Turtle
specl-translate specs/specl_explorer/spec.md specs/specl_explorer/spec.ttl

# Validate with explanations
specl-validate validate specs/specl_explorer/spec.ttl src/specl/shapes.ttl --explain

# Maturity score
specl-validate score specs/specl_explorer/spec.ttl src/specl/shapes.ttl

# Diff two versions (auto-appends CHANGELOG.spec.md)
specl-validate diff old.ttl new.ttl

# Badge
specl-validate badge specs/specl_explorer/spec.ttl src/specl/shapes.ttl --out badge.svg

# LLM gap interrogator (requires local Ollama)
specl-assist gaps specs/specl_explorer/spec.ttl src/specl/shapes.ttl --model llama3.1

# Consistency check
specl-assist check specs/specl_explorer/spec.ttl --model llama3.1
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
│   ├── specl_tool/          # SPECL tool itself (dogfood)
│   ├── specl_explorer/      # Spec explorer component
│   ├── html_presenter/      # Interactive HTML presentations
│   ├── pptx_templater/      # PowerPoint corporate template filler
│   └── excel_service/       # Excel generation service
├── .github/workflows/      # CI validation
└── .pre-commit-config.yaml
```

## Spec explorer

Open `src/specl/explorer.html` in a browser and drop a generated `spec.ttl` file to browse requirements, user stories, and open issues. Read-only, zero build, no server.

## Authoring

Write specs in markdown under `specs/<name>/spec.md`. Use ID-bulleted lists for requirements (`R1.1`), user stories (`US1`), and open issues. The spec file itself carries YAML frontmatter with `spec_id`, `title`, `version`, and `status`. See `specs/specl_explorer/spec.md` for the reference example.

## Deferred features

See `specs/specl_explorer/ISSUES.md` for traceability registries, domain extension patterns, and other items scheduled for future iterations.