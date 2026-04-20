# specl changelog

## 0.3.0

Stable namespace, self-evaluation, and CI infrastructure.

### Added

- **Stable w3id.org namespace.** All generated Turtle now uses
  permanent identifiers: `https://w3id.org/specl/ns#` (vocabulary,
  prefix `specl:`) and `https://w3id.org/specl/spec#` (instances,
  prefix `spec:`). The old `https://example.org/ekga/ns#` namespace
  and `ekga:` prefix are retired. See `NAMESPACE-MIGRATION.md` for
  the rationale and w3id.org setup instructions.
- **`specl_tool` spec** — SPECL now evaluates its own maturity. The
  new `specs/specl_tool/spec.md` covers the parser, validator, scorer,
  badge generator, LLM assistant, explorer, and packaging (16
  requirements, all fully annotated, 100% maturity at ship).
- **Maturity badges auto-committed by CI.** The `spec.yml` workflow
  generates SVG badges for every spec and commits them to
  `static/badges/` on pushes to `main`. Badges are git-tracked and
  referenced in the README via `raw.githubusercontent.com` so they
  render without depending on GitHub Pages.
- **GitHub Pages deployment.** The `pages.yml` workflow publishes the
  ontology (`ns.ttl`), SHACL shapes (`shapes.ttl`), the spec explorer
  (`explorer.html`), committed badges, and a vocabulary landing page
  to `zwelz3.github.io/specl/`. This is the dereference target for
  the w3id.org redirects.
- **Vocabulary landing page** at `static/index.html` documenting all
  SPECL classes, key properties, and namespace URIs. Served as the
  GitHub Pages index.
- **PyPI badge** in the README header (`img.shields.io/pypi/v/specl`).
- **Conda note** after the install section indicating a conda-forge
  recipe is in progress.

### Changed

- **Prefix rename: `ekga:` → `specl:`** across all source files,
  shapes, ontology, explorer, and documentation. The `ekga:` prefix
  was an artifact of the first downstream project; `specl:` matches
  the package name and is semantically correct for a general-purpose
  spec language.
- **Hash namespaces for both vocabulary and instances.** Both
  `specl:` and `spec:` use `#` (not `/`). Hash namespaces resolve
  all terms to a single document, which is the right model for
  specs authored and consumed as a unit. Slash namespace support
  (Schema.org pattern) is tracked as an open issue for a future
  release.
- **GitHub Actions updated to Node 24.** `actions/checkout@v6` and
  `actions/setup-python@v6` (native Node 24), plus
  `FORCE_JAVASCRIPT_ACTIONS_TO_NODE24=true` for actions that have
  not yet released Node 24 versions. Python bumped to 3.12.
- **`pip install specl`** in the README (was `pip install -e .`).

### Deferred

- Multi-file specs via front-matter `companion_files` key.
- `specl suggest-annotations` subcommand.
- Priority-weighted maturity scoring.
- Slash namespace support via `namespace_style: hash | slash`
  front-matter key.

## 0.2.0

Parser extension for structured per-item annotations. Addresses the
core limitation that prototype-status specs could not reach non-zero
maturity without external tooling.

### Added

- **Sub-bullet annotations** under any ID-bulleted item. Sub-bullets
  at two or more spaces of indent with a recognized key produce
  structured RDF triples. Recognized keys: `priority`, `acceptance`,
  `verifiedBy`, `constrains`, `asA`, `soThat`, `owner`, `recommendation`,
  `status`, `rationale`, `affects`. See `docs/SYNTAX.md`.
- **Comma-separated multi-values** on `constrains:` and `affects:`
  sub-bullets. Prose-heavy keys (`acceptance`, `verifiedBy`) do not
  split on commas — use multiple sub-bullets for multiple values.
- **OpenIssue ID prefix `OQ`** (e.g., `OQ1`). Previously open issues
  were auto-slugged from their description; `OQ`-prefixed items now
  produce stable IRIs and accept sub-bullet annotations (`owner`,
  `recommendation`, `status`).
- **DecisionRecord support**. New section `# Decisions` recognized,
  with `D`-prefixed IDs and sub-bullet annotations (`status`,
  `rationale`, `affects`). `status:` is context-sensitive and maps to
  `specl:decisionStatus` for decisions, `specl:resolutionStatus` for
  open issues.
- **Front-matter comment block** `<!--specl ... -->` for
  spec-level metadata that does not belong in YAML front-matter. First
  supported key: `created:` (overrides the default of today's date).
- **`--strict` flag** on `specl-translate` prints parser warnings
  to stderr (unrecognized annotation keys, orphaned sub-bullets,
  prefix mismatches). Warnings are non-fatal.

### Changed

- Turtle output now uses one-property-per-line formatting (added in
  0.1.x, reconfirmed in 0.2.0 for readability and clean git diffs).
- Section `# Open Issues` is now recognized alongside
  `# Open Questions` and `# Open Questions and Gaps (flag for follow-up)`.

### Backward compatibility

Existing specs without sub-bullet annotations produce byte-identical
RDF to 0.1.x (same subject set, same triples). The EKGA reference
spec was used as the golden-file fixture during development.

### Deferred to 0.3.0

- Multi-file specs via front-matter `companion_files` key (Phase 4 of
  the enhancement plan).
- `specl suggest-annotations` subcommand for scaffolding missing
  sub-bullets (Phase 5).
- Priority-weighted maturity scoring (distinguish clean MUSTs from
  clean SHOULDs).

## 0.1.0

Initial release.
