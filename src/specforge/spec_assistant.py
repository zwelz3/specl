"""spec_assistant.py — LLM helpers for the EKGA spec. Ollama only.

  python spec_assistant.py gaps   spec.ttl shapes.ttl [--model llama3.1]
  python spec_assistant.py check  spec.ttl            [--model llama3.1]

`gaps` reads SHACL warnings and, for each, prints a targeted question
plus a drafted answer for human approval. Never writes the spec.
`check` asks the LLM to flag contradictions, duplications, and
requirements that talk past each other. Emits findings as OpenIssue
stubs you can paste into the spec.
"""
from __future__ import annotations
import sys, json, argparse, urllib.request
from validate_spec import load, run_shacl

OLLAMA = "http://localhost:11434/api/generate"

def ask(model, prompt):
    data = json.dumps({"model": model, "prompt": prompt, "stream": False}).encode()
    req = urllib.request.Request(OLLAMA, data=data, headers={"Content-Type":"application/json"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read())["response"].strip()

def cmd_gaps(args):
    g, s = load(args.data), load(args.shapes)
    _, results, _ = run_shacl(g, s)
    warnings = [r for r in results if r["severity"] == "Warning"]
    print(f"Found {len(warnings)} warnings. Drafting prompts...\n")
    for w in warnings:
        # Pull the requirement description for context
        ctx = ""
        for p, o in g.predicate_objects(__import__("rdflib").URIRef(w["focus"])):
            if "description" in str(p): ctx = str(o); break
        prompt = (f"Requirement: {ctx}\nGap: {w['message']}\n"
                  f"Draft a concise answer (1-3 sentences) the spec author can review. "
                  f"Do not invent facts; if unclear, say what information is needed.")
        print(f"--- {w['focus'].split('/')[-1]} ---")
        print(f"Gap: {w['message']}")
        try:
            print(f"Draft: {ask(args.model, prompt)}\n")
        except Exception as e:
            print(f"[ollama error: {e}]\n")

def cmd_check(args):
    g = load(args.data)
    reqs = []
    for r in g.subjects(__import__("rdflib").RDF.type,
                        __import__("rdflib").URIRef("https://example.org/ekga/ns#Requirement")):
        desc = g.value(r, __import__("rdflib").URIRef("http://purl.org/dc/terms/description"))
        reqs.append(f"{str(r).split('/')[-1]}: {desc}")
    corpus = "\n".join(reqs)
    prompt = ("You are reviewing a software specification for internal consistency. "
              "Identify contradictions, duplications, and requirements that appear to "
              "talk past each other. Output each finding as a markdown bullet under "
              "an 'Open Issues' heading. Do not rewrite requirements.\n\n"
              f"Requirements:\n{corpus}")
    print(ask(args.model, prompt))

def main():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)
    for name, fn in [("gaps", cmd_gaps), ("check", cmd_check)]:
        sp = sub.add_parser(name)
        sp.add_argument("data")
        if name == "gaps": sp.add_argument("shapes")
        sp.add_argument("--model", default="llama3.1")
        sp.set_defaults(func=fn)
    args = p.parse_args(); args.func(args)

if __name__ == "__main__":
    main()
