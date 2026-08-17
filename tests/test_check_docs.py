"""Regression tests for the documentation checker.

Every hole found in this checker so far came from an unanchored pattern, and
each was found by hand rather than by a test. These cover the three.
"""
from __future__ import annotations

import shutil
import subprocess
import sys

from conftest import ROOT


def run(tree):
    return subprocess.run(
        [sys.executable, "tools/check_docs.py"], cwd=tree, capture_output=True, text=True
    )


def copy_tree(tmp_path):
    dest = tmp_path / "repo"
    shutil.copytree(
        ROOT, dest, ignore=shutil.ignore_patterns(".git", "__pycache__", ".venv")
    )
    return dest


def test_clean_tree_passes(tmp_path):
    assert run(copy_tree(tmp_path)).returncode == 0


def test_umbrella_command_is_caught(tmp_path):
    tree = copy_tree(tmp_path)
    (tree / "docs" / "ROADMAP.md").write_text(
        (tree / "docs" / "ROADMAP.md").read_text(encoding="utf-8") + "\n\nRun `specl frobnicate x`.\n"
    , encoding="utf-8")
    result = run(tree)
    assert result.returncode == 1 and "specl frobnicate" in result.stdout


def test_missing_path_is_not_suppressed_by_nearby_prose(tmp_path):
    tree = copy_tree(tmp_path)
    (tree / "docs" / "ROADMAP.md").write_text(
        (tree / "docs" / "ROADMAP.md").read_text(encoding="utf-8")
        + "\n\nSee `docs/nope/absent.md`. The old draft is missing, so that one is current.\n"
    , encoding="utf-8")
    result = run(tree)
    assert result.returncode == 1 and "docs/nope/absent.md" in result.stdout


def test_identifier_is_not_read_as_a_command(tmp_path):
    tree = copy_tree(tmp_path)
    (tree / "docs" / "ROADMAP.md").write_text(
        (tree / "docs" / "ROADMAP.md").read_text(encoding="utf-8") + "\n\nThe id `specl-tool-001` is a label.\n"
    , encoding="utf-8")
    assert run(tree).returncode == 0


def test_stale_extraction_pattern_fails_loudly(tmp_path):
    tree = copy_tree(tmp_path)
    source = tree / "src" / "specl" / "validate_spec.py"
    source.write_text(source.read_text(encoding="utf-8").replace('add_parser("', "add_parser(NAME_"), encoding="utf-8")
    result = run(tree)
    assert result.returncode == 1 and "extraction pattern is stale" in result.stdout


def test_dead_w3id_redirect_target_is_caught(tmp_path):
    """The vendored rules are the source of truth for a pull request against
    another repository, so a dead target here becomes a live 404 elsewhere."""
    tree = copy_tree(tmp_path)
    rules = tree / "tools" / "w3id" / "specl.htaccess"
    rules.write_text(rules.read_text(encoding="utf-8").replace("docs/contracts/1.md", "docs/contracts/9.md"), encoding="utf-8")
    result = run(tree)
    assert result.returncode == 1 and "docs/contracts/9.md" in result.stdout


def test_site_asset_the_build_does_not_produce_is_caught(tmp_path):
    tree = copy_tree(tmp_path)
    rules = tree / "tools" / "w3id" / "specl.htaccess"
    rules.write_text(rules.read_text(encoding="utf-8").replace("specl/ns.jsonld", "specl/ns.rdf"), encoding="utf-8")
    result = run(tree)
    assert result.returncode == 1 and "ns.rdf" in result.stdout


def test_the_publish_workflow_refuses_pre_1_0(tmp_path):
    """0007 says releases are tagged and published once, at 1.0. The publish
    workflow fires on any published GitHub release, so tagging through the UI
    would have pushed to PyPI and broken the policy silently."""
    workflow = (ROOT / ".github" / "workflows" / "publish.yml").read_text(encoding="utf-8")
    assert "Refuse to publish before 1.0" in workflow
    assert "0007-internal-releases-until-1.0.md" in workflow


def test_the_supported_python_range_is_actually_tested():
    """A support claim nobody runs is a claim the first adopter tests for you.

    The floor was 3.10 while CI ran 3.12 alone, and the repository tooling uses
    tomllib, which is 3.11 and later.
    """
    import re

    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    workflow = (ROOT / ".github" / "workflows" / "spec.yml").read_text(encoding="utf-8")
    floor = re.search(r'requires-python\s*=\s*">=(\d+)\.(\d+)"', pyproject)
    assert floor, "requires-python not found; the pattern is stale"
    assert "windows-latest" in workflow, (
        "the suite runs on one platform, which is how three encoding defects "
        "reached an adopter"
    )
    matrix = re.search(r"python-version:\s*\[([^\]]+)\]", workflow)
    assert matrix, "no python-version matrix in the workflow"
    tested = set(re.findall(r"'(\d+\.\d+)'", matrix.group(1)))
    assert f"{floor.group(1)}.{floor.group(2)}" in tested, (
        f"pyproject claims >={floor.group(0)} and CI does not test that version"
    )


def test_the_w3id_pending_table_names_every_rule_not_yet_upstream():
    """The table drifted once already: it was written at 0.7.0 and never gained
    the versioned locations or contract 2, so someone reading it would have
    understated the change they were filing."""
    import re

    rules = (ROOT / "tools" / "w3id" / "specl.htaccess").read_text(encoding="utf-8")
    readme = (ROOT / "tools" / "w3id" / "README.md").read_text(encoding="utf-8")
    table = readme[readme.index("## What is pending"):]
    patterns = {m.group(1) for m in re.finditer(r"^RewriteRule\s+\^(\S+?)/\?\$", rules, re.M)}
    # Rules live upstream since before this project's review round.
    already_live = {"ns", "shapes", "explorer"}
    for pattern in sorted(patterns - already_live):
        assert f"`^{pattern}`" in table, (
            f"^{pattern} is in the rules file and not named in the pending table"
        )


def test_a_badge_url_for_a_missing_specification_is_caught(tmp_path):
    """Badges are generated by a loop over specs/, so the build produces one per
    specification and nothing else. Exempting the directory wholesale would let
    a URL for a specification that does not exist render as a broken image."""
    tree = copy_tree(tmp_path)
    readme = tree / "README.md"
    readme.write_text(
        readme.read_text(encoding="utf-8").replace(
            "badges/specl_tool.svg", "badges/ghost.svg"
        ),
        encoding="utf-8",
    )
    result = run(tree)
    assert result.returncode == 1
    assert "names no specification" in result.stdout
