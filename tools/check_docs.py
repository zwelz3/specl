#!/usr/bin/env python3
"""Check that documentation agrees with the code it describes.

Every defect found in the 0.3.0 review round shared one shape: an artifact
asserting something another artifact did not do. The ontology declared object
properties the translator emitted as literals. The shapes required a property the
translator could not produce. The changelog described a release that was not
published. Documentation referenced a Makefile that does not exist and a console
script nobody had decided to add.

None of those is a hard bug. Each is a disagreement between two artifacts that
nothing checked. This checks the documentation side of that class.

Four checks:

1. Referenced repository paths exist.
2. Referenced ``specl-*`` commands are declared in ``[project.scripts]``.
3. Referenced ``specl-validate <sub>`` subcommands are registered in
   ``validate_spec.py``.
4. No document invokes a bare ``specl`` umbrella command, which does not exist.
5. Every redirect target in the vendored w3id rules resolves to something this
   repository actually contains or builds.
6. The package version, the vocabulary's ``owl:versionInfo``, and the newest
   changelog entry agree.
7. The graph contract number agrees across the translator, the vocabulary's
   ``owl:versionIRI``, and the shapes' ``owl:versionIRI``.

Anything a document may legitimately reference before it exists is declared in
``tools/documented-gaps.toml`` with the record that authorizes it. There is no
proximity heuristic and no per-document suppression list for repository content:
an exception is a registry entry naming a record, or it is a failure.

Exit 1 on any failure. Run from the repository root.
"""
from __future__ import annotations

import re
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Verbatim archives of documents received from elsewhere. Their references
# describe the sender's view at the time and must not be rewritten to match
# this repository.
EXCLUDE = {
    # Verbatim archive of a document received from a downstream consumer. Its
    # references describe the sender's repository and must not be rewritten.
    "docs/proposals/0002a-downstream-requests-as-received.md",
    # Verbatim archive of the g3-toolkit request. Its references describe that
    # project's repository and must not be rewritten to match this one.
    "docs/proposals/0003a-g3t-component-identity-as-received.md",
}

# Documents that legitimately reference another repository's paths. Command
# checks still apply; path checks do not.
FOREIGN_PATHS = {
    "docs/proposals/0002-downstream-request-disposition.md",
}

# Only tokens that look like repository paths. A bare filename in prose
# ("the shapes.ttl file") is not a path reference and is not checked.
PATH_RE = re.compile(r"`([A-Za-z0-9_.-]+(?:/[A-Za-z0-9_.-]+)+\.(?:md|py|ttl|toml|yml|yaml|html|svg))`")
LINK_RE = re.compile(r"\[[^\]]*\]\(([^)#][^)]*)\)")
# The trailing boundary matters. Without it, `specl-tool-001` in prose matches
# as a reference to a command named specl-tool-, which is the third false
# result this checker has produced from an unanchored pattern.
CMD_RE = re.compile(r"`(specl-[a-z-]+)(?=[`\s]|$)")
SUB_RE = re.compile(r"`specl-validate ([a-z-]+)")

# The defect this checker was written for. `specl migrate-iris` reached three
# documents by implying an umbrella command that has never existed. The
# hyphenated names all match CMD_RE; a bare `specl <verb>` matches nothing else
# here, so it needs its own rule. `docs/decisions/0001-cli-surface.md` leaves
# the bare command unclaimed, which is what makes this checkable.
UMBRELLA_RE = re.compile(r"`specl\s+([a-z][a-z-]*)")
# Words that follow `specl` in prose without invoking a command.
UMBRELLA_ALLOW = {"is", "does", "has", "will", "and", "or", "as", "for"}


def gaps() -> dict:
    path = ROOT / "tools" / "documented-gaps.toml"
    if not path.exists():
        return {}
    with path.open("rb") as fh:
        return tomllib.load(fh)


def declared_scripts() -> set[str]:
    with (ROOT / "pyproject.toml").open("rb") as fh:
        return set(tomllib.load(fh).get("project", {}).get("scripts", {}))


def registered_subcommands() -> set[str]:
    """Subcommands `specl-validate` actually registers.

    Extracted by pattern rather than by import, because this check runs without
    the package installed. An empty result means the extraction broke, not that
    the binary has no subcommands, and the caller fails on it. A checker that
    silently stops checking is the failure mode this tool exists to prevent.
    """
    source = (ROOT / "src" / "specl" / "validate_spec.py").read_text(encoding="utf-8")
    return set(re.findall(r'add_parser\(\s*"([a-z-]+)"', source))


