"""Ergonomics: the diff side effect, the assistant endpoint, and stub suggestion.

P12 and P11, plus the assistant decoupling. None of these is subtle; two of them
are the kind of defect that survives because nobody writes a test for a side
effect they have stopped noticing.
"""
from __future__ import annotations

import subprocess
import sys

import pytest

from conftest import ROOT, SHAPES, SRC, translate

pytest.importorskip("rdflib")

HEAD = "---\ntitle: T\nspec_base: https://example.org/specs/t#\nspec_id: t-001\n---\n\n"


def run(module, *args, cwd=None):
    return subprocess.run(
        [sys.executable, "-m", module, *args],
        cwd=cwd or ROOT, env={"PYTHONPATH": str(SRC), "PATH": "/usr/bin:/bin"},
        capture_output=True, text=True,
    )


@pytest.fixture
def graph(tmp_path):
    source = tmp_path / "s.md"
    source.write_text(HEAD + "# Requirements\n\n- R1 The system must persist records.\n", encoding="utf-8")
    target = tmp_path / "s.ttl"
    translate(source, target)
    return target


def test_diff_writes_nothing_by_default(tmp_path, graph):
    """P12. It appended to CHANGELOG.spec.md in the working directory on every
    invocation, including read-only inspection, and duplicated on a second run."""
    before = set(tmp_path.iterdir())
    result = run("specl.validate_spec", "diff", str(graph), str(graph), cwd=tmp_path)
    assert result.returncode == 0
    assert set(tmp_path.iterdir()) == before
    assert not (tmp_path / "CHANGELOG.spec.md").exists()


def test_diff_writes_where_asked(tmp_path, graph):
    out = tmp_path / "changes.md"
    result = run("specl.validate_spec", "diff", str(graph), str(graph),
                 "--changelog", str(out), cwd=tmp_path)
    assert result.returncode == 0 and out.exists()
    assert "## diff" in out.read_text(encoding="utf-8")


def test_suggest_annotations_needs_no_model(graph):
    """Stubs come from the shapes, not from a model. A plausible acceptance
    criterion nobody checked is worse than an absent one: the shapes stop
    reporting it and the gap becomes invisible."""
    result = run("specl.spec_assistant", "suggest-annotations", str(graph), str(SHAPES))
    assert result.returncode == 0
    assert "- acceptance: Given <precondition>" in result.stdout
    assert "<" in result.stdout, "every value is a placeholder"


def test_the_endpoint_is_configurable_and_defaults_locally():
    from specl.spec_assistant import DEFAULT_ENDPOINT, endpoint
    import argparse

    assert DEFAULT_ENDPOINT.startswith("http://localhost")
    assert endpoint(argparse.Namespace(endpoint=None)) == DEFAULT_ENDPOINT
    assert endpoint(argparse.Namespace(endpoint="https://api.example/v1/chat/completions")) == (
        "https://api.example/v1/chat/completions"
    )


def test_no_authorization_header_without_a_key(monkeypatch):
    """A local endpoint does not want one, and some reject the request outright
    when it carries one."""
    import argparse
    from specl import spec_assistant

    monkeypatch.delenv("SPECL_LLM_API_KEY", raising=False)
    captured = {}

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def read(self):
            return b'{"choices":[{"message":{"content":"ok"}}]}'

    def fake_urlopen(req, timeout=None):
        captured["headers"] = dict(req.header_items())
        return FakeResponse()

    monkeypatch.setattr(spec_assistant.urllib.request, "urlopen", fake_urlopen)
    args = argparse.Namespace(model="m", endpoint=None, api_key=None, timeout=5)
    assert spec_assistant.ask(args, "hello") == "ok"
    assert not any(k.lower() == "authorization" for k in captured["headers"])

    args.api_key = "secret"
    spec_assistant.ask(args, "hello")
    assert captured["headers"].get("Authorization") == "Bearer secret"


def test_claude_needs_no_separate_code_path():
    """Anthropic publishes an OpenAI-compatible chat-completions layer, so the
    provider is a URL rather than an adapter."""
    import argparse
    from specl.spec_assistant import PROVIDERS, endpoint

    assert PROVIDERS["claude"] == "https://api.anthropic.com/v1/chat/completions"
    assert endpoint(argparse.Namespace(endpoint=None, provider="claude")) == PROVIDERS["claude"]
    assert endpoint(
        argparse.Namespace(endpoint="https://gateway.example/v1/chat/completions",
                           provider="claude")
    ) == "https://gateway.example/v1/chat/completions", "--endpoint wins over --provider"


def test_max_tokens_is_always_sent(monkeypatch):
    """Optional for some servers, required by others. An omitted field that
    fails against one provider only is found the day someone switches."""
    import argparse
    import json as _json
    from specl import spec_assistant

    captured = {}

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def read(self):
            return b'{"choices":[{"message":{"content":"ok"}}]}'

    def fake_urlopen(req, timeout=None):
        captured["body"] = _json.loads(req.data)
        return FakeResponse()

    monkeypatch.setattr(spec_assistant.urllib.request, "urlopen", fake_urlopen)
    spec_assistant.ask(
        argparse.Namespace(model="m", endpoint=None, provider="claude",
                           api_key=None, timeout=5, max_tokens=256),
        "hello",
    )
    assert captured["body"]["max_tokens"] == 256


def test_shapes_default_to_the_bundled_file(tmp_path):
    """OQ2, closed. `specl-validate validate spec.ttl` is the first command an
    adopter runs, and it failed on a fresh install because the shapes path was
    required and nothing says where the bundled file lives."""
    source = tmp_path / "s.md"
    source.write_text(HEAD + "# Requirements\n\n- R1 The system must persist records.\n", encoding="utf-8")
    target = tmp_path / "s.ttl"
    translate(source, target)
    for cmd in ("validate", "score"):
        result = run("specl.validate_spec", cmd, str(target))
        assert result.returncode == 0, f"{cmd}: {result.stderr}"
    assert run("specl.spec_assistant", "suggest-annotations", str(target)).returncode == 0
