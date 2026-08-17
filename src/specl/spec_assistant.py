"""spec_assistant.py — LLM helpers for the SPECL spec. Ollama only.

  python spec_assistant.py gaps   spec.ttl shapes.ttl [--model llama3.1]
  python spec_assistant.py check  spec.ttl            [--model llama3.1]

`gaps` reads SHACL warnings and, for each, prints a targeted question
plus a drafted answer for human approval. Never writes the spec.
`check` asks the LLM to flag contradictions, duplications, and
requirements that talk past each other. Emits findings as OpenIssue
stubs you can paste into the spec.
"""
from __future__ import annotations
import os, sys, json, argparse, urllib.request

from rdflib import RDF, URIRef

from specl.validate_spec import bundled_shapes, load, run_shacl, SPECL

# One code path for Ollama, vLLM, llama.cpp, and hosted providers, because all
# of them speak the OpenAI chat-completions shape. The default is the local
# Ollama endpoint, so nothing that worked before needs configuring.
DEFAULT_ENDPOINT = "http://localhost:11434/v1/chat/completions"

# Named endpoints, so nobody has to remember a base URL or discover by trial
# that a provider needs a trailing path segment. Anthropic publishes an
# OpenAI-compatible layer, so Claude needs no separate code path: see
# https://platform.claude.com/docs/en/api/openai-sdk
PROVIDERS = {
    "ollama": "http://localhost:11434/v1/chat/completions",
    "claude": "https://api.anthropic.com/v1/chat/completions",
    "openai": "https://api.openai.com/v1/chat/completions",
    "vllm": "http://localhost:8000/v1/chat/completions",
    "llamacpp": "http://localhost:8080/v1/chat/completions",
}
DESCRIPTION = URIRef("http://purl.org/dc/terms/description")


def endpoint(args):
    if getattr(args, "endpoint", None):
        return args.endpoint
    provider = getattr(args, "provider", None)
    if provider:
        return PROVIDERS[provider]
    return os.environ.get("SPECL_LLM_ENDPOINT") or DEFAULT_ENDPOINT


def api_key(args):
    return getattr(args, "api_key", None) or os.environ.get("SPECL_LLM_API_KEY")


def ask(args, prompt):
    """One request, in the shape every provider on this path accepts.

    Nothing here is specific to a vendor. A key is sent only when one is
    configured, because a local endpoint does not want an Authorization header
    and some reject the request outright when it carries one.
    """
    # max_tokens is sent unconditionally. It is optional for some servers and
    # required by others, and an omitted field that fails only against one
    # provider is the kind of difference nobody finds until they switch.
    body = json.dumps({
        "model": args.model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": getattr(args, "max_tokens", 1024),
        "stream": False,
    }).encode()
    headers = {"Content-Type": "application/json"}
    key = api_key(args)
    if key:
        headers["Authorization"] = f"Bearer {key}"
    req = urllib.request.Request(endpoint(args), data=body, headers=headers)
    with urllib.request.urlopen(req, timeout=args.timeout) as r:
        payload = json.loads(r.read())
    return payload["choices"][0]["message"]["content"].strip()

def cmd_gaps(args):
    g, s = load(args.data), load(args.shapes)
    _, results, _ = run_shacl(g, s)
    warnings = [r for r in results if r["severity"] == "Warning"]
    print(f"Found {len(warnings)} warnings. Drafting prompts...\n")
    for w in warnings:
        # Pull the requirement description for context
        ctx = str(g.value(URIRef(w["focus"]), DESCRIPTION) or "")
        prompt = (f"Requirement: {ctx}\nGap: {w['message']}\n"
                  f"Draft a concise answer (1-3 sentences) the spec author can review. "
                  f"Do not invent facts; if unclear, say what information is needed.")
        print(f"--- {w['focus'].split('/')[-1]} ---")
        print(f"Gap: {w['message']}")
        try:
            print(f"Draft: {ask(args, prompt)}\n")
        except Exception as e:
            print(f"[{endpoint(args)}: {e}]\n")