BLOB_RE = re.compile(r"https://github\.com/zwelz3/specl/blob/main/([^\s\]]+)")
# Slashes included. The versioned locations are ns/1.ttl and shapes/1.ttl, and
# a pattern that stopped at the first slash matched neither, so both new rules
# were silently unchecked on the run that added them.
SITE_RE = re.compile(r"https://zwelz3\.github\.io/specl/([A-Za-z0-9_./-]+)")


def check_w3id_targets() -> list[str]:
    """Every redirect target that points into this repository must exist.

    The vendored rules are the source of truth for a pull request against
    another repository, so a dead target here becomes a live 404 that nobody
    here would notice. Site targets are checked against what the Pages workflow
    builds rather than against the tree, since the site is assembled.
    """
    path = ROOT / "tools" / "w3id" / "specl.htaccess"
    if not path.exists():
        return ["tools/w3id/specl.htaccess: missing; the redirect source is the PR"]
    text = path.read_text(encoding="utf-8")
    pages = (ROOT / ".github" / "workflows" / "pages.yml").read_text(encoding="utf-8")
    failures = []
    for target in sorted(set(BLOB_RE.findall(text))):
        if not (ROOT / target).exists():
            failures.append(
                f"tools/w3id/specl.htaccess: redirects to {target!r}, which is not in the tree"
            )
    for asset in sorted(set(SITE_RE.findall(text))):
        # Badges are written by a loop over specs/, so the build guarantees one
        # per specification and nothing else. Exempting the whole directory
        # would let a badge URL for a specification that does not exist pass.
        if asset.startswith("badges/") and "_site/badges" in pages:
            name = asset[len("badges/"):].removesuffix(".svg")
            if (ROOT / "specs" / name / "spec.md").exists():
                continue
            failures.append(
                f"tools/w3id/specl.htaccess: badge {asset!r} names no "
                "specification under specs/"
            )
            continue
        if f"_site/{asset}" not in pages:
            failures.append(
                f"tools/w3id/specl.htaccess: redirects to site asset {asset!r}, "
                "which the Pages workflow does not build"
            )
    return failures


VERSION_RE = re.compile(r'^version\s*=\s*"([^"]+)"', re.M)
VERSION_INFO_RE = re.compile(r'owl:versionInfo\s+"([^"]+)"')
CHANGELOG_RE = re.compile(r"^## (\d+\.\d+\.\d+)", re.M)


