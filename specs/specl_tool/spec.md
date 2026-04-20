---
spec_id: specl-tool-001
title: SPECL Tool
version: 0.3.0
status: prototype
---

# Intent
Specify the SPECL toolchain itself — the parser, validator, scorer, badge generator, LLM assistant, and explorer — so the tool is governed by the same spec-driven process it provides to downstream projects.

# Purpose
Give SPECL a maturity signal of its own. Every capability the tool exposes to consumers must be traceable to a requirement with acceptance criteria, a priority, and a verification artifact.

# Requirements

## R1 Translation
- R1.1 `specl-translate` must parse markdown with YAML front-matter, H1 sections, ID-bulleted items (R, US, OQ, D prefixes), and indented sub-bullet annotations into valid Turtle.
  - priority: MUST
  - constrains: spec_to_rdf
  - acceptance: Given any markdown spec conforming to docs/SYNTAX.md, when translated, the output parses without error in rdflib and every ID-bulleted item appears as a typed individual with specl:partOf linking to the spec.
  - verifiedBy: tests/test_translate.py::test_roundtrip
- R1.2 Sub-bullet annotations must populate structured RDF properties (priority, acceptance, verifiedBy, constrains, asA, soThat, owner, recommendation, status, rationale, affects).
  - priority: MUST
  - constrains: spec_to_rdf
  - acceptance: Given a requirement with all annotation keys, when translated, the output contains the corresponding specl: triples with correct property names.
  - verifiedBy: tests/test_translate.py::test_annotations
- R1.3 Comma-separated values on constrains and affects sub-bullets must produce multiple triples. Prose keys must not split on commas.
  - priority: MUST
  - constrains: spec_to_rdf
  - acceptance: Given `constrains: A, B`, output has two specl:constrains triples. Given `acceptance: Given X, when Y`, output has one specl:acceptanceCriterion triple with the full comma-containing string.
  - verifiedBy: tests/test_translate.py::test_multi_value
- R1.4 Specs without sub-bullet annotations must produce identical output to specl 0.1.x.
  - priority: MUST
  - constrains: spec_to_rdf
  - acceptance: Given the EKGA reference spec with no sub-bullets, the translated subject set is identical to the 0.1.x golden file.
  - verifiedBy: tests/test_translate.py::test_backward_compat
- R1.5 The `--strict` flag must print parser warnings to stderr without failing the translation.
  - priority: SHOULD
  - constrains: spec_to_rdf
  - acceptance: Given a spec with an unrecognized annotation key, when translated with --strict, stderr contains a warning and the exit code is 0.
  - verifiedBy: tests/test_translate.py::test_strict_warnings

## R2 Validation
- R2.1 `specl-validate validate` must run the SHACL shapes graph against a translated spec and report violations and warnings.
  - priority: MUST
  - constrains: validate_spec
  - acceptance: Given a spec.ttl with a missing dct:description on a Requirement, validation reports a Violation.
  - verifiedBy: tests/test_validate.py::test_violation_detection
- R2.2 The severity gate must be driven by the spec's own specl:status value.
  - priority: MUST
  - constrains: validate_spec
  - acceptance: Given a spec at status draft with Warnings only, validate exits 0. Given status production with Warnings, validate exits 1.
  - verifiedBy: tests/test_validate.py::test_severity_gate
- R2.3 `specl-validate score` must report a maturity percentage based on production-ready requirements.
  - priority: MUST
  - constrains: validate_spec
  - acceptance: Given 3 of 10 requirements with all four production properties, score reports 30%.
  - verifiedBy: tests/test_validate.py::test_score
- R2.4 `specl-validate badge` must produce a valid SVG file with color reflecting the maturity score.
  - priority: SHOULD
  - constrains: validate_spec
  - acceptance: Given a score of 40%, the badge SVG contains fill color matching the red threshold.
  - verifiedBy: tests/test_validate.py::test_badge
- R2.5 `specl-validate diff` must report added, removed, and modified requirements between two Turtle files.
  - priority: SHOULD
  - constrains: validate_spec
  - acceptance: Given old.ttl with R1.1 and new.ttl with R1.1 (changed) and R1.2 (added), diff reports 1 added and 1 modified.
  - verifiedBy: tests/test_validate.py::test_diff

## R3 Namespaces
- R3.1 All generated Turtle must use `https://w3id.org/specl/ns#` as the vocabulary namespace and `https://w3id.org/specl/spec#` as the instance namespace.
  - priority: MUST
  - constrains: spec_to_rdf, core_ttl
  - acceptance: Given any spec, translated output prefixes are specl: and spec: pointing to the w3id.org URIs.
  - verifiedBy: tests/test_translate.py::test_namespace_iris

## R4 Explorer
- R4.1 The explorer must be a single self-contained HTML file under 30 KB.
  - priority: MUST
  - constrains: explorer
  - acceptance: explorer.html file size is under 30720 bytes and contains no external resource references.
  - verifiedBy: tests/test_explorer.py::test_size_and_self_contained

## R5 LLM Assistant
- R5.1 `specl-assist gaps` must read SHACL warnings and draft remediation prompts via Ollama.
  - priority: SHOULD
  - constrains: spec_assistant
  - acceptance: Given a spec with warnings and a running Ollama instance, gaps prints a draft for each warning.
  - verifiedBy: tests/test_assist.py::test_gaps
- R5.2 `specl-assist check` must flag contradictions and duplications across requirements.
  - priority: SHOULD
  - constrains: spec_assistant
  - acceptance: Given a spec with two requirements that contradict, check output includes a finding referencing both.
  - verifiedBy: tests/test_assist.py::test_check

## R6 Packaging
- R6.1 The package must be installable via `pip install specl` and register three console scripts.
  - priority: MUST
  - constrains: pyproject
  - acceptance: After pip install, specl-translate, specl-validate, and specl-assist are on PATH and --help works.
  - verifiedBy: tests/test_install.py::test_entry_points
- R6.2 shapes.ttl, core.ttl, and explorer.html must be included as package data.
  - priority: MUST
  - constrains: pyproject
  - acceptance: After pip install, importlib.resources.files('specl').joinpath('shapes.ttl') resolves.
  - verifiedBy: tests/test_install.py::test_package_data

# User Stories

- US1 As a spec author, I run specl-translate on my markdown, specl-validate to check it, and see a maturity score that climbs as I add annotations.
- US2 As a CI pipeline, I run specl-validate on every PR and fail the build if a production-status spec has violations or warnings.
- US3 As an AI agent, I read the translated spec.ttl to understand what a system should do before generating code.

# Open Questions and Gaps

- Whether to add a `specl init <name>` scaffolding command that creates a new spec directory with a template spec.md. Recommendation: add in 0.4.0.
- Whether specl-validate should default to the bundled shapes.ttl via importlib.resources when no shapes path is given. Recommendation: implement in 0.3.0 to reduce CLI verbosity.
- Whether to support a `namespace_style: hash | slash` front-matter key for specs that want per-element slash URIs (Schema.org pattern). Recommendation: defer to 0.4.0.
