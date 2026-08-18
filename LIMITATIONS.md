# Known limitations

What specl does not do, collected in one place so that adopting it is a decision
made with the costs visible rather than discovered afterwards. Everything here
is recorded in `docs/ROADMAP.md` with more reasoning; this is the version to
read before deciding.

## One entity across several specifications becomes several nodes

`constrains` and `verifiedBy` mint a node under the referencing specification's own base when given a bare name, so three specifications naming `engine` produce three unrelated nodes. This is not a spelling problem: it happens when everyone spells it identically.

**There is a way to share one.** Write the absolute IRI, and every specification naming it names the same node. The verbosity is the cost, and the front-matter abbreviation for it is 2.0 work. Personas and agents were never affected: `role:` and `owner:` resolve a `PREFIX:ID` token against a base declared under `references:`, so declaring one in a parent specification and referencing it from peers already gives one node per entity.

Visible in specl's own repository, where `specl_tool` declares
`component-explorer` while `specl_explorer` is that component with its own
Specification IRI, and nothing in the graph relates them.

Deferred to 2.0 and expected to break things: the likely fix moves every
component IRI a project has. **If you are running a multi-specification program,
this is the limitation most likely to matter to you, and the 2.0 window is where
to raise it.**

## Validation needs a SHACL processor with Advanced Features

The shapes use SPARQL-based targets and constraints, which the SHACL
specification makes optional. `specl-validate` bundles a processor that has them
and refuses to run rather than report a clean result it cannot stand behind.

A processor without them does not error. It reports almost nothing and calls the
graph conforming. If you validate inside an existing pipeline with a different
engine, run `specl-validate conformance --export` and check yours against the
fixture before trusting a green result.

## The contract pins an interface, not bytes

`owl:versionIRI` names the graph contract, and a contract 1 or 2 document gains
classes and properties across releases. What it may not do is move an IRI or
change a property's range. If you need byte stability, vendor a copy.

## An owner is a literal

`specl:owner` is declared a datatype property. Every other reference-valued
property resolves to an IRI; this one holds a name, joinable only by string
equality. Fixing it is a range change and both pre-1.0 breaking releases are
spent, so it waits for 2.0.

## Some things the format cannot express

A `constrains` value containing a parenthesised list splits on the commas inside
the parentheses, producing fragments. Seen in a real specification.

There is no relation for a file as distinct from a software component or a
vocabulary term. Projects use `constrains` for all three.

Nested content under an item is an ordered list of strings and nothing richer.

## Provenance is recorded, not verified

Each item names the file and line it came from. `verifiedBy` names a test, and
nothing checks that the test still exercises what the requirement says, or that
the implementation behind it is unchanged. A verification claim here means a
name resolves.

## Prefixed tokens do not resolve without declaration

A `PREFIX:ID` reference resolves only through `references:` or `vocabularies:` in
the referencing specification's own front matter. There is no registry and none
is planned, so two specifications may use the same prefix for different things.

## Labels carry no language tags

`rdfs:label`, `skos:prefLabel`, and `skos:altLabel` are emitted as plain
literals. SKOS expects at most one `prefLabel` per language and nothing enforces
either the tagging or the cardinality. specl does not know what language a
specification is written in and will not guess.

## Scale is untested

The largest specification specl has translated is roughly 750 lines and 120
items. Nothing is known about behaviour at ten times that, and validation is
SHACL over an in-memory graph, so expect it to be the first thing that hurts.

## It has one author

specl has been written and reviewed by one person. From 1.0 the specification
does not change without consensus, which is a commitment about the future rather
than evidence about the past. `GOVERNANCE.md` is how that commitment is kept and
`docs/proposals/OPEN.md` is where you check what is pending.
