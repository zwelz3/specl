---
spec_id: pptxgen-001
title: Corporate PowerPoint Template Filler
version: 0.1.0
status: prototype
---

# Intent
Specify a tool that populates an approved corporate PowerPoint template from structured inputs, preserving brand compliance and eliminating manual slide assembly for routine deliverables.

# Purpose
Produce branded .pptx decks from markdown or JSON content without letting authors drift from the approved master layout, color palette, or typography.

# Requirements

- R1.1 The tool must accept a corporate .pptx template as input and preserve all master slide layouts, theme colors, fonts, and placeholders exactly.
- R1.2 Content must be supplied as markdown or JSON with a declared mapping from content sections to named slide layouts in the template.
- R1.3 Text placeholders must be filled without altering run-level formatting (font family, size, color) inherited from the layout.
- R1.4 Images must fit placeholder bounds with configurable crop or letterbox behavior, never stretched.
- R1.5 Tables must be inserted using the template's native table style, not as images.
- R1.6 Speaker notes from the source content must populate the notes pane of each slide.
- R1.7 The tool must emit a validation report listing any content that could not be placed (missing layout, overflowing text, unsupported element).
- R2.1 python-pptx is the preferred implementation library.

# User Stories

- US1 Generate a weekly status deck from a markdown file that matches the corporate template pixel-for-pixel.
- US2 Bulk-produce customer-specific decks from a CSV of account data and a single content template.
- US3 Reject content that would break brand compliance before producing the file.

# Open Questions and Gaps (flag for follow-up)

- Chart generation strategy (native pptx charts vs embedded images) is undecided.
- Multi-language template support is unspecified.
- Versioning policy for template updates is not defined.
