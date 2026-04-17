---
spec_id: explorer-001
title: specl Spec Explorer
version: 0.1.0
status: prototype
---

# Intent
Define a single-file, zero-dependency HTML tool that lets a reader load a specl-generated `spec.ttl` file and understand its content, structure, raw Turtle representation, and production maturity in one view without any build step, server, or network access.

# Purpose
Replace the current drag-and-drop viewer (which only lists subject IDs and short descriptions) with an actual reading tool. A spec author, reviewer, or downstream AI agent should be able to open the explorer, drop a `spec.ttl`, and immediately see the spec's metadata, every requirement and user story with full detail, where gaps exist, and how close the spec is to production-ready — with the raw Turtle one tab away for verification.

# Requirements

## R1 Packaging and Runtime
- R1.1 The explorer must be a single self-contained `.html` file with no external runtime dependencies (no CDN scripts, no fonts, no network calls).
- R1.2 It must open and function correctly from the local filesystem (`file://`) in modern Chromium, Firefox, and Safari.
- R1.3 It must ship as `src/specl/explorer.html` inside the specl Python package and be included as package data in `pyproject.toml`.
- R1.4 Total file size should stay under 30 KB uncompressed.
- R1.5 No build step. Vanilla HTML, CSS, and JavaScript only.

## R2 Input and Parsing
- R2.1 The explorer must accept a `spec.ttl` file via a file input control and via drag-and-drop onto the window.
- R2.2 It must include a minimal Turtle parser sufficient for the specl output format (subject + indented predicates, `@prefix` declarations, `"..."` and `"""..."""` string literals, IRIs with `spec:` and `ekga:` prefixes).
- R2.3 The parser must extract all `ekga:Specification`, `ekga:Requirement`, `ekga:UserStory`, `ekga:OpenIssue`, `ekga:DecisionRecord`, `ekga:DesignNote`, and `ekga:Comment` individuals with their full property sets.
- R2.4 Parse failures on individual statements must not crash the tool; log to console and skip the malformed statement.
- R2.5 The raw file text must be retained in memory so the Raw Turtle tab can display it exactly as loaded.

## R3 Layout
- R3.1 A fixed header shows spec title, version, status badge, and a maturity progress bar.
- R3.2 A left sidebar (approximately 320 px wide) contains the file input, a live text filter, and the grouped item list.
- R3.3 A main panel to the right of the sidebar contains tabbed content (Detail, Raw Turtle, Summary).
- R3.4 The layout must use CSS Grid or Flexbox so the sidebar and main panel scroll independently.
- R3.5 A dark theme is the default. Color tokens must be declared as CSS custom properties at `:root` so a future light theme can be added without rewriting the stylesheet.

## R4 Sidebar Behavior
- R4.1 Items are grouped by type, with group headers showing the type label and count (e.g., "Requirements (8)").
- R4.2 Each item row shows its short ID (e.g., `R1.2`, `US3`) and a truncated preview of its description.
- R4.3 Each type has a distinct color dot indicator. Colors must be defined as CSS variables so they can be themed.
- R4.4 Items must sort naturally within their group, so `R1.10` follows `R1.9`, not `R1.1`.
- R4.5 The filter input must match against item ID and description, case-insensitive, updating the list on every keystroke.
- R4.6 Clicking a sidebar item selects it, highlights the row, and updates the main panel. The selection must persist across tab changes.

## R5 Header and Maturity
- R5.1 The header must display the spec's `dct:title`, `dct:hasVersion`, and `ekga:status` properties.
- R5.2 A maturity score must be computed client-side as the percentage of `ekga:Requirement` individuals that carry all four production properties: `ekga:priority`, `ekga:acceptanceCriterion`, `ekga:verifiedBy`, and `ekga:constrains`.
- R5.3 The score must render as both a numeric percentage and a horizontal progress bar.
- R5.4 The bar color must shift: red below 50%, amber from 50% to 84%, green at 85% and above. Thresholds must be declared as constants at the top of the script for easy tuning.
- R5.5 If the loaded spec has zero requirements, the maturity score displays as "—" and the bar is empty, not zero.

