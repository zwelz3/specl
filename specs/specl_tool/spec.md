---
spec_base: https://w3id.org/specl/tool/spec#
prefix: TOOL
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
  - verifiedBy: tests/test_golden.py::test_translation_matches_golden
- R1.2 Sub-bullet annotations must populate structured RDF properties (priority, acceptance, verifiedBy, constrains, role, capability, benefit, owner, recommendation, decisionStatus, resolutionStatus, rationale, affects).
  - priority: MUST
  - constrains: spec_to_rdf
  - acceptance: Given a requirement with all annotation keys, when translated, the output contains the corresponding specl: triples with correct property names.
  - verifiedBy: tests/test_shapes_coverage.py::test_violation_paths_are_producible
- R1.3 Comma-separated values on constrains and affects sub-bullets must produce multiple triples. Prose keys must not split on commas.
  - priority: MUST
  - constrains: spec_to_rdf
  - acceptance: Given `constrains: A, B`, output has two specl:constrains triples. Given `acceptance: Given X, when Y`, output has one specl:acceptanceCriterion triple with the full comma-containing string.
  - verifiedBy: tests/test_references.py::test_external_artifacts_become_typed_nodes_with_readable_iris
- R1.4 Specs without sub-bullet annotations must produce identical output to specl 0.1.x.
  - priority: MUST
  - constrains: spec_to_rdf
  - acceptance: Given the EKGA reference spec with no sub-bullets, the translated subject set is identical to the 0.1.x golden file.
- R1.5 The `--strict` flag must print parser warnings to stderr without failing the translation. Retained for compatibility; it selects behavior that R1.6 makes unconditional.
  - priority: SHOULD
  - constrains: spec_to_rdf
  - acceptance: Given a spec with an unrecognized annotation key, when translated with --strict, stderr contains a warning and the exit code is 0.
  - verifiedBy: tests/test_warnings.py::test_strict_still_exits_zero
- R1.6 Parser warnings must print to stderr on every translation, with no flag required, followed by a count naming the source file. A warning that appears only behind a flag is one nobody reads.
  - priority: MUST
  - constrains: spec_to_rdf
  - acceptance: Given a spec with an unrecognized annotation key, when translated with no flags, stderr contains the warning and a count line.
  - verifiedBy: tests/test_warnings.py::test_warnings_print_without_any_flag
- R1.8 An indented bullet that names no known annotation key must be read as nested content when it sits at four or more columns, and must warn as a probable typo below that. Nested lines attach to the item as an `rdf:List` on `specl:detail` in source order, with IRI-named cells rather than blank nodes.
  - priority: MUST
  - constrains: spec_to_rdf
  - acceptance: Given a requirement with a four-column sub-list of unrecognized keys, translation emits an rdf:List on specl:detail containing those lines in order, every node in the graph is an IRI, and no warning is produced. Given the same lines at two columns, translation warns.
  - verifiedBy: tests/test_nested_content.py::test_nested_content_becomes_detail
- R1.7 The `--fail-on-warning` flag must exit non-zero when the parser produced any warning, after writing the output file. The output is written either way, because reading the emitted graph is how the cost of a dropped line is seen.
  - priority: MUST
  - constrains: spec_to_rdf
  - acceptance: Given a spec with an unrecognized annotation key, when translated with --fail-on-warning, the output file exists and the exit code is 1. Given a spec with no warnings, the exit code is 0.
  - verifiedBy: tests/test_warnings.py::test_fail_on_warning_gates

## R2 Validation
- R2.1 `specl-validate validate` must run the SHACL shapes graph against a translated spec and report violations and warnings.
  - priority: MUST
  - constrains: validate_spec
  - acceptance: Given a spec.ttl with a missing dct:description on a Requirement, validation reports a Violation.
  - verifiedBy: tests/test_exit_criteria.py::test_criterion_3_a_decisions_section_validates
- R2.2 The severity gate must be driven by the spec's own specl:status value.
  - priority: MUST
  - constrains: validate_spec
  - acceptance: Given a spec at status draft with Warnings only, validate exits 0. Given status production with Warnings, validate exits 1.
  - verifiedBy: tests/test_score.py::test_score_and_gate_never_disagree_in_sign
