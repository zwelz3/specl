"""Produce the stage 0 fixture set.

Generated fixtures are translator output and may be regenerated at any time.
Hand-authored fixtures are deliberately NOT translator output; each carries a
comment saying so, because the condition under test is one the translator
cannot produce. Regenerating them deletes the test.
"""
import os
import shutil
import subprocess
import sys
import tempfile
import textwrap

OUT = os.path.dirname(os.path.abspath(__file__))
os.makedirs(OUT, exist_ok=True)

FM = """---
spec_base: https://w3id.org/specl/fixtures/{slug}#
prefix: FX
spec_id: fixture-{slug}
title: Fixture {slug}
version: 0.0.1
status: draft
---

<!--specl
created: 2026-08-30
-->

# Intent
Fixture exercising: {intent}

# Purpose
Stage 0 fixture for the explorer harness. See explorer/fixtures/README.md.
"""


def generated(slug, intent, body):
    src = FM.format(slug=slug, intent=intent) + "\n" + textwrap.dedent(body)
    md = os.path.join(OUT, f"{slug}.md")
    ttl = os.path.join(OUT, f"{slug}.ttl")
    open(md, "w").write(src)
    r = subprocess.run(["specl-translate", md, ttl], capture_output=True, text=True)
    print(f"{slug:24s} {r.stdout.strip()}")
    os.remove(md)


def hand(slug, why, ttl):
    header = (f"# HAND-AUTHORED FIXTURE. Not translator output and must not be regenerated.\n"
              f"# Condition under test: {why}\n")
    open(os.path.join(OUT, f"{slug}.ttl"), "w").write(header + textwrap.dedent(ttl))
    print(f"{slug:24s} hand-authored")


PREFIXES = """\
@prefix specl: <https://w3id.org/specl/ns#> .
@prefix spec: <https://w3id.org/specl/fixtures/{slug}#> .
@prefix dct:  <http://purl.org/dc/terms/> .
@prefix xsd:  <http://www.w3.org/2001/XMLSchema#> .
@prefix skos: <http://www.w3.org/2004/02/skos/core#> .

<https://w3id.org/specl/fixtures/{slug}> a specl:Specification ;
    dct:conformsTo <https://w3id.org/specl/contract/{contract}> ;
    dct:title "Fixture {slug}" ;
    dct:hasVersion "0.0.1" ;
    specl:status "draft" ;
    specl:intent \"\"\"Hand-authored fixture.\"\"\" ;
    specl:purpose \"\"\"Stage 0.\"\"\" .
"""


def pre(slug, contract=2):
    return PREFIXES.format(slug=slug, contract=contract)


# ---- Generated -------------------------------------------------------------

generated("repeated-predicates", "R2.6, three values on one predicate", """
# Requirements
- R1 The thing must do three things.
  - priority: MUST
  - acceptance: Given A, when B, then C.
  - acceptance: Given D, when E, then F.
  - acceptance: Given G, when H, then I.
""")

generated("detail-list", "R2.7, sub-bullets producing an rdf:List", """
# Requirements
- R1 Fields must render in order:
    - description
    - priority
    - acceptance
    - verified by
- R2 A plain requirement with no detail.
""")

generated("unresolvable-reference", "R6.6, a reference resolving to nothing in the graph", """
# Requirements
- R1 Must be verified by something that is not in this graph.
  - priority: MUST
  - verifiedBy: https://example.org/tests/nothing-here
- R2 Must be verified by R1, which is in this graph.
  - priority: MUST
  - verifiedBy: R1
""")

generated("alt-labels", "R4.5, a persona whose skos:altLabel differs from its title", """
# Personas
- P1. Someone who reads specifications for a living.
  - title: Reviewer
  - prefLabel: Reviewer
  - altLabel: Auditor
  - altLabel: Assessor

# User Stories
- US1 As a reviewer I want to find things, so that I can read them.
  - role: P1
""")

generated("zero-requirements", "R5.5, a specification with no requirements", """
# User Stories
- US1 As a reader I want a story, so that the population for the figure is empty.
""")

generated("no-items", "R9.3, a specification with no items at all", "")

# 500 items for R10.1.
big = ["# Requirements"]
for i in range(1, 501):
    big.append(f"- R{i} Requirement number {i} exists so that the file has five hundred items.")
    big.append("  - priority: SHOULD")
generated("five-hundred-items", "R10.1, 500 items", "\n".join(big) + "\n")

# ---- Hand-authored ---------------------------------------------------------

