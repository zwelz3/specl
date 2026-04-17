---
spec_id: htmlpres-001
title: Interactive HTML Presentation Tool
version: 0.1.0
status: prototype
---

# Intent
Capture the design of a zero-dependency, single-file HTML presentation tool suitable for technical talks with live code, diagrams, and interactive widgets.

# Purpose
Give presenters a durable, version-controllable alternative to slide decks that renders in any browser, works offline, and supports embedded interactivity without a build step.

# Requirements

- R1.1 Output must be a single self-contained HTML file with no external runtime dependencies.
- R1.2 Slides are authored in markdown with YAML frontmatter per slide for transitions and speaker notes.
- R1.3 The tool must support keyboard navigation (arrow keys, space, home/end) and a presenter mode with notes on a second display.
- R1.4 Embedded code blocks must be executable for JavaScript and renderable with syntax highlighting for all common languages.
- R1.5 Mermaid diagrams and inline SVG must render natively.
- R1.6 Export to PDF must be supported via the browser print pathway with correct page breaks.
- R2.1 The tool should load a deck in under 500ms on a cold browser cache for decks up to 100 slides.

# User Stories

- US1 Present a conference talk from a USB drive on an unknown machine with no network.
- US2 Share a deck as a single .html attachment that recipients can open directly.
- US3 Maintain a deck in git alongside the code it describes, with meaningful diffs.

# Open Questions and Gaps (flag for follow-up)

- Theming strategy (CSS variables vs inline) is unspecified.
- Audio and video embedding approach is undecided.
- Speaker notes window coordination protocol needs selection (BroadcastChannel vs localStorage events).