- R2.3 `specl-validate score` must report a maturity percentage based on production-ready requirements.
  - priority: MUST
  - constrains: validate_spec
  - acceptance: Given 3 of 10 requirements with all four production properties, score reports 30%.
  - verifiedBy: tests/test_score.py::test_the_population_is_every_item_not_only_requirements
- R2.4 `specl-validate badge` must produce a valid SVG file with color reflecting the maturity score.
  - priority: SHOULD
  - constrains: validate_spec
  - acceptance: Given a score of 40%, the badge SVG contains fill color matching the red threshold.
- R2.5 `specl-validate diff` must report added, removed, and modified requirements between two Turtle files.
  - priority: SHOULD
  - constrains: validate_spec
  - acceptance: Given old.ttl with R1.1 and new.ttl with R1.1 (changed) and R1.2 (added), diff reports 1 added and 1 modified.
  - verifiedBy: tests/test_migrate.py::test_diff_ignore_base_sees_a_rebased_graph_as_the_same_items

## R3 Namespaces
- R3.1 All generated Turtle must use `https://w3id.org/specl/ns#` as the vocabulary namespace and the specification's own declared `spec_base` as the instance namespace. The translator must never mint instance IRIs into a namespace the specification did not declare.
  - priority: MUST
  - constrains: spec_to_rdf, core_ttl
  - acceptance: Given any spec, translated output prefixes are specl: and spec: pointing to the w3id.org URIs.
  - verifiedBy: tests/test_spec_base.py::test_no_node_is_minted_under_the_retired_namespace

## R4 Explorer
- R4.1 The explorer must be a single self-contained HTML file under 30 KB.
  - priority: MUST
  - constrains: explorer
  - acceptance: explorer.html file size is under 30720 bytes and contains no external resource references.

## R5 LLM Assistant
- R5.1 `specl-assist gaps` must read SHACL warnings and draft remediation prompts via Ollama.
  - priority: SHOULD
  - constrains: spec_assistant
  - acceptance: Given a spec with warnings and a running Ollama instance, gaps prints a draft for each warning.
- R5.2 `specl-assist check` must flag contradictions and duplications across requirements.
  - priority: SHOULD
  - constrains: spec_assistant
  - acceptance: Given a spec with two requirements that contradict, check output includes a finding referencing both.

## R6 Packaging
- R6.1 The package must be installable via `pip install specl` and register three console scripts.
  - priority: MUST
  - constrains: pyproject
  - acceptance: After pip install, specl-translate, specl-validate, and specl-assist are on PATH and --help works.
- R6.2 shapes.ttl, core.ttl, and explorer.html must be included as package data.
  - priority: MUST
  - constrains: pyproject
  - acceptance: After pip install, importlib.resources.files('specl').joinpath('shapes.ttl') resolves.

# User Stories

- US1 As a spec author, I run specl-translate on my markdown, specl-validate to check it, and see a maturity score that climbs as I add annotations.
- US2 As a CI pipeline, I run specl-validate on every PR and fail the build if a production-status spec has violations or warnings.
- US3 As an AI agent, I read the translated spec.ttl to understand what a system should do before generating code.

# Open Questions and Gaps

- OQ1 Whether to add a scaffolding command that creates a new spec directory with a template spec.md. Its CLI surface is undecided and follows `docs/decisions/0001-cli-surface.md`; there is no umbrella `specl` command to hang it on.
  - recommendation: Add in 0.4.0
  - status: open
- OQ2 Whether specl-validate should default to the bundled shapes.ttl via importlib.resources when no shapes path is given.
  - recommendation: Implemented. It was the first command an adopter runs and it failed, because nothing tells someone who pip installed the package where the bundled file lives
  - resolutionStatus: resolved
- OQ3 Whether to support a `namespace_style: hash | slash` front-matter key for specs that want per-element slash URIs (Schema.org pattern).
  - recommendation: Defer to 0.4.0
  - status: open