hand("local-name-collision", "R2.8, two terms from different namespaces sharing a local name",
     pre("local-name-collision") + """
@prefix ex: <https://example.org/vocab#> .

spec:R1 a specl:Requirement ;
    specl:partOf <https://w3id.org/specl/fixtures/local-name-collision> ;
    dct:title "Title from Dublin Core" ;
    ex:title "Title from the example vocabulary" ;
    dct:description "Carries dct:title and ex:title, which share a local name." .
""")

hand("unrecognised-class", "R2.9, a class the explorer does not represent",
     pre("unrecognised-class") + """
spec:R1 a specl:Requirement ;
    specl:partOf <https://w3id.org/specl/fixtures/unrecognised-class> ;
    dct:title "An ordinary requirement" ;
    dct:description "Present so the file is not empty." .

spec:W1 a specl:Widget ;
    specl:partOf <https://w3id.org/specl/fixtures/unrecognised-class> ;
    dct:title "A widget" ;
    dct:description "specl:Widget is not a class the explorer represents." .
""")

hand("malformed-statement", "R2.4, a malformed statement among valid ones",
     pre("malformed-statement") + """
spec:R1 a specl:Requirement ;
    specl:partOf <https://w3id.org/specl/fixtures/malformed-statement> ;
    dct:title "Before the damage" ;
    dct:description "Loads." .

spec:R2 a specl:Requirement
    dct:title "Missing the semicolon after the class and ending with garbage
    this is not turtle ;;; .

spec:R3 a specl:Requirement ;
    specl:partOf <https://w3id.org/specl/fixtures/malformed-statement> ;
    dct:title "After the damage" ;
    dct:description "Also loads." .
""")

hand("future-contract", "R2.10, a contract version the explorer does not implement",
     pre("future-contract", contract=99) + """
spec:R1 a specl:Requirement ;
    specl:partOf <https://w3id.org/specl/fixtures/future-contract> ;
    dct:title "Declared under contract 99" ;
    dct:description "The explorer implements contract 2." .
""")

hand("no-title", "R4.2, an item carrying no dct:title",
     pre("no-title") + """
spec:R1 a specl:Requirement ;
    specl:partOf <https://w3id.org/specl/fixtures/no-title> ;
    dct:description "This requirement has a description and no title, so the row falls back to a preview." .
""")

hand("no-specification", "R9.2, a file with no specl:Specification individual",
     """\
@prefix specl: <https://w3id.org/specl/ns#> .
@prefix spec: <https://w3id.org/specl/fixtures/no-specification#> .
@prefix dct:  <http://purl.org/dc/terms/> .

spec:R1 a specl:Requirement ;
    dct:title "An orphan" ;
    dct:description "There is no specification individual in this file." .
""")

readme = """# Stage 0 fixtures

Each file exercises one condition the explorer must handle. Files whose first
line says HAND-AUTHORED are not translator output and must not be regenerated;
the condition they test is one the translator cannot produce.

| Fixture | Requirement | Source |
| --- | --- | --- |
| repeated-predicates | R2.6 | Generated |
| detail-list | R2.7 | Generated |
| local-name-collision | R2.8 | Hand-authored |
| unrecognised-class | R2.9 | Hand-authored |
| malformed-statement | R2.4 | Hand-authored |
| future-contract | R2.10 | Hand-authored |
| unresolvable-reference | R6.6 | Generated |
| alt-labels | R4.5 | Generated |
| no-title | R4.2 | Hand-authored |
| zero-requirements | R5.5 | Generated |
| no-items | R9.3 | Generated |
| no-specification | R9.2 | Hand-authored |
| five-hundred-items | R10.1 | Generated |

Regenerate the generated set with `python3 make_fixtures.py` from a checkout
with specl installed. The harness (`../test/run.mjs`) needs nothing but Node.
"""
open(os.path.join(OUT, "README.md"), "w").write(readme)
print("README written")


# ---- The explorer's own specification, as a fixture ------------------------
# `python3 make_fixtures.py --spec path/to/spec.md`. Translated from a copy
# named spec.md so the emitted source-document identifier is the real one.
if "--spec" in sys.argv:
    src = sys.argv[sys.argv.index("--spec") + 1]
    with tempfile.TemporaryDirectory() as d:
        tmp = os.path.join(d, "spec.md")
        shutil.copy(src, tmp)
        r = subprocess.run(["specl-translate", tmp, os.path.join(OUT, "explorer-spec.ttl")], capture_output=True, text=True)
        print(f"{'explorer-spec':24s} {r.stdout.strip()}")
