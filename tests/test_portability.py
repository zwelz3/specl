"""Text I/O that assumes the platform's default encoding.

Python picks the locale encoding when none is given: UTF-8 on Linux, cp1252 on
most Windows installs. Every check here ran on Ubuntu, so 110 encoding-less
calls sat in the tree until an adopter ran the suite on Windows.

The first round fixed the reads and the second round found ten writes it had
missed, so this walks the AST rather than matching text. A call spanning two
lines defeated the line-based version, and worse, it treated a call it could not
parse as passing: a check that silently stops checking is the failure mode
`docs/decisions/0006-artifact-agreement-strategy.md` names explicitly, and this
one committed it.
"""
from __future__ import annotations

import ast

import pytest

from conftest import ROOT

TEXT_IO = ("read_text", "write_text", "open")
SEARCHED = ("src", "tests", "tools")


def unencoded_calls(path):
    """Every text read or write in a file that does not name an encoding.

    Parsed rather than pattern-matched. A syntax error raises rather than
    returning nothing, because a file this cannot read is a file it is not
    checking.
    """
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        name = func.attr if isinstance(func, ast.Attribute) else getattr(func, "id", None)
        if name not in TEXT_IO:
            continue
        if any(keyword.arg == "encoding" for keyword in node.keywords):
            continue
        if name == "open":
            # A bare `open` in binary mode takes no encoding, and an attribute
            # `.open` is something else entirely, such as a zipfile member.
            if isinstance(func, ast.Attribute):
                continue
            mode = node.args[1] if len(node.args) > 1 else None
            if isinstance(mode, ast.Constant) and "b" in str(mode.value):
                continue
        yield node.lineno


def python_files():
    for directory in SEARCHED:
        for path in sorted((ROOT / directory).rglob("*.py")):
            if "__pycache__" not in path.parts:
                yield path


def test_no_text_io_relies_on_the_platform_encoding():
    offenders = [
        f"{path.relative_to(ROOT)}:{line}"
        for path in python_files()
        for line in unencoded_calls(path)
    ]
    assert not offenders, (
        "text I/O without an explicit encoding uses cp1252 on Windows:\n  "
        + "\n  ".join(offenders)
    )


def test_the_checker_sees_a_call_split_across_lines():
    """The specific blind spot that let ten writes through. A line-based scan
    found the opening parenthesis, never found the closing one, and treated the
    unparseable result as fine."""
    source = ROOT / "tests" / "_portability_probe.py"
    source.write_text(
        "from pathlib import Path\n"
        "def f(p: Path):\n"
        "    p.write_text(\n"
        '        "text"\n'
        "    )\n",
        encoding="utf-8",
    )
    try:
        assert list(unencoded_calls(source)) == [3]
    finally:
        source.unlink()


def test_a_file_it_cannot_parse_raises_rather_than_passing():
    source = ROOT / "tests" / "_portability_broken.py"
    source.write_text("def f(\n", encoding="utf-8")
    try:
        with pytest.raises(SyntaxError):
            list(unencoded_calls(source))
    finally:
        source.unlink()


def test_the_shipped_file_that_exposed_this_still_has_non_ascii():
    """If `explorer.html` ever becomes pure ASCII, the check above is the only
    thing standing between this defect and its return."""
    raw = (ROOT / "src" / "specl" / "explorer.html").read_bytes()
    assert any(byte > 127 for byte in raw)