## R6 Detail Tab
- R6.1 When an item is selected, the Detail tab shows its ID as a heading, its type as a subtitle, and all known properties as a definition list.
- R6.2 Type-specific fields must render in a sensible order:
    - Requirement: description, priority, acceptance criterion, verified by, constrains
    - UserStory: description, as a, I want, so that, acceptance criterion
    - OpenIssue: description, recommendation, owner, resolution status
    - DecisionRecord: description, status, rationale, affects
- R6.3 Properties that exist in the expected set but are absent in the data must render as an italic "not set" placeholder in a muted warning color, so gaps are visually obvious.
- R6.4 For requirements specifically, the tab must show a "production-ready" chip in green when all four production properties are present, or a "needs work" chip in amber otherwise.
- R6.5 Long text values must wrap cleanly and remain selectable for copy.

## R7 Raw Turtle Tab
- R7.1 When an item is selected, the tab shows that item's Turtle statement block, extracted from the raw text by locating the subject IRI and taking characters through the next statement terminator (`\n.` or ` .\n`).
- R7.2 When no item is selected, the tab shows the full raw file.
- R7.3 The displayed Turtle must be syntax-highlighted: distinct colors for prefixes, IRIs, predicates, string literals, and comments.
- R7.4 Highlighting must be implemented with a small inline function (regex-based is acceptable); no external highlighter library.
- R7.5 The Turtle block must render in a monospace font and allow horizontal scrolling for long lines.

## R8 Summary Tab
- R8.1 Shows total item count, requirement count, and production-ready ratio (e.g., "3/8 production-ready") as chips.
- R8.2 Shows the spec's `ekga:intent` and `ekga:purpose` prose in full.
- R8.3 Shows a per-type breakdown (how many requirements, stories, open issues, etc.).
- R8.4 Must render regardless of whether a sidebar item is selected.

## R9 Empty and Error States
- R9.1 Before any file is loaded, the main panel shows a centered "Drop a spec.ttl file to begin" message.
- R9.2 If the dropped file fails to parse (no Specification individual found), show an error message explaining the expected format and linking to the specl README convention.
- R9.3 If the file is empty or contains no recognized items, show "No items found in this file."

## R10 Non-Functional
- R10.1 First paint after file drop must complete in under 200 ms for specs up to 500 items on mid-tier hardware.
- R10.2 No data leaves the browser. No telemetry, no network requests, no external resource loads.
- R10.3 The tool must be keyboard accessible: tab to the file input, filter, and sidebar items; arrow keys to navigate the item list.
- R10.4 Must function offline. Opening the HTML file from a USB drive on an air-gapped machine is a supported use case.

# User Stories

- US1 As a spec author, I open the explorer, drop my spec.ttl, and immediately see which requirements are missing acceptance criteria so I know where to focus.
- US2 As a reviewer, I filter the sidebar by a keyword to find all requirements touching authentication, click through each one, and read their full detail without opening the markdown file.
- US3 As an AI agent integrator, I open the explorer to verify that the Turtle generated by `spec_to_rdf.py` matches what I expect before feeding it to a downstream tool.
- US4 As a program manager, I glance at the maturity bar to gauge how close the spec is to production-ready without asking the author.
- US5 As an auditor with no development tools installed, I open the explorer from a USB drive on a locked-down workstation and read the spec.

# Design Considerations

- The Turtle parser does not need to be RFC-compliant. It only needs to handle the output of `specl.spec_to_rdf`, which is deterministic and well-formed. A 30-line parser is sufficient.
- Prefer declarative CSS over runtime style manipulation. Use CSS classes and variables; avoid setting styles via JavaScript except for the maturity bar width and color.
- Keep the JavaScript in a single `<script>` block at the bottom of the file. No modules, no imports, no bundler.
- Treat the explorer as read-only. Editing, saving, or uploading is explicitly out of scope for v1.
- The existing broken `explorer.html` placeholder in the package should be replaced wholesale, not patched.

# Open Questions and Gaps

- Whether to support loading the companion `spec.md` alongside the `.ttl` for side-by-side reading. Recommendation: defer to v2.
- Whether to render Mermaid diagrams embedded in description strings. Recommendation: defer; out of scope for a read-only viewer.
- Whether to show SHACL validation results inline by also loading a `shapes.ttl`. Recommendation: defer to v2 as a separate "Validation" tab.
- Light theme toggle. Recommendation: defer, but ensure CSS variables are structured to support it.
- Export of the current view (selected item as PDF or HTML snippet). Recommendation: defer; browser print is sufficient for v1.