def check_versions() -> list[str]:
    """The package, the vocabulary, and the changelog agree.

    Four version strings drifted apart before anyone counted them: pyproject
    said 0.2.0, core.ttl said 0.1.0, and the changelog was preparing 0.3.0.
    Nothing compared them, which is the same shape as every other defect this
    checker exists for.
    """
    failures = []
    package = VERSION_RE.search((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    vocabulary = VERSION_INFO_RE.search((ROOT / "src" / "specl" / "core.ttl").read_text(encoding="utf-8"))
    changelog = CHANGELOG_RE.search((ROOT / "CHANGELOG.md").read_text(encoding="utf-8"))
    if not (package and vocabulary and changelog):
        return ["could not read one of the version strings; the patterns are stale"]
    dunder = re.search(r"__version__\s*=\s*['\"]([^'\"]+)", (ROOT / "src" / "specl" / "__init__.py").read_text(encoding="utf-8"))
    found = {
        "pyproject.toml": package.group(1),
        "src/specl/__init__.py __version__": dunder.group(1) if dunder else "unreadable",
        "src/specl/core.ttl owl:versionInfo": vocabulary.group(1),
        "CHANGELOG.md newest entry": changelog.group(1),
    }
    if len(set(found.values())) > 1:
        listed = ", ".join(f"{k} = {v}" for k, v in found.items())
        failures.append(f"version strings disagree: {listed}")
    return failures


CONTRACT_RE = re.compile(r'CONTRACT\s*=\s*"https://w3id\.org/specl/contract/(\d+)"')
VERSION_IRI_RE = re.compile(r"owl:versionIRI\s+<https://w3id\.org/specl/\w+/(\d+)>")


def check_contract_version() -> list[str]:
    """The contract number is asserted in three places and must agree.

    The translator emits it into every graph as dct:conformsTo. The vocabulary
    and the shapes each carry it as owl:versionIRI, which is what a consumer
    pins. Three artifacts asserting one number is the shape that has drifted
    here before.
    """
    sources = {
        "src/specl/spec_to_rdf.py CONTRACT": CONTRACT_RE,
        "src/specl/core.ttl owl:versionIRI": VERSION_IRI_RE,
        "src/specl/shapes.ttl owl:versionIRI": VERSION_IRI_RE,
    }
    paths = {
        "src/specl/spec_to_rdf.py CONTRACT": "src/specl/spec_to_rdf.py",
        "src/specl/core.ttl owl:versionIRI": "src/specl/core.ttl",
        "src/specl/shapes.ttl owl:versionIRI": "src/specl/shapes.ttl",
    }
    found = {}
    for label, pattern in sources.items():
        match = pattern.search((ROOT / paths[label]).read_text(encoding="utf-8"))
        if not match:
            return [f"{label}: not found; the pattern is stale and the check is not running"]
        found[label] = match.group(1)
    if len(set(found.values())) > 1:
        listed = ", ".join(f"{k} = {v}" for k, v in found.items())
        return [f"graph contract version disagrees: {listed}"]
    return []


def check_registry(*tables: dict) -> list[str]:
    """Every declared gap names a record, and that record exists."""
    failures = []
    for table in tables:
        for name, meta in table.items():
            record = meta.get("record")
            if not record:
                failures.append(
                    f"tools/documented-gaps.toml: {name!r} names no record"
                )
            elif not (ROOT / record).exists():
                failures.append(
                    f"tools/documented-gaps.toml: {name!r} cites missing record {record!r}"
                )
    return failures


def main() -> int:
    scripts = declared_scripts()
    subs = registered_subcommands()
    data = gaps()
    planned_scripts = data.get("scripts", {})
    planned_subs = data.get("validate_subcommands", {})
    allowed_paths = data.get("paths", {})
    umbrella = data.get("umbrella_mentions", {})

    failures: list[str] = check_registry(
        planned_scripts, planned_subs, allowed_paths, umbrella
    )
    failures += check_w3id_targets()
    failures += check_versions()
    failures += check_contract_version()
    if not subs:
        failures.append(
            "tools/check_docs.py: found no subcommands in validate_spec.py; "
            "the extraction pattern is stale and the subcommand check is not running"
        )

    # README badge URLs are site assets too, and the same rule applies: a
    # published URL the build does not produce is a broken image.
    for doc in sorted(ROOT.rglob("*.md")):
        rel = doc.relative_to(ROOT).as_posix()
        if ".git" in doc.parts or rel in EXCLUDE:
            continue
        text = doc.read_text(encoding="utf-8")

        paths = set(LINK_RE.findall(text))
        if rel not in FOREIGN_PATHS:
            paths |= set(PATH_RE.findall(text))
        for match in paths:
            if match.startswith(("http://", "https://")):
                continue
            if match in allowed_paths:
                continue
            candidate = (doc.parent / match).resolve()
            if not candidate.exists() and not (ROOT / match).exists():
                failures.append(f"{rel}: references missing path {match!r}")

        for asset in sorted(set(SITE_RE.findall(text))):
            if not asset.startswith("badges/"):
                continue
            name = asset[len("badges/"):].removesuffix(".svg")
            if not (ROOT / "specs" / name / "spec.md").exists():
                failures.append(
                    f"{rel}: badge {asset!r} names no specification under specs/"
                )

        for cmd in set(CMD_RE.findall(text)):
            if cmd not in scripts and cmd not in planned_scripts:
                failures.append(
                    f"{rel}: references command {cmd!r}, "
                    f"not in [project.scripts] and not in tools/documented-gaps.toml"
                )

        for sub in set(SUB_RE.findall(text)):
            if sub not in subs and sub not in planned_subs:
                failures.append(
                    f"{rel}: references subcommand 'specl-validate {sub}', "
                    f"not registered and not in tools/documented-gaps.toml"
                )

        allowed_verbs = set(umbrella.get(rel, {}).get("verbs", []))
        for verb in set(UMBRELLA_RE.findall(text)):
            if verb in UMBRELLA_ALLOW or verb in allowed_verbs:
                continue
            failures.append(
                f"{rel}: references 'specl {verb}', but there is no umbrella "
                f"'specl' command; see docs/decisions/0001-cli-surface.md"
            )

    if failures:
        print(f"doc consistency: {len(failures)} problem(s)\n")
        for line in failures:
            print(f"  {line}")
        print(
            "\nA reference to something unimplemented is fine, but it needs a "
            "recorded decision.\nAdd the entry point, subcommand, or file, or "
            "declare the gap in tools/documented-gaps.toml\nwith the record that "
            "authorizes it."
        )
        return 1

    print("doc consistency: ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
