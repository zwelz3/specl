# Releasing

Two kinds of release, and 1.0 is different from every one before it.

## Any 0.x or 1.x release

Tagged in this repository, never published. See
`docs/decisions/0007-internal-releases-until-1.0.md`.

1. `pytest -q` and `python3 tools/check_docs.py` from a clean clone, on Linux
   and Windows. CI covers both; run them locally if the tag is not going through
   CI first.
2. Bump `pyproject.toml`, `src/specl/__init__.py`, `core.ttl` and `shapes.ttl`
   `owl:versionInfo`. The doc checker fails if they disagree with the newest
   changelog heading, so it will tell you if you miss one.
3. Date the changelog heading.

**Write changelog entries when you tag, not before.** The 0.3.0 section was written as a plan and read afterwards as a record, so four of its entries describe things that never shipped or were later reversed. One of them was the accepted half of a downstream request, cited as done in the disposition that declined the alternative, and it sat unshipped for eight releases because the changelog said otherwise and nothing checked. An unreleased section is a plan; label it as one or leave it empty.
4. `git tag -a vX.Y.Z`, push the tag.

Do not create a GitHub *release* before 1.0. The publish workflow fires on one
and refuses any 0.x version, so it will fail loudly rather than publish, but the
failure is noise.

## 1.0.0

The first published release, the moment the contract stops being yours alone to
change, and the day the 2.0 collection window opens. The ordering below is not
arbitrary: several steps are irreversible and two depend on content existing
before something points at it.

### Before tagging

1. **Confirm both open criteria are met.** `docs/ROADMAP.md` carries the table.
   As of writing, criterion 3 is the only one outstanding.

2. **Publish the Pages content first.** The versioned vocabulary and shapes
   copies the build writes under `_site`, and `docs/contracts/2.md`, must be
   live *before* the redirects pointing at them merge. A redirect merged ahead of its target is a live 404 on an identifier
   already emitted into every graph.

3. **File the w3id pull request.** `tools/w3id/README.md` has the measured
   delta, the procedure, and the verification loop. Their maintainers review
   redirect changes, so allow days rather than minutes. Nine rules are new and
   one target changes; nothing upstream is removed, so no identifier already in
   the wild stops resolving.

4. **Verify every redirect** with the loop in that README, including both
   Accept-header variants for `ns`. This closes criterion 3.

5. **Set the window dates** in `docs/proposals/OPEN.md`: the day you tag and the
   same date one year on. `GOVERNANCE.md` is meaningless until that date exists,
   because every proposal locks to it.

### Tagging

6. Bump all four version strings to `1.0.0`, date the changelog heading, run the
   suite and the doc checker one more time from a clean clone.

7. `git tag -a v1.0.0` and push.

8. **Create the GitHub release.** This is the irreversible step: it triggers
   `publish.yml`, which builds and pushes to PyPI. The guard permits any version
   at or above 1.0, so nothing will stop a mistake here. Check the version in
   `pyproject.toml` before clicking.

### After tagging

9. **Notify the downstream consumer.** The embargo in
   `specs/commitments/spec.md` lifts when 0.3.0 is tagged and the redirects are
   live, whichever is later. Both are now true. The amendment says they are
   notified rather than left to infer it, so this is a message you send, not a
   file you edit.

10. **Update the README install section.** It currently says PyPI carries 0.2.0
    and tells people to install from git. That stops being true the moment step
    8 finishes.

11. **Open the adopter registry.** Nothing else is required, but the governance
    mechanism depends on registered adopters existing, and nobody registers
    against a project that has not asked.

## After 1.0

Additive changes ship in 1.x whenever they are ready. Substantive ones collect
against the window closing date and release together as 2.0. `GOVERNANCE.md` is
the process; this file is only the mechanics.
