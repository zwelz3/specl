# w3id redirect rules

`specl.htaccess` in this directory is the intended state of `specl/.htaccess` in
[perma-id/w3id.org](https://github.com/perma-id/w3id.org). The copy here is the
source of truth. Upstream is a mirror of it, updated by pull request.

## Why the file lives here

The registration covers the whole `/specl/` path, so every specl IRI that
resolves does so through rules this project owns but does not host. That makes
the rules a sixth artifact making claims about this repository, kept in a place
where nobody working here would see them drift. Vendoring puts them under the
same review and the same checks as everything else.

## What keeps it honest

The contract 1 copies of the vocabulary and shapes live in `published/` as
frozen files. Graphs in the wild pin `https://w3id.org/specl/ns/1`, so it has to
keep resolving to the same bytes, and reconstructing them from a git tag during
the build required the tag to exist and the checkout to have fetched it.

`tools/check_docs.py` verifies every redirect target that points back at this
project. A `blob/main/<path>` target must exist in the tree. A
`zwelz3.github.io/specl/<asset>` target must be something
`.github/workflows/pages.yml` actually builds. That second rule exists because a
JSON-LD content-negotiation rule pointed at `ns.jsonld` for a long time while the
build never produced it, so any client asking for JSON-LD got a 404.

The check runs in CI and is covered by `tests/test_check_docs.py`.

## How to apply an update

The upstream file is `specl/.htaccess` in
[perma-id/w3id.org](https://github.com/perma-id/w3id.org). It is replaced whole
rather than patched, so the two never diverge by accumulating edits made in one
place and not the other.

1. Edit `specl.htaccess` here, in the same commit as whatever motivated it.
2. `python3 tools/check_docs.py`. A target that does not exist in the tree, or a
   site asset the Pages workflow does not build, fails the check.
3. Confirm the Pages site already serves every `zwelz3.github.io` target. A
   redirect merged ahead of the content it points at is a live 404.
4. Fork perma-id/w3id.org, replace `specl/.htaccess` with this file verbatim,
   and open a pull request. Their maintainers review redirect changes; expect
   turnaround in days rather than minutes.
5. After it merges, verify each rule, including the content-negotiated variants:

   ```bash
   for p in ns shapes ns/1 ns/2 shapes/1 shapes/2 spec tool/spec \
            explorer/spec commitments/spec contract/1 contract/2 explorer; do
     printf '%-18s %s\n' "$p" "$(curl -s -o /dev/null -w '%{http_code} -> %{redirect_url}' \
       "https://w3id.org/specl/$p")"
   done
   curl -sI -H 'Accept: text/turtle' https://w3id.org/specl/ns | grep -i location
   curl -sI -H 'Accept: application/ld+json' https://w3id.org/specl/ns | grep -i location
   ```

   Every one should be a 303 to the target in this file, and neither
   Accept-header variant should land on the HTML page.

## What is pending

Measured against the live upstream file rather than remembered. Nine rules are
new and one target changes.

| Rule | Change | Why |
| --- | --- | --- |
| `^tool/spec` | new | specl_tool's instance base, emitted into every graph it produces |
| `^explorer/spec` | new | specl_explorer's instance base |
| `^commitments/spec` | new | the commitments register's base, cited by a second party as `UR11` and the like |
| `^contract/1` | new | contract 1 is named by `dct:conformsTo` in every pre-0.11 graph |
| `^contract/2` | new | contract 2 is named in every graph from 0.11 onward |
| `^ns/1`, `^ns/2` | new | versioned vocabulary, committed under UR17 |
| `^shapes/1`, `^shapes/2` | new | versioned shapes, committed under UR17 |
| `^spec` | target changes | the base is retired and not reassigned; it now explains itself via `NAMESPACE-MIGRATION.md` rather than pointing at the specs directory |

Nothing upstream is removed, so no identifier already in the wild stops
resolving.

Until this merges, the IRIs above are valid identifiers that do not dereference.
That is cosmetic rather than a correctness problem: validation never fetches and
nothing in this project resolves an IRI at runtime. It stops being cosmetic when
a second party publishes documents citing those IRIs, which is why the downstream
embargo in `specs/commitments/spec.md` lifts on this merging rather than on a
tag.

## What is not covered yet

Content negotiation for the versioned locations. `^ns/1` and the others serve
Turtle only, while `^ns` negotiates HTML, Turtle, and JSON-LD. Adding variants is
a later edit to the same file and breaks nothing.
