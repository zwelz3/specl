---
spec_id: xlsvc-001
title: Excel Report Generation Service
version: 0.1.0
status: prototype
---

# Intent
Define a lightweight HTTP service that generates multi-sheet Excel workbooks from structured data with repeatable formatting, formulas, and charts for recurring reporting workflows.

# Purpose
Eliminate hand-built Excel reports by exposing a single service endpoint that turns query results plus a report definition into a formatted .xlsx file, delivered synchronously for small reports and via job queue for large ones.

# Requirements

- R1.1 The service must expose an HTTP POST endpoint that accepts a report definition (JSON) and returns a .xlsx file or a job ID.
- R1.2 Report definitions must support multiple named sheets, each bound to a data source (inline JSON, SQL query, or uploaded CSV).
- R1.3 Cell formatting (number formats, conditional formatting, borders, fonts, fills) must be declarable per column or per range.
- R1.4 Formulas must be supported, including cross-sheet references and Excel-native functions.
- R1.5 Charts must be generated from sheet data using openpyxl or xlsxwriter chart primitives.
- R1.6 Large reports (over 100k rows or over 30 seconds of generation time) must be handled via an async job queue with status polling.
- R1.7 The service must authenticate callers via OAuth 2.0 bearer tokens.
- R2.1 Output files must open without errors in Excel 2016 and later and in LibreOffice Calc.
- R2.2 The service must emit structured logs and OpenTelemetry traces for every request.

# User Stories

- US1 Generate a monthly financial report from a SQL query with three summary sheets and a pivot-style chart.
- US2 Produce a per-customer workbook in under two seconds for customer portal downloads.
- US3 Submit a large historical export as an async job and retrieve the file when ready.

# Open Questions and Gaps (flag for follow-up)

- Choice of generation library (openpyxl vs xlsxwriter vs both) is undecided.
- Pivot table support is not specified.
- Template-based generation (use an existing .xlsx as a skeleton) is not yet scoped.
- Data source connector list for v1 is not finalized.
