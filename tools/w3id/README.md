# w3id redirect rules

`specl.htaccess` and `upstream-README.md` in this directory are copies of the `.htaccess` and `README.md` in the `specl` directory of [perma-id/w3id.org](https://github.com/perma-id/w3id.org). They are kept byte-identical to what is live there, and changes go upstream by pull request.

Both files are theirs in form. The `.htaccess` header follows the house style their examples use, and their process requires a `README.md` alongside it listing the maintainer's GitHub account. An earlier version of this directory held only the rules, in a house style of its own, which meant the file described as the source of truth diverged from the file actually serving traffic the moment a pull request was reviewed.

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

1. Edit `specl.htaccess` and, if the URI table changes, `upstream-README.md`, in the same commit as whatever motivated it.
2. `python3 tools/check_docs.py`. A target that does not exist in the tree, or a
   site asset the Pages workflow does not build, fails the check.
3. Confirm the Pages site already serves every `zwelz3.github.io` target. A redirect merged ahead of the content it points at is a live 404 on an identifier that may already be in emitted graphs.
4. Fork perma-id/w3id.org and replace their `specl` directory's `.htaccess` and `README.md` with these two files verbatim. **Their files use LF endings**; a Windows clone with `core.autocrlf=true` will produce a diff touching every line, which is a diff a volunteer maintainer closes unread. Set `core.autocrlf=false` in that clone and verify with `git diff --stat` before opening the pull request.
5. Open the pull request. Fill in their template rather than leaving it blank, squash to one commit, and use a message naming the project rather than "Update .htaccess". Their maintainers review redirect changes; expect turnaround in days.
6. After it merges, verify each rule, including the content-negotiated variants:

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

Nothing. The nine rules below and the one changed target merged upstream; the copies here match what is live.

Recompute this section rather than trusting it whenever something changes, by diffing against `https://raw.githubusercontent.com/perma-id/w3id.org/master/specl/.htaccess`. The table went stale once already.

## What merged

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

These now resolve, which closes 1.0 criterion 3 and satisfies the second half of the downstream embargo condition in `specs/commitments/spec.md`.

## What is not covered yet

Content negotiation for the versioned locations. `^ns/1` and the others serve
Turtle only, while `^ns` negotiates HTML, Turtle, and JSON-LD. Adding variants is
a later edit to the same file and breaks nothing.
