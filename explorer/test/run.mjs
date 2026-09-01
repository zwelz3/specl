// Explorer harness. Plain Node, no dependencies.
//   node test/run.mjs            run fixtures against explorer.html
//   node test/run.mjs --before   also run the shipped 1.0.0 parser and record its failures
import { readFileSync, readdirSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';
import assert from 'node:assert/strict';
import vm from 'node:vm';

const here = dirname(fileURLToPath(import.meta.url));
const root = join(here, '..');
const fx = (name) => readFileSync(join(root, 'fixtures', name + '.ttl'), 'utf8');

function scriptOf(html) {
  const m = html.match(/<script>([\s\S]*?)<\/script>\s*<\/body>/);
  if (!m) throw new Error('no trailing <script> in html');
  return m[1];
}

// The rewrite: pure functions, no DOM needed.
function loadNew() {
  const ctx = { console };
  vm.runInNewContext(scriptOf(readFileSync(join(root, 'explorer.html'), 'utf8')), ctx);
  return ctx;
}

// The shipped 1.0.0 parser, for the before-state. Its script touches the DOM
// at top level, so give it a stub that swallows everything.
function loadOld(path) {
  const el = () => ({ onchange: null, oninput: null, onclick: null, style: {}, classList: { add() {}, remove() {} }, textContent: '', innerHTML: '' });
  const ctx = { console, document: { getElementById: el, querySelectorAll: () => [] }, window: { addEventListener() {} } };
  vm.runInNewContext(scriptOf(readFileSync(path, 'utf8')), ctx);
  return ctx;
}

const NS = { specl: 'https://w3id.org/specl/ns#', dct: 'http://purl.org/dc/terms/', skos: 'http://www.w3.org/2004/02/skos/core#' };
const item = (m, id) => m.items.find((i) => i.id === id);
const plain = (x) => JSON.parse(JSON.stringify(x)); // values cross a vm realm; compare by structure
const vals = (it, p) => plain((it.props[p] || []).map((v) => v.value));

// ---- Expectations on the rewrite ---------------------------------------
const CASES = {
  'repeated-predicates': (m) => {
    assert.equal(vals(item(m, 'R1'), NS.specl + 'acceptanceCriterion').length, 3, 'R2.6: three criteria retained');
  },
  'detail-list': (m) => {
    assert.deepEqual(plain(item(m, 'R1').details), ['description', 'priority', 'acceptance', 'verified by'], 'R2.7: list in order');
    assert.equal(item(m, 'R2').details.length, 0);
    assert.equal(m.report.filter((r) => r.kind === 'orphan-list-cell').length, 0, 'cells consumed by their owner');
  },
  'local-name-collision': (m) => {
    const r = item(m, 'R1');
    assert.equal(vals(r, NS.dct + 'title')[0], 'Title from Dublin Core', 'R2.8: dct:title kept');
    assert.equal(vals(r, 'https://example.org/vocab#title')[0], 'Title from the example vocabulary', 'R2.8: ex:title kept');
  },
  'unrecognised-class': (m) => {
    assert.ok(item(m, 'R1'), 'ordinary item present');
    assert.equal(m.items.length, 1, 'widget not listed as an item');
    const rep = m.report.filter((r) => r.kind === 'unrepresented-class');
    assert.equal(rep.length, 1, 'R2.9: one unrepresented class reported');
    assert.ok(rep[0].subject.endsWith('#W1') && rep[0].detail === 'Widget');
  },
  'malformed-statement': (m) => {
    assert.ok(item(m, 'R1') && item(m, 'R3'), 'R2.4: statements either side of the damage load');
    const rep = m.report.filter((r) => r.kind === 'malformed-statement');
    assert.equal(rep.length, 1, 'one malformed statement reported');
    assert.ok(rep[0].subject.endsWith('#R2'), 'and it is named');
  },
  'future-contract': (m) => {
    assert.equal(m.contract, 'https://w3id.org/specl/contract/99');
    assert.equal(m.contractKnown, false, 'R2.10: unknown contract flagged');
    assert.ok(m.report.some((r) => r.kind === 'unknown-contract'));
  },
  'unresolvable-reference': (m) => {
    const vb = NS.specl + 'verifiedBy';
    const r1 = vals(item(m, 'R1'), vb)[0], r2 = vals(item(m, 'R2'), vb)[0];
    assert.equal(m.index.isResolvable(r1), false, 'R6.6: external test IRI does not resolve');
    assert.equal(m.index.isResolvable(r2), true, 'R6.6: local reference resolves');
    assert.equal(m.index.resolve(r2).id, 'R1');
    assert.equal(m.index.referrers(r2).length, 1, 'R6.7: backlink recorded');
  },
  'alt-labels': (m, ctx) => {
    const p = item(m, 'P1');
    assert.deepEqual(vals(p, NS.skos + 'altLabel').sort(), ['Assessor', 'Auditor']);
    assert.deepEqual(plain(ctx.skosLabels(p)).sort(), ['Assessor', 'Auditor', 'Reviewer'], 'R4.5: every SKOS label available to the filter');
  },
  'no-title': (m, ctx) => {
    const r = item(m, 'R1');
    assert.equal(vals(r, NS.dct + 'title').length, 0);
    assert.ok(ctx.labelOf(r).startsWith('This requirement has a description'), 'R4.2: preview fallback');
  },
  'zero-requirements': (m) => {
    assert.ok(m.spec);
    assert.equal(m.items.filter((i) => i.cls === 'Requirement').length, 0, 'R5.5: empty population');
  },
  'no-items': (m) => {
    assert.ok(m.spec, 'R9.3: specification still present');
    assert.equal(m.items.length, 0);
  },
  'no-specification': (m) => {
    assert.equal(m.spec, null);
    assert.ok(m.report.some((r) => r.kind === 'no-specification'), 'R9.2: reported, not thrown');
  },
  'five-hundred-items': (m, ctx, ms) => {
    assert.equal(m.items.filter((i) => i.cls === 'Requirement').length, 500);
    assert.ok(ms < 200, `R10.1: parse in ${ms.toFixed(1)} ms (budget is 200 ms for first paint, parse must be well inside it)`);
  },
};

// ---- Before-state: what the shipped parser gets wrong -------------------
const BEFORE = {
  'repeated-predicates': (o) => o.items.find((i) => i.id === 'R1').props.acceptanceCriterion.startsWith('Given G') ? 'FAIL keeps only the last of three criteria' : 'ok',
  'detail-list': (o) => o.items.find((i) => i.id === 'R1').props.detail && !('description' in o) ? 'FAIL detail is a dangling pointer; sub-bullets dropped' : 'ok',
  'local-name-collision': (o) => o.items.find((i) => i.id === 'R1').props.title === 'Title from the example vocabulary' ? 'FAIL ex:title silently overwrote dct:title' : 'ok',
  'unrecognised-class': (o) => o.items.length === 2 ? 'FAIL widget counted as an item, cannot be listed' : 'ok',
  'malformed-statement': (o) => o.items.map((i) => i.id).join(',') !== 'R1,R3' ? `FAIL parsed ${o.items.map((i) => i.id).join(',')}; damage not isolated or not reported` : 'ok (skipped silently to console)',
  'future-contract': (o) => 'FAIL contract not read',
  'unresolvable-reference': (o) => 'FAIL reference rendered as text; no resolution',
  'alt-labels': (o) => 'FAIL altLabel collapsed to last value; not filterable',
  'no-title': (o) => 'ok (never used title anyway)',
  'zero-requirements': (o) => 'ok',
  'no-items': (o) => o.items.length === 1 ? 'FAIL SourceDocument counted as an item' : 'ok',
  'no-specification': (o) => o.spec === null ? 'ok' : 'FAIL',
  'five-hundred-items': (o) => o.items.length === 501 ? 'FAIL SourceDocument counted; 501 reported' : 'ok',
};

// ---- View model (stages 3 to 6) ------------------------------------------
const VIEW = {
  'R4.7 pinned specification row, exempt from filter': (c) => {
    const m = c.parse(fx('explorer-spec'));
    const g = plain(c.sidebarRows(m, '', null));
    assert.equal(g[0].group, 'Specification'); assert.ok(g[0].pinned); assert.equal(g[0].rows[0].id, 'spec');
    const f = plain(c.sidebarRows(m, 'zzzzqqq', null));
    assert.equal(f.length, 1, 'only the pinned group survives a filter matching nothing');
  },
  'R4.1 R4.4 groups with counts, natural order': (c) => {
    const m = c.parse(fx('five-hundred-items'));
    const g = plain(c.sidebarRows(m, '', null)).find((x) => x.cls === 'Requirement');
    assert.equal(g.count, 500);
    const ids = g.rows.map((r) => r.id);
    assert.ok(ids.indexOf('R2') < ids.indexOf('R10') && ids.indexOf('R10') < ids.indexOf('R100'), 'R2 < R10 < R100');
  },
  'R4.8 R4.2 label is the title, preview only without one': (c) => {
    const m = c.parse(fx('explorer-spec'));
    const row = plain(c.sidebarRows(m, 'R2.6', null))[1].rows[0];
    assert.ok(row.label.startsWith('A predicate appearing more than once') && row.label.endsWith('\u2026'), 'title, as derived by the translator');
    const m2 = c.parse(fx('no-title'));
    assert.ok(plain(c.sidebarRows(m2, '', null))[1].rows[0].label.startsWith('This requirement has a description'));
  },
  'R4.5 filter matches SKOS labels and says so': (c) => {
    const m = c.parse(fx('alt-labels'));
    const hit = plain(c.sidebarRows(m, 'auditor', null)).find((g) => g.cls === 'Persona');
    assert.ok(hit && hit.rows.length === 1, 'P1 listed for its altLabel');
    assert.equal(hit.rows[0].match, 'label:alt'); assert.equal(hit.rows[0].matchText, 'Auditor');
    const vis = plain(c.sidebarRows(m, 'reviewer', null)).find((g) => g.cls === 'Persona');
    assert.equal(vis.rows[0].match, 'label', 'a match on the displayed label needs no explanation');
    const desc = plain(c.sidebarRows(m, 'for a living', null)).find((g) => g.cls === 'Persona');
    assert.equal(desc.rows[0].match, 'description'); assert.ok(desc.rows[0].matchText.includes('for a living'));
  },
  'R6.2 R6.3 class order, then the rest, absent-but-expected marked': (c) => {
    const m = c.parse(fx('five-hundred-items'));
    const rows = plain(c.detailRows(m, item(m, 'R1')));
    assert.deepEqual(rows.slice(0, 3).map((r) => r.key), ['description', 'priority', 'acceptanceCriterion']);
    const acc = rows.find((r) => r.key === 'acceptanceCriterion');
    assert.ok(acc.absent && acc.expected, 'acceptance criterion shown as expected and absent');
    assert.ok(!rows.find((r) => r.key === 'rationale'), 'rationale is neither present nor expected, so no row');
    const spec = plain(c.detailRows(m, m.spec));
    assert.ok(spec.map((r) => r.key).indexOf('intent') < spec.map((r) => r.key).indexOf('conformsTo'));
  },
  'R6.6 references resolve or are marked': (c) => {
    const m = c.parse(fx('unresolvable-reference'));
    const r1 = plain(c.detailRows(m, item(m, 'R1'))).find((r) => r.key === 'verifiedBy').values[0];
    const r2 = plain(c.detailRows(m, item(m, 'R2'))).find((r) => r.key === 'verifiedBy').values[0];
    assert.equal(r1.kind, 'ref'); assert.equal(r1.resolvable, false);
    assert.equal(r2.resolvable, true); assert.equal(r2.id, 'R1'); assert.ok(r2.isItem);
  },
  'R6.7 backlinks grouped by predicate': (c) => {
    const m = c.parse(fx('unresolvable-reference'));
    const bl = plain(c.backlinks(m, item(m, 'R1')));
    assert.equal(bl.length, 1); assert.equal(bl[0].key, 'verifiedBy'); assert.equal(bl[0].items[0].id, 'R2');
    const m2 = c.parse(fx('explorer-spec'));
    const d = plain(c.backlinks(m2, item(m2, 'R3.3')));
    assert.ok(d.find((g) => g.key === 'affects' && g.items.some((x) => x.id === 'D1')), 'D1 affects R3.3');
  },
  'R6.8 provenance names document and line': (c) => {
    const m = c.parse(fx('explorer-spec'));
    const p = plain(c.provenanceOf(m, item(m, 'R6.2')));
    assert.equal(p.document, 'spec.md'); assert.ok(/^\d+$/.test(p.line)); assert.ok(p.resolvable);
  },
  'R7.1 R7.6 raw block includes owned list cells; whole file is the file': (c) => {
    const m = c.parse(fx('detail-list'));
    const b1 = c.rawBlock(m, item(m, 'R1'), false), b2 = c.rawBlock(m, item(m, 'R2'), false);
    assert.ok(b1.includes('spec:R1 a specl:Requirement') && b1.includes('rdf:first "description"'), 'R1 block carries its cells');
    assert.ok(!b2.includes('rdf:first'), 'R2 block has none');
    assert.equal(c.rawBlock(m, item(m, 'R1'), true), m.raw);
  },
  'R7.7 line numbers are the file\u2019s, and gaps are marked': (c) => {
    const m = c.parse(fx('explorer-spec'));
    const raw = m.raw.split('\n');
    const L = plain(c.rawLines(m, item(m, 'R6.2'), false));
    assert.ok(L.length > 1);
    const unesc = (h) => h.replace(/<[^>]*>/g, '').replace(/&lt;/g, '<').replace(/&gt;/g, '>')
      .replace(/&quot;/g, '"').replace(/&#39;/g, "'").replace(/&amp;/g, '&');
    L.filter((x) => !x.gap).forEach((x) => assert.equal(unesc(x.html), raw[x.n - 1], `line ${x.n} matches the file`));
    assert.ok(L.some((x) => x.gap), 'the break between the statement and its list cells is marked');
    const W = plain(c.rawLines(m, null, true));
    assert.equal(W.length, raw.length);
    assert.equal(W[0].n, 1);
    assert.equal(W[W.length - 1].n, raw.length);
    assert.equal(W.filter((x) => x.gap).length, 0, 'the whole file has no gaps');
  },
  'R7.3 a token spanning a newline does not straddle two lines': (c) => {
    const q = '"'.repeat(3);
    const L = plain(c.highlightLines('a:b ' + q + 'one\ntwo' + q + ' ;\nc:d "x" .'));
    assert.equal(L.length, 3);
    L.forEach((h) => assert.equal((h.match(/<span/g) || []).length, (h.match(/<[/]span>/g) || []).length, 'balanced on every line'));
    assert.ok(L[0].includes('one') && L[1].includes('two'));
  },
  'R6.1 the heading is the class and the identifier': (c) => {
    const m = c.parse(fx('explorer-spec'));
    assert.equal(c.headingOf(item(m, 'R6.2')), 'Requirement R6.2');
    assert.equal(c.headingOf(m.spec), 'Specification', 'the specification is not "Specification spec"');
    assert.ok(!plain(c.detailRows(m, item(m, 'R6.2'), grammar)).some((r) => r.key === 'title'),
      'a title the description already shows is not repeated as a row');
    assert.ok(plain(c.detailRows(m, m.items.find((x) => x.cls === 'Persona'), grammar)).some((r) => r.key === 'title'),
      'a title that is not a truncation is shown');
  },
  'R7.3 highlighting distinguishes token kinds': (c) => {
    const h = c.highlight('@prefix dct: <http://purl.org/dc/terms/> .\nspec:R1 a specl:Requirement ;\n    dct:title "T" . # done\n');
    for (const cls of ['k', 'i', 'p', 's', 'c']) assert.ok(h.includes(`class="${cls}"`), 'token class ' + cls);
  },
  'R8 counts exclude nodes that are not items': (c) => {
    assert.equal(plain(c.specCounts(c.parse(fx('no-items')))).total, 0);
    assert.equal(plain(c.specCounts(c.parse(fx('five-hundred-items')))).total, 500);
  },
  'R11.1 fragment round-trips selection, tab and whole-file': (c) => {
    const m = c.parse(fx('explorer-spec'));
    for (const [id, tab, whole] of [['R1.1', 'detail', false], ['R6.2', 'ttl', false], ['spec', 'ttl', true]]) {
      const d = plain(c.decodeHash(c.encodeHash(id, tab, whole)));
      assert.deepEqual([d.id, d.tab, d.whole], [id, tab, whole]);
      assert.ok(c.findById(m, id), 'resolves against the model');
    }
  },
};

// ---- Stages 7 to 10 ---------------------------------------------------------
// Generated inputs. On a fresh checkout these do not exist yet; say what to run
// rather than dying on a stack trace.
function generated(rel, how) {
  try { return JSON.parse(readFileSync(join(root, ...rel), 'utf8')); }
  catch { missing.push(`${rel.join('/')}  ->  ${how}`); return null; }
}
const missing = [];
const grammar = generated(['build', 'grammar.json'], 'python3 build/grammar.py > build/grammar.json');
const report = generated(['fixtures', 'explorer-spec.report.json'], 'specl-validate validate fixtures/explorer-spec.ttl --json fixtures/explorer-spec.report.json');
try { readFileSync(join(root, 'fixtures', 'explorer-spec.ttl')); }
catch { missing.push('fixtures/explorer-spec.ttl  ->  python3 fixtures/make_fixtures.py --spec ../specs/specl_explorer/spec.md'); }
if (missing.length) {
  console.error('Generated inputs are absent. Produce them and run again:\n  ' + missing.join('\n  '));
  console.error('\nThe hand-authored fixtures in fixtures/ are committed and are never regenerated.');
  process.exit(2);
}
const LATER = {
  'R5.6 estimate reproduces specl-validate on the explorer spec (94%, 101/110)': (c) => {
    const m = c.parse(fx('explorer-spec'));
    const e = plain(c.readiness(m, grammar, null, null));
    assert.equal(e.mode, 'estimate'); assert.equal(e.score, 94); assert.equal(e.clean, 101); assert.equal(e.total, 110);
    const f = plain(c.readiness(m, null, null, null));
    assert.equal(f.score, 94, 'the built-in fallback agrees when no grammar is present');
  },
  'R5.6 a supplied report gives the same figure by the same definition': (c) => {
    const m = c.parse(fx('explorer-spec'));
    const r = plain(c.readiness(m, grammar, report, null));
    assert.equal(r.mode, 'report'); assert.equal(r.score, 94); assert.equal(r.clean, 101);
    const est = plain(c.readiness(m, grammar, null, null));
    assert.deepEqual(r.contributors.map((x) => x.item.id), est.contributors.map((x) => x.item.id), 'same unclean set either way');
  },
  'R5.6 a supplied score is displayed as supplied': (c) => {
    const m = c.parse(fx('explorer-spec'));
    const r = plain(c.readiness(m, grammar, null, {score: 42, clean: 3, total: 7, subscores: {}}));
    assert.equal(r.mode, 'supplied'); assert.equal(r.score, 42); assert.equal(r.clean, 3); assert.equal(r.total, 7);
    const g = plain(c.readiness(m, grammar, null, {score: 99, clean: 1, total: 1, gate_failed: true}));
    assert.equal(g.score, null, 'a failed gate reports no figure');
  },
  'R5.7 every mode states its definition': (c) => {
    const m = c.parse(fx('explorer-spec'));
    for (const r of [c.readiness(m, grammar, null, null), c.readiness(m, grammar, report, null), c.readiness(m, null, null, null)]) {
      const d = plain(r.definition);
      for (const k of ['population', 'clean', 'weights', 'figure', 'exclusions', 'mode']) assert.ok(d[k], 'definition has ' + k);
    }
    assert.ok(/^3 retired items excluded$/.test(plain(c.readiness(m, grammar, null, null)).definition.exclusions), 'the withdrawn requirements are named as excluded');
  },
  'R5.9 contributors ordered by weight then id, each with reasons': (c) => {
    const m = c.parse(fx('explorer-spec'));
    const r = plain(c.readiness(m, grammar, null, null));
    for (let i = 1; i < r.contributors.length; i++) assert.ok(r.contributors[i - 1].weight >= r.contributors[i].weight);
    assert.ok(r.contributors.every((x) => x.reasons.length), 'every contributor says why');
    assert.ok(r.contributors.every((x) => x.item.cls === 'OpenIssue' && x.reasons.some((y) => y.key === 'owner')), 'on this spec, the only shortfall is open-issue owners');
  },
  'R5.5 empty population reports no figure': (c) => {
    assert.equal(plain(c.readiness(c.parse(fx('no-items')), grammar, null, null)).score, null);
    const z = plain(c.readiness(c.parse(fx('zero-requirements')), grammar, null, null));
    assert.equal(z.total, 1, 'a story is still in the population');
  },
  'R6.4 an item knows whether it is clean and why': (c) => {
    const m = c.parse(fx('five-hundred-items'));
    const r = c.readiness(m, grammar, null, null);
    const row = r.rows.find((x) => x.item.id === 'R1');
    assert.equal(row.clean, false); assert.ok(plain(row.reasons).some((x) => x.key === 'acceptanceCriterion' && x.why === 'missing'));
    assert.equal(row.weight, 3, 'SHOULD weighs 3');
  },
  'R5.6 conditional expectations follow the graph': (c) => {
    const m = c.parse(fx('unresolvable-reference'));
    const r = c.readiness(m, grammar, null, null);
    // R1 carries verifiedBy; the fixture holds no Test or AcceptanceQuery node, so verifiedBy is not expected of R2.
    const r2 = r.rows.find((x) => x.item.id === 'R2');
    assert.ok(!plain(r2.reasons).some((x) => x.key === 'verifiedBy'), 'verifiedBy not demanded when the graph declares no verification artifact');
  },
  'R12.1 R12.2 findings attach by focus node': (c) => {
    const m = c.parse(fx('explorer-spec'));
    const counts = plain(c.findingCounts(report));
    assert.equal(Object.keys(counts).length, 9);
    const oq1 = item(m, 'OQ1');
    assert.equal(plain(c.findingsFor(report, oq1.iri)).length, 1);
    assert.equal(plain(c.findingsFor(report, item(m, 'R1.1').iri)).length, 0);
    assert.equal(plain(c.findingsFor(null, oq1.iri)).length, 0, 'no report, no findings, no throw');
  },
  'R13.1 R13.2 reference carries the grammar and its provenance': (c) => {
    const ref = plain(c.referenceModel({nodes: {}}, grammar, null));
    assert.equal(ref.specl, '1.0.0'); assert.ok(ref.contract.endsWith('/contract/2')); assert.ok(ref.generated);
    assert.ok(ref.keys.length >= 20 && ref.keys.some((k) => k.key === 'acceptance' && k.property.endsWith('acceptanceCriterion')));
    assert.ok(ref.keys.some((k) => k.key === 'verifiedBy' && k.reference && k.range.endsWith('Test')));
    assert.ok(ref.sections.some((s) => s.heading === 'Requirements' && s.prefixes[0] === 'R'));
    assert.equal(c.referenceModel({nodes: {}}, null, null), null, 'no grammar, no reference, no invention');
  },
  'R13.3 reference marks what the selected item lacks': (c) => {
    const m = c.parse(fx('five-hundred-items'));
    const ref = plain(c.referenceModel(m, grammar, item(m, 'R1')));
    const req = ref.classes.find((x) => x.cls === 'Requirement');
    assert.ok(req.selected);
    const acc = req.expects.find((e) => e.key === 'acceptanceCriterion'), pri = req.expects.find((e) => e.key === 'priority');
    assert.equal(acc.present, false); assert.equal(pri.present, true);
    const vb = req.expects.find((e) => e.key === 'verifiedBy'); assert.equal(vb.applies, false, 'conditional expectation shown as not applying');
  },
};

const ctx = loadNew();
let pass = 0, fail = 0;
console.log('== stages 7 to 10 ==');
for (const [name, check] of Object.entries(LATER)) {
  try { check(ctx); console.log(`  ${name.padEnd(76)} pass`); pass++; }
  catch (e) { console.log(`  ${name.padEnd(76)} FAIL  ${e.message.split('\n')[0]}`); fail++; }
}
console.log('\n== view model ==');
for (const [name, check] of Object.entries(VIEW)) {
  try { check(ctx); console.log(`  ${name.padEnd(64)} pass`); pass++; }
  catch (e) { console.log(`  ${name.padEnd(64)} FAIL  ${e.message.split('\n')[0]}`); fail++; }
}
console.log('\n== parser ==');
for (const [name, check] of Object.entries(CASES)) {
  const t0 = performance.now();
  let m;
  try { m = ctx.parse(fx(name)); } catch (e) { console.log(`  ${name.padEnd(24)} THREW ${e.message}`); fail++; continue; }
  const ms = performance.now() - t0;
  try { check(m, ctx, ms); console.log(`  ${name.padEnd(24)} pass  (${ms.toFixed(1)} ms, ${m.report.length} reported)`); pass++; }
  catch (e) { console.log(`  ${name.padEnd(24)} FAIL  ${e.message}`); fail++; }
}
console.log(`${pass} passed, ${fail} failed`);

if (process.argv.includes('--before')) {
  const old = loadOld(join(root, 'test', 'explorer-1.0.0.html'));
  console.log('\n== shipped 1.0.0 parser, before-state ==');
  for (const [name, check] of Object.entries(BEFORE)) {
    let o;
    try { o = old.parse(fx(name)); } catch (e) { console.log(`  ${name.padEnd(24)} THREW ${e.message}`); continue; }
    console.log(`  ${name.padEnd(24)} ${check(o)}`);
  }
}


// ---- Non-functional, what can be checked without a browser ----------------
{
  console.log('\n== non-functional (proxy checks) ==');
  const src = readFileSync(join(root, 'explorer.html'), 'utf8');
  const script = scriptOf(src);
  const css = () => src.match(/<style>([\s\S]*?)<\/style>/)[1];
  const checks = {
    'R10.1 parse + sidebar + detail for 500 items well inside 200 ms': () => {
      const t0 = performance.now();
      const m = ctx.parse(fx('five-hundred-items'));
      ctx.sidebarRows(m, '', null); ctx.detailRows(m, m.spec); ctx.readiness(m, grammar, null, null);
      const ms = performance.now() - t0;
      assert.ok(ms < 200, `${ms.toFixed(0)} ms`); return `${ms.toFixed(0)} ms`;
    },
    'R10.2 R1.1 no external resource, request or navigation in the file': () => {
      for (const bad of [/<link[^>]+href=/i, /<script[^>]+src=/i, /\bfetch\s*\(/, /XMLHttpRequest/, /new\s+WebSocket/, /navigator\.sendBeacon/, /<img[^>]+src=["']?https?:/i, /@import/, /url\(\s*["']?https?:/i]) assert.ok(!bad.test(src), 'found ' + bad);
    },
    'R1.5 no bundler, transpiler or module loader': () => {
      for (const bad of [/\bimport\s+[\w{*]/, /\brequire\s*\(/, /\bexport\s+(default|const|function)/, /type="module"/]) assert.ok(!bad.test(script), 'found ' + bad);
    },
    'R13.5 no markdown interpreter: only the Turtle tokenizer reads text': () => {
      // Regex sources that would read markdown structure: a front-matter fence, a heading, a list bullet.
      for (const bad of [/\/\^---/, /\/\^#\{?1?/, /\/\^\\s\*-\\s/, /\/\^- /, /marked\(|markdownit|remark|js-yaml/i]) assert.ok(!bad.test(script), 'found ' + bad);
      assert.ok(/function tokenize\(/.test(script), 'the Turtle tokenizer is the only thing that reads text');
    },
    'R7.4 highlighting is a function in the file': () => { assert.ok(/function highlight\(/.test(script)); },
    'OQ5 a light theme exists, dark is the default, and both are token blocks': () => {
      assert.ok(/<html lang="en" data-theme="dark">/.test(src), 'dark by default');
      const themed = (css().match(/:root[^{]*\{[^}]*\}/g) || []).filter((b) => /--accent:/.test(b) && /--hl-k:/.test(b));   // the print block redefines the base tokens only
      assert.equal(themed.length, 3, 'dark, light, and auto under prefers-color-scheme');
      const names = (b) => (b.match(/--[a-z-]+:/g) || []).sort().join(',');
      assert.equal(names(themed[0]), names(themed[1]), 'light declares every token dark declares');
      assert.equal(names(themed[0]), names(themed[2]), 'auto declares every token dark declares');
      assert.ok(/color-scheme:dark/.test(themed[0]) && /color-scheme:light/.test(themed[1]), 'each names its scheme so form controls follow');
    },
    'R13.6 withdrawn: the file emits no specl source': () => {
      for (const bad of [/composeItem/, /compose-out/, /Compose an item/]) assert.ok(!bad.test(src), 'found ' + bad);
    },
    'R3.5 every colour is a token at :root': () => {
      // Every :root block (the base tokens and any media-query override) may carry literals; nothing else may.
      const outside = css().replace(/:root[^{]*\{[^}]*\}/g, '').match(/#[0-9a-f]{3,8}\b/gi) || [];
      const stray = outside;
      assert.deepEqual(stray, [], 'colour literals outside :root');
    },
  };
  for (const [name, check] of Object.entries(checks)) {
    try { const note = check(); console.log(`  ${name.padEnd(76)} pass${note ? '  (' + note + ')' : ''}`); pass++; }
    catch (e) { console.log(`  ${name.padEnd(76)} FAIL  ${e.message.split('\n')[0]}`); fail++; }
  }
  console.log(`${pass} passed, ${fail} failed`);
}


// ---- Regressions from the self-review ------------------------------------
{
  console.log('\n== self-review regressions ==');
  const m = ctx.parse(fx('explorer-spec'));
  const checks = {
    'SR-1 no item is called clean while its panel flags a missing property': () => {
      const r = ctx.readiness(m, grammar, null, null);
      const bad = m.items.filter((it) => {
        const row = r.rows.find((x) => x.item === it);
        return row && row.clean && ctx.detailRows(m, it, grammar).some((x) => x.absent && x.expected);
      });
      assert.deepEqual(plain(bad.map((x) => x.id)), []);
    },
    'SR-1 the detail view and the drawer agree about one class': () => {
      const it = m.items.find((x) => x.id === 'OQ1');
      const panel = plain(ctx.detailRows(m, it, grammar)).filter((x) => x.expected).map((x) => x.key).sort();
      // The panel marks what would be flagged if absent; the drawer marks the same
      // set as required. A constraint with no minCount (resolutionStatus) is neither.
      const drawer = plain(ctx.referenceModel(m, grammar, it)).classes.find((c) => c.cls === 'OpenIssue')
        .expects.filter((e) => e.applies !== false && e.required).map((e) => e.key).sort();
      assert.deepEqual(panel, [...new Set(drawer)]);
      const optional = plain(ctx.referenceModel(m, grammar, it)).classes.find((c) => c.cls === 'OpenIssue')
        .expects.filter((e) => e.applies !== false && !e.required).map((e) => e.key);
      assert.deepEqual(optional, ['resolutionStatus'], 'and the one that is neither is shown as optional, not absent');
    },
    'SR-1 a conditional expectation is not demanded when the graph lacks the class': () => {
      const it = m.items.find((x) => x.id === 'R1.1');
      const keys = plain(ctx.detailRows(m, it, grammar)).filter((x) => x.absent && x.expected).map((x) => x.key);
      assert.deepEqual(keys, [], 'no Component and no Test in this graph, so constrains and verifiedBy are not expected');
    },
    'SR-2 the specification view counts reconcile': () => {
      const c = plain(ctx.specCounts(m)), r = ctx.readiness(m, grammar, null, null);
      assert.equal(c.retired + r.clean + (r.total - r.clean), c.total, `${c.total} items = ${c.retired} retired + ${r.clean} clean + ${r.total - r.clean} not clean`);
      assert.equal(c.counted, r.total);
      const retired = plain(ctx.sidebarRows(m, '', null, true)).filter((g) => !g.pinned).flatMap((g) => g.rows.map((x) => x.id));
      assert.deepEqual(retired, ['R7.2', 'R8.4', 'R13.6'], 'the retired chip opens the excluded items');  // three withdrawn requirements
    },
    'SR-6 no complex :not() selector, which older Safari rejects': () => {
      assert.ok(!/:not\([^)]*[ >+~][^)]*\)/.test(readFileSync(join(root, 'explorer.html'), 'utf8').match(/<script>([\s\S]*)<\/script>/)[1]));
    },
    'SR-8 no figure when the gate fails, on every route': () => {
      const bad = ctx.parse('@prefix specl: <https://w3id.org/specl/ns#> .\n@prefix dct: <http://purl.org/dc/terms/> .\n@prefix s: <https://x#> .\n<https://x> a specl:Specification ; dct:conformsTo <https://w3id.org/specl/contract/2> ; dct:title "t" ; dct:hasVersion "1" ; specl:status "draft" .\ns:R1 a specl:Requirement ; dct:description "x" .');
      const est = ctx.readiness(bad, grammar, null, null);
      assert.equal(est.score, null); assert.equal(est.gateFailed, true);
      const viaReport = ctx.readiness(bad, grammar, {status: 'draft', results: [{severity: 'Violation', focus: 'https://x#R1', path: 'p', message: 'm'}]}, null);
      assert.equal(viaReport.score, null, 'a report carrying a Violation withholds the figure too');
      const prod = ctx.readiness(m, grammar, {status: 'production', results: [{severity: 'Warning', focus: 'https://w3id.org/specl/explorer/spec#OQ1', path: 'p', message: 'm'}]}, null);
      assert.equal(prod.score, null, 'at status production a Warning fails the gate, as specl-validate has it');
      assert.notEqual(ctx.readiness(m, grammar, report, null).score, null, 'and a passing graph still shows one');
    },
    'SR-7 readiness is memoised per load': () => {
      const t0 = performance.now(); ctx.readiness(m, grammar, null, null); const cold = performance.now() - t0;
      assert.ok(cold < 100, `${cold.toFixed(0)} ms`); return `${cold.toFixed(0)} ms cold`;
    },
  };
  for (const [name, check] of Object.entries(checks)) {
    try { const note = check(); console.log(`  ${name.padEnd(76)} pass${note ? '  (' + note + ')' : ''}`); pass++; }
    catch (e) { console.log(`  ${name.padEnd(76)} FAIL  ${e.message.split('\n')[0]}`); fail++; }
  }
  console.log(`${pass} passed, ${fail} failed`);
}
process.exit(fail ? 1 : 0);
