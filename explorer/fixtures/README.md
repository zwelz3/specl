# Stage 0 fixtures

Each file exercises one condition the explorer must handle. Files whose first
line says HAND-AUTHORED are not translator output and must not be regenerated;
the condition they test is one the translator cannot produce.

| Fixture | Requirement | Source |
| --- | --- | --- |
| repeated-predicates | R2.6 | Generated |
| detail-list | R2.7 | Generated |
| local-name-collision | R2.8 | Hand-authored |
| unrecognised-class | R2.9 | Hand-authored |
| malformed-statement | R2.4 | Hand-authored |
| future-contract | R2.10 | Hand-authored |
| unresolvable-reference | R6.6 | Generated |
| alt-labels | R4.5 | Generated |
| no-title | R4.2 | Hand-authored |
| zero-requirements | R5.5 | Generated |
| no-items | R9.3 | Generated |
| no-specification | R9.2 | Hand-authored |
| five-hundred-items | R10.1 | Generated |

Regenerate the generated set with `python3 make_fixtures.py` from a checkout
with specl installed. The harness (`../test/run.mjs`) needs nothing but Node.
