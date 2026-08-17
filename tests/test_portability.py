"""Text I/O that assumes the platform's default encoding.

Python picks the locale encoding when none is given: UTF-8 on Linux, cp1252 on
most Windows installs. Every check in this repository ran on Ubuntu, so a
hundred and ten encoding-less reads sat here until an adopter ran the suite on
Windows and three tests failed on a single non-ASCII byte in `explorer.html`.

Only three failed because only one shipped file happens to carry non-ASCII
today. The rest were equally wrong and merely lucky, which is why this checks
the pattern rather than the symptom.
"""
from __future__ import annotations

import re

from conftest import ROOT

CALLS = re.compile(r"(?<![\w.])(?:\w+\.)?(read_text|write_text|open)\(")
BINARY = re.compile(r"""["'][rwax]b["']""")
SEARCHED = ("src", "tests", "tools")


def arguments(line: str, start: int) -> str | None:
    """The full argument text of a call, counting nested parentheses.

    A pattern that stops at the first close paren reports
    `write_text(f(x), encoding="utf-8")` as unencoded, because the nested call
    ends the match before the keyword. Widening the pattern only moves the
    blind spot, so the parentheses are counted.
    """
    depth, out = 0, []
    for char in line[start:]:
        if char == "(":
            depth += 1
            if depth == 1:
                continue
        elif char == ")":
            depth -= 1
            if depth == 0:
                return "".join(out)
        out.append(char)
    return None


def python_files():
    for directory in SEARCHED:
        for path in sorted((ROOT / directory).rglob("*.py")):
            if "__pycache__" not in path.parts:
                yield path


def test_no_text_io_relies_on_the_platform_encoding():
    offenders = []
    for path in python_files():
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if "urlopen" in line or "subprocess.run" in line:
                continue
            for match in CALLS.finditer(line):
                args = arguments(line, match.end() - 1)
                if args is None or "encoding=" in args:
                    continue
                if match.group(1) == "open" and BINARY.search(args):
                    continue
                # `files(...) / name` returns a Traversable, whose read_text
                # already defaults to UTF-8 rather than to the locale.
                if match.group(1) == "read_text" and not args.strip():
                    if "files(" in line:
                        continue
                offenders.append(f"{path.relative_to(ROOT)}:{number}: {line.strip()}")
    assert not offenders, (
        "text I/O without an explicit encoding reads as cp1252 on Windows:\n  "
        + "\n  ".join(offenders)
    )


def test_the_shipped_file_that_exposed_this_still_has_non_ascii():
    """If `explorer.html` ever becomes pure ASCII, the check above is the only
    thing standing between this defect and its return."""
    raw = (ROOT / "src" / "specl" / "explorer.html").read_bytes()
    assert any(byte > 127 for byte in raw)
