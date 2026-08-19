# Downstream commitments

This register is a specl specification. It lives at `specs/commitments/spec.md`
and is translated, validated, and scored in CI alongside the other two.

Each commitment carries the consumer's own request identifier, `UR1` through `UR17`, plus `UR18` onward for commitments this register makes that no request asked for, whether raised by a downstream report or by specl itself. A conversation about `UR11` resolves to one IRI on both sides:
`https://w3id.org/specl/commitments/spec#UR11`.

The move is recorded in `docs/decisions/0008-commitments-as-a-specification.md`.
Three releases in a row under-delivered against clauses written here, each time
because the roadmap summarized what this document committed and the summary was
believed. A commitment with an identifier, a status, and a verification claim
checked against the test suite is harder to summarize away.

`docs/proposals/0002-downstream-request-disposition.md` remains the record of how
each request was decided, and
`docs/proposals/0002a-downstream-requests-as-received.md` the requests as they
arrived. This file is a pointer.
