"""Rewrite a pre-0.3.0 graph onto a specification's own base.

Before 0.3.0 every specification minted items under one shared namespace,
`https://w3id.org/specl/spec#`, so `spec:R1.1` meant a different requirement
depending on which file it came from. 0.3.0 gives each specification its own
base and retires the shared one without reassigning it.

A project that still has the markdown migrates by regenerating; that path is
better because it also picks up titles, IRI-valued references, and the contract
declaration. This tool exists for a consumer holding only Turtle.

Usage: specl-migrate iris <in.ttl> <out.ttl> --base <https://.../spec#>
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from rdflib import Graph, Literal, URIRef

from .spec_to_rdf import (
    BULLET_RE,
    CONTRACT,
    CURIE_RE,
    LEGACY_SPEC_BASE,
    REFERENCE_KEYS,
    SAFE_LOCAL_RE,
    SpecError,
    check_base,
    derive_title,
    slug,
)

SPECL = "https://w3id.org/specl/ns#"
SPECIFICATION = URIRef(SPECL + "Specification")
RDF_TYPE = URIRef("http://www.w3.org/1999/02/22-rdf-syntax-ns#type")
DCT = "http://purl.org/dc/terms/"
TITLE = URIRef(DCT + "title")
DESCRIPTION = URIRef(DCT + "description")
IDENTIFIER = URIRef(DCT + "identifier")
CONFORMS_TO = URIRef(DCT + "conformsTo")
SKOS = "http://www.w3.org/2004/02/skos/core#"


def legacy_nodes(graph: Graph) -> set[URIRef]:
    return {
        n for n in graph.all_nodes()
        if isinstance(n, URIRef) and str(n).startswith(LEGACY_SPEC_BASE)
    } | {
        p for p in set(graph.predicates())
        if str(p).startswith(LEGACY_SPEC_BASE)
    }


def build_mapping(graph: Graph, base: str) -> dict[URIRef, URIRef]:
    """Two rules, because the Specification node did not move the way items did.

    An item is the base plus its token, which is a substitution of one prefix
    for another. The Specification is the base without its terminator, which is
    not a substitution at all: `spec:xlsvc-001` becomes
    `https://example.org/specs/excel_service`, dropping the identifier entirely.
    The old value survives as `dct:identifier` if the caller regenerates; this
    tool leaves whatever the graph already carries.
    """
    specs = list(graph.subjects(RDF_TYPE, SPECIFICATION))
    if len(specs) != 1:
        raise SpecError(
            f"the graph declares {len(specs)} specifications and this tool "
            "migrates one at a time. A merged pre-0.3.0 graph cannot be "
            "migrated at all: its items collided, so which specification an "
            "item belonged to is no longer recoverable. Migrate each source "
            "graph separately, then merge."
        )
    mapping = {specs[0]: URIRef(base[:-1])}
    for node in legacy_nodes(graph):
        if node not in mapping:
            mapping[node] = URIRef(base + str(node)[len(LEGACY_SPEC_BASE):])
    return mapping


def rewrite(graph: Graph, mapping: dict[URIRef, URIRef]) -> Graph:
    out = Graph()
    for prefix, namespace in graph.namespaces():
        if str(namespace) != LEGACY_SPEC_BASE:
            out.bind(prefix, namespace)
    for s, p, o in graph:
        out.add((mapping.get(s, s), mapping.get(p, p), mapping.get(o, o)))
    return out


def convert_references(graph: Graph, base: str, warnings: list[str]) -> Graph:
    """Turn the three object properties from literals into IRIs.

    The same three outcomes the translator applies, so a migrated graph matches
    what regenerating from the markdown would have produced. Reusing the
    translator's own patterns rather than restating them keeps one source of
    truth for the rules.
    """
    known = {
        str(s)[len(base):] for s in graph.subjects()
        if str(s).startswith(base)
    }
    for key, cls in REFERENCE_KEYS.items():
        prop = URIRef(SPECL + key)
        for subject, obj in list(graph.subject_objects(prop)):
            if not isinstance(obj, Literal):
                continue
            token = str(obj).strip()
            if BULLET_RE.match(f"- {token} x"):
                if token not in known:
                    warnings.append(
                        f"{subject}: {key} references {token!r}, which no item "
                        "in this graph declares"
                    )
                target = URIRef(base + token)
            elif CURIE_RE.match(token) or cls is None:
                warnings.append(
                    f"{subject}: {key} value {token!r} is not an identifier and "
                    "names no external artifact type; left as a literal"
                )
                continue
            else:
                local = token if SAFE_LOCAL_RE.match(token) else slug(token)
                target = URIRef(f"{base}{cls.lower()}-{local}")
                graph.add((target, RDF_TYPE, URIRef(SPECL + cls)))
                graph.add((target, IDENTIFIER, Literal(token)))
            graph.remove((subject, prop, obj))
            graph.add((subject, prop, target))
    return graph


def add_missing_titles(graph: Graph, base: str) -> int:
    """Derive the titles a regenerated graph would have materialized.

    The derivation is deterministic and specified, so applying it here produces
    the same values regenerating would, rather than inventing anything.
    """
    added = 0
    for subject in set(graph.subjects()):
        if not str(subject).startswith(base):
            continue
        if graph.value(subject, TITLE) is not None:
            continue
        description = graph.value(subject, DESCRIPTION)
        if description is None:
            continue
        graph.add((subject, TITLE, Literal(derive_title(str(description)))))
        added += 1
    return added


# Renamed in contract 2. Every graph a consumer holds under contract 1 carries
# the old names, and renaming a property is precisely what a designated breaking
# release is for, so the migration is mechanical and total.
CONTRACT_2_RENAMES = {
    "iWant": "capability",
    "soThat": "benefit",
}


def _contract_base(graph: Graph) -> str:
    spec = next(iter(graph.subjects(RDF_TYPE, SPECIFICATION)), None)
    return f"{spec}#" if spec else ""


def cmd_contract(args) -> int:
    """Move a contract 1 graph to contract 2.

    Two changes. The user story properties are renamed to say what they mean
    rather than which fragment of a sentence template they came from. And
    content-hash IRIs for design notes and comments are reported rather than
    rewritten: the identifier was a function of the prose, so nothing in the
    graph says what it should become. That one needs the source.
    """
    source, target = Path(args.src), Path(args.dst)
    if source.resolve() == target.resolve():
        print("error: refusing to overwrite the input graph", file=sys.stderr)
        return 2

    graph = Graph().parse(source)
    base = _contract_base(graph)
    renamed = 0
    for old, new in CONTRACT_2_RENAMES.items():
        old_p, new_p = URIRef(SPECL + old), URIRef(SPECL + new)
        for s_, o in list(graph.subject_objects(old_p)):
            graph.remove((s_, old_p, o))
            graph.add((s_, new_p, o))
            renamed += 1

    # specl:asA held a name; specl:role names a declared persona. One node per
    # distinct literal is faithful rather than a guess: two stories that said
    # the same string meant the same person in the old graph, and two that said
    # different strings were already distinct there. Any fragmentation this
    # produces was present in contract 1, which is the defect the change fixes
    # going forward rather than retroactively.
    old_role = URIRef(SPECL + "asA")
    role, persona = URIRef(SPECL + "role"), URIRef(SPECL + "Persona")
    minted = {}
    for s_, o in list(graph.subject_objects(old_role)):
        name = str(o)
        if name not in minted:
            node = URIRef(f"{base}persona-{slug(name)}")
            graph.add((node, RDF_TYPE, persona))
            graph.add((node, TITLE, Literal(name)))
            graph.add((node, URIRef(SKOS + "prefLabel"), Literal(name)))
            minted[name] = node
        graph.remove((s_, old_role, o))
        graph.add((s_, role, minted[name]))
    if minted:
        print(f"minted {len(minted)} persona(s) from specl:asA literals")

    # specl:owner held a name and now names a declared agent. Same reasoning as
    # the persona case: one node per distinct literal is faithful, because two
    # items that said the same string meant the same person under contract 1.
    old_owner = URIRef(SPECL + "owner")
    agent_cls = URIRef(SPECL + "Agent")
    agents = {}
    for s_, o in list(graph.subject_objects(old_owner)):
        if not isinstance(o, Literal):
            continue
        name = str(o)
        if name not in agents:
            node = URIRef(f"{base}agent-{slug(name)}")
            graph.add((node, RDF_TYPE, agent_cls))
            graph.add((node, TITLE, Literal(name)))
            graph.add((node, URIRef(SKOS + "prefLabel"), Literal(name)))
            agents[name] = node
        graph.remove((s_, old_owner, o))
        graph.add((s_, old_owner, agents[name]))
    if agents:
        print(f"minted {len(agents)} agent(s) from specl:owner literals")

    hashed = sorted(
        str(n) for n in graph.all_nodes()
        if isinstance(n, URIRef)
        and re.search(r"#(designnote|comment)-[0-9a-f]{8}$", str(n))
    )

    conforms = URIRef(DCT + "conformsTo")
    for s_, o in list(graph.subject_objects(conforms)):
        if str(o).endswith("/contract/1"):
            graph.remove((s_, conforms, o))
            graph.add((s_, conforms, URIRef("https://w3id.org/specl/contract/2")))

    target.write_text(graph.serialize(format="turtle"), encoding="utf-8")
    print(f"wrote {target} ({renamed} propert(y|ies) renamed)")

    if hashed:
        print(
            f"warning: {len(hashed)} content-hash IRI(s) remain. Contract 2 "
            "requires DN and C identifiers, and the old IRI was a function of "
            "the prose, so nothing in the graph says what it should become. "
            "Add identifiers in the markdown and regenerate:",
            file=sys.stderr,
        )
        for n in hashed:
            print(f"  {n}", file=sys.stderr)
        return 3
    return 0


# Annotation keys renamed in contract 2. The graph migration handles Turtle; a
# project that still has its markdown was told regenerating is the better path,
# and then given nothing to migrate the markdown with.
SOURCE_RENAMES = {"asA": "role", "iWant": "capability", "soThat": "benefit"}


def cmd_source(args) -> int:
    """Rewrite a pre-0.11 specification's markdown for contract 2.

    Renames what can be renamed mechanically and reports what cannot. The rest
    needs a judgement the tool does not have: an owner becomes a declared agent,
    and a design note or comment needs an identifier chosen by whoever knows
    what the note is about. Inventing either would produce a specification that
    parses and misdescribes itself.
    """
    source = Path(args.src)
    text = source.read_text(encoding="utf-8")
    renamed = {}
    for old, new in SOURCE_RENAMES.items():
        pattern = re.compile(rf"^(\s+- ){old}(\s*:)", re.M)
        text, count = pattern.subn(rf"\g<1>{new}\g<2>", text)
        if count:
            renamed[old] = count

    manual = []
    # role and owner both take identifiers in contract 2. Renaming asA to role
    # turns a value that worked into one that warns, so the report says which
    # values need declaring rather than leaving it to be discovered.
    for key, section_heading, prefix, what in (
        ("role", "Personas", "P", "persona"),
        ("owner", "Agents", "AG", "agent"),
    ):
        names = sorted({
            m.group(1).strip()
            for m in re.finditer(rf"^\s+- {key}\s*:\s*(.+)$", text, re.M)
            if not BULLET_RE.match(f"- {m.group(1).strip()} x")
        })
        if names:
            manual.append(
                f"{len(names)} {key} value(s) name {'an' if what[0] in 'aeiou' else 'a'} {what} rather than "
                f"referencing one: {', '.join(repr(n) for n in names)}. Add a "
                f"'# {section_heading}' section with a {prefix}-prefixed item "
                f"for each and point {key} at the identifier. Referencing by "
                "name would make two spellings two nodes, which is why the "
                "value is an identifier."
            )

    for heading, prefix in (("Design Considerations", "DN"), ("Comments", "C")):
        section = re.search(rf"^# {heading}\s*$(.*?)(?=^# |\Z)", text, re.M | re.S)
        if not section:
            continue
        bare = [
            line for line in section.group(1).splitlines()
            if line.startswith("- ") and not BULLET_RE.match(line)
        ]
        if bare:
            manual.append(
                f"{len(bare)} bullet(s) under '{heading}' have no identifier. "
                f"Contract 2 requires {prefix} identifiers there, and the right "
                "numbering is yours to choose."
            )

    if args.dry_run:
        print(f"{source}: would rename {sum(renamed.values())} annotation(s)")
    else:
        Path(args.dst).write_text(text, encoding="utf-8")
        print(f"wrote {args.dst} ({sum(renamed.values())} annotation(s) renamed)")
    for old, count in sorted(renamed.items()):
        print(f"  {old} -> {SOURCE_RENAMES[old]}  ({count})")

    if manual:
        print("\nNot done automatically, because the choice is not the tool's:",
              file=sys.stderr)
        for note in manual:
            print(f"  - {note}", file=sys.stderr)
        return 3
    return 0


def cmd_iris(args) -> int:
    source, target = Path(args.src), Path(args.dst)
    if source.resolve() == target.resolve():
        print("error: refusing to overwrite the input graph", file=sys.stderr)
        return 2
    try:
        base = check_base(args.spec_base)
    except SpecError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    graph = Graph().parse(source)
    found = legacy_nodes(graph)
    if not found:
        print(f"{source}: no IRIs under {LEGACY_SPEC_BASE}; nothing to migrate")
        return 0

    try:
        mapping = build_mapping(graph, base)
    except SpecError as exc:
        print(f"error: {source}: {exc}", file=sys.stderr)
        return 2

    if args.dry_run:
        for old in sorted(mapping, key=str):
            print(f"  {old}\n  -> {mapping[old]}")
        print(f"{len(mapping)} IRIs would move")
        return 0

    rewritten = rewrite(graph, mapping)

    # The old Specification IRI's local name was the spec_id, and 0.3.0 keeps
    # that value as dct:identifier. Recovering it here means the migrated graph
    # carries what regenerating would have carried.
    specification = URIRef(base[:-1])
    old_local = str(next(iter(mapping))).split("#")[-1]
    for old, new in mapping.items():
        if new == specification:
            old_local = str(old)[len(LEGACY_SPEC_BASE):]
    if rewritten.value(specification, IDENTIFIER) is None and old_local:
        rewritten.add((specification, IDENTIFIER, Literal(old_local)))

    warnings: list[str] = []
    convert_references(rewritten, base, warnings)
    titled = add_missing_titles(rewritten, base)
    rewritten.add((specification, CONFORMS_TO, URIRef(CONTRACT)))
    rewritten.bind("spec", base)
    target.write_text(rewritten.serialize(format="turtle"), encoding="utf-8")

    print(
        f"wrote {target} ({len(mapping)} IRIs moved onto {base}, "
        f"{titled} titles derived)"
    )
    for w in warnings:
        print(f"warning: {w}", file=sys.stderr)
    print(
        "note: nested content and the prefix key cannot be recovered from "
        "Turtle, because nothing emitted them before 0.3.0. Regenerating from "
        "the markdown is the better path wherever the markdown exists.",
        file=sys.stderr,
    )
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(prog="specl-migrate")
    sub = ap.add_subparsers(dest="command", required=True)
    iris = sub.add_parser("iris", help="rewrite pre-0.3.0 IRIs onto a declared base")
    iris.add_argument("src")
    iris.add_argument("dst")
    iris.add_argument(
        "--spec-base",
        required=True,
        help="the specification's spec_base, ending in '#'. Required: the tool "
             "cannot infer which specification a shared-namespace graph came "
             "from, and the value becomes a permanent identifier.",
    )
    iris.add_argument("--dry-run", action="store_true", help="report the mapping only")
    iris.set_defaults(func=cmd_iris)

    src = sub.add_parser(
        "source", help="rewrite a pre-0.11 specification's markdown for contract 2"
    )
    src.add_argument("src")
    src.add_argument("dst", nargs="?", default=None)
    src.add_argument("--dry-run", action="store_true")
    src.set_defaults(func=cmd_source)

    contract = sub.add_parser(
        "contract", help="move a contract 1 graph to contract 2"
    )
    contract.add_argument("src")
    contract.add_argument("dst")
    contract.set_defaults(func=cmd_contract)
    args = ap.parse_args()
    if getattr(args, "dst", None) is None and args.command == "source" and not args.dry_run:
        ap.error("source requires a destination path, or --dry-run")
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