def cmd_check(args):
    g = load(args.data)
    reqs = []
    for r in g.subjects(RDF.type, SPECL.Requirement):
        desc = g.value(r, DESCRIPTION)
        reqs.append(f"{str(r).split('/')[-1]}: {desc}")
    corpus = "\n".join(reqs)
    prompt = ("You are reviewing a software specification for internal consistency. "
              "Identify contradictions, duplications, and requirements that appear to "
              "talk past each other. Output each finding as a markdown bullet under "
              "an 'Open Issues' heading. Do not rewrite requirements.\n\n"
              f"Requirements:\n{corpus}")
    print(ask(args, prompt))

def cmd_suggest_annotations(args):
    """Annotation stubs for what the shapes say is missing, deferred since 0.2.0.

    Stubs, not answers. Every line printed is pasteable and every value is a
    placeholder the author replaces, because a plausible acceptance criterion
    nobody checked is worse than an absent one: the shapes stop reporting it and
    the gap becomes invisible.
    """
    g, sh = load(args.data), load(args.shapes)
    _, results, _ = run_shacl(g, sh)
    missing = {}
    for r in results:
        path = str(r.get("path") or "")
        if not path.startswith(str(SPECL)):
            continue
        missing.setdefault(r["focus"], set()).add(path.split("#")[-1])

    keys = {
        "acceptanceCriterion": "acceptance", "verifiedBy": "verifiedBy",
        "constrains": "constrains", "priority": "priority",
        "asA": "asA", "iWant": "iWant", "soThat": "soThat",
        "recommendation": "recommendation", "rationale": "rationale",
        "gates": "gates",
    }
    placeholder = {
        "acceptance": "Given <precondition> when <action> then <observable>",
        "verifiedBy": "tests/<file>.py::<test>",
        "constrains": "<component>",
        "priority": "MUST",
        "gates": "<requirement id>",
    }
    if not missing:
        print("No annotation gaps reported by the shapes.")
        return
    for focus in sorted(missing):
        lines = [
            f"  - {keys[p]}: {placeholder.get(keys[p], '<' + keys[p] + '>')}"
            for p in sorted(missing[focus]) if p in keys
        ]
        if not lines:
            continue
        print(f"--- {focus.split('#')[-1]} ---")
        print(str(g.value(URIRef(focus), DESCRIPTION) or "").strip())
        print("\n".join(lines))
        print()


def main():
    p = argparse.ArgumentParser(prog="specl-assist")
    sub = p.add_subparsers(dest="cmd", required=True)
    for name, fn in [("gaps", cmd_gaps), ("check", cmd_check),
                     ("suggest-annotations", cmd_suggest_annotations)]:
        sp = sub.add_parser(name)
        sp.add_argument("data")
        if name in ("gaps", "suggest-annotations"):
            sp.add_argument("shapes", nargs="?", default=None,
                            help="defaults to the shapes bundled with specl")
        sp.add_argument("--model", default="llama3.1")
        sp.add_argument("--provider", choices=sorted(PROVIDERS),
                        help="named endpoint. Overridden by --endpoint.")
        sp.add_argument("--max-tokens", type=int, default=1024)
        sp.add_argument("--endpoint", metavar="URL",
                        help="OpenAI-compatible chat-completions endpoint. "
                             "Defaults to SPECL_LLM_ENDPOINT, then to local Ollama.")
        sp.add_argument("--api-key", metavar="KEY",
                        help="sent as a bearer token when set; defaults to "
                             "SPECL_LLM_API_KEY. Omitted entirely when unset, "
                             "because local endpoints reject the header.")
        sp.add_argument("--timeout", type=int, default=120)
        sp.set_defaults(func=fn)
    args = p.parse_args()
    if getattr(args, "shapes", None) is None and hasattr(args, "shapes"):
        args.shapes = bundled_shapes()
    args.func(args)

if __name__ == "__main__":
    main()
