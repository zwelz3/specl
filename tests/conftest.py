"""Shared paths and helpers for the specl test suite.

Goldens capture what the translator does today, defects included. That is the
point of them: when P16 widens the identifier grammar or P3 rebases every IRI,
the golden diff is exactly the change and nothing else.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
GOLDEN = Path(__file__).resolve().parent / "golden"
FIXTURES = Path(__file__).resolve().parent / "fixtures"
SHAPES = SRC / "specl" / "shapes.ttl"

# Specifications this project publishes, and fixtures that only feed tests.
# A directory is a specification only if it holds a spec.md. tests/fixtures also
# carries pre-0.3.0 Turtle for the migration tool, which has no markdown source
# and must not be swept into the golden or grammar suites.
PUBLISHED = sorted(
    p.name for p in (ROOT / "specs").iterdir() if (p / "spec.md").exists()
)
FIXTURE_SPECS = sorted(
    p.name for p in FIXTURES.iterdir() if (p / "spec.md").exists()
)

def normalize(turtle: str) -> str:
    """Kept as a seam, now the identity.

    Goldens were normalized because the translator stamped translation time into
    dct:created, so output differed across days. P17 emits the property only
    when a specification supplies one, and every comparison is byte-for-byte
    against unmodified output.
    """
    return turtle


def spec_path(name: str) -> Path:
    published = ROOT / "specs" / name / "spec.md"
    return published if published.exists() else FIXTURES / name / "spec.md"


def translate(source: Path, target: Path, *extra: str) -> subprocess.CompletedProcess:
    """Run the translator as a subprocess, the way CI and users invoke it."""
    return subprocess.run(
        [sys.executable, "-m", "specl.spec_to_rdf", str(source), str(target), *extra],
        cwd=ROOT,
        env={"PYTHONPATH": str(SRC), "PATH": "/usr/bin:/bin"},
        capture_output=True,
        text=True,
    )


@pytest.fixture(scope="session")
def all_specs() -> list[str]:
    return PUBLISHED + FIXTURE_SPECS
