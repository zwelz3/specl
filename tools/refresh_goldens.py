#!/usr/bin/env python3
"""Regenerate tests/golden from current translator behavior.

Run after an intentional change to the emission surface, then read the diff.
The diff is the review: it should contain the change being made and nothing
else.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tests"))
from conftest import GOLDEN, PUBLISHED, FIXTURE_SPECS, normalize, spec_path, translate  # noqa: E402


def main() -> int:
    GOLDEN.mkdir(exist_ok=True)
    for name in PUBLISHED + FIXTURE_SPECS:
        target = GOLDEN / f"{name}.ttl"
        result = translate(spec_path(name), target)
        if result.returncode != 0:
            print(f"{name}: FAILED\n{result.stderr}")
            return 1
        target.write_text(normalize(target.read_text(encoding="utf-8")), encoding="utf-8")
        print(f"{name}: {len(target.read_text(encoding='utf-8').splitlines())} lines")
    return 0


if __name__ == "__main__":
    sys.exit(main())
