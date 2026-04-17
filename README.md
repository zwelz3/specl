# specl

RDF-native, SHACL-validated specifications for spec-driven AI development.

Specs are authored in markdown with stable IDs (`R1.2`, `US3`), translated to RDF, validated against a tiered SHACL shapes graph, and scored for maturity. Designed to be the durable source of truth that AI coding agents read before they write.

## Install

```bash
pip install -e .
```

## Quick start

```bash
# Translate the EKGA spec to Turtle
specl-translate specs/ekga/spec.md specs/ekga/spec.ttl

# Validate with explanations
specl-validate validate specs/ekga/spec.ttl src/specl/shapes.ttl --explain

# Maturity score
specl-validate score specs/ekga/spec.ttl src/specl/shapes.ttl

# Diff two versions (auto-appends CHANGELOG.spec.md)
specl-validate diff old.ttl new.ttl

# Badge
specl-validate badge specs/ekga/spec.ttl src/specl/shapes.ttl --out badge.svg

# LLM gap interrogator (requires local Ollama)
specl-assist gaps specs/ekga/spec.ttl src/specl/shapes.ttl --model llama3.1

# Consistency check
specl-assist check specs/ekga/spec.ttl --model llama3.1
```

## Severity tiers

SHACL shapes are split two ways so specs can evolve:

- **Violations** — structural. Always fail. A spec that violates these is broken.
- **Warnings** — production-readiness. Accumulate during prototyping, block only when `ekga:status "production"`.

The gate reads status from the spec itself, so no CI reconfiguration is needed as the spec matures.

## Layout

```
specl/
├── src/specl/          # Python package
│   ├── spec_to_rdf.py      # markdown -> Turtle
│   ├── validate_spec.py    # validate / diff / score / badge
│   ├── spec_assistant.py   # LLM gap interrogator + consistency checker
│   ├── shapes.ttl          # tiered SHACL shapes
│   ├── core.ttl            # ekga-core ontology stub
│   └── explorer.html       # lightweight read-only spec viewer
├── specs/
│   ├── ekga/               # Enterprise Knowledge Graph App (WIP)
│   ├── html_presenter/     # Interactive HTML presentations
│   ├── pptx_templater/     # PowerPoint corporate template filler
│   └── excel_service/      # Excel generation service
├── .github/workflows/      # CI validation
└── .pre-commit-config.yaml
```

## Spec explorer

Open `src/specl/explorer.html` in a browser and drop a generated `spec.ttl` file to browse requirements, user stories, and open issues. Read-only, zero build, no server.

## Authoring

Write specs in markdown under `specs/<name>/spec.md`. Use ID-bulleted lists for requirements (`R1.1`), user stories (`US1`), and open issues. The spec file itself carries YAML frontmatter with `spec_id`, `title`, `version`, and `status`. See `specs/ekga/spec.md` for the reference example.

## Deferred features

See `specs/ekga/ISSUES.md` for traceability registries, domain extension patterns, and other items scheduled for future iterations.
