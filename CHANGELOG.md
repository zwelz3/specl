# specl changelog

## 0.2.1

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
  0.1.x, reconfirmed in 0.2.1 for readability and clean git diffs).
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
