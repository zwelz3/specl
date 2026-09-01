// DOM smoke test. Optional: needs jsdom on the module path. The main harness
// (run.mjs) has no dependencies; this one checks the parts only a DOM can:
// the constant tab set (R3.3), default selection (R4.6), the pinned row
// (R4.7), selection without rebuilding the list (R4.9), the raw-view toggle
// (R7.6), the fragment (R11.1) and the trail (R11.2).
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';
import { createRequire } from 'node:module';
import assert from 'node:assert/strict';

const here = dirname(fileURLToPath(import.meta.url));
const root = join(here, '..');
let JSDOM;
try { JSDOM = createRequire(process.env.JSDOM_FROM || import.meta.url)('jsdom').JSDOM; }
catch { console.log('jsdom not available; DOM smoke test skipped'); process.exit(0); }

const html = readFileSync(join(root, 'explorer.html'), 'utf8');
const ttl = readFileSync(join(root, 'fixtures', 'explorer-spec.ttl'), 'utf8');
const dom = new JSDOM(html, { runScripts: 'dangerously', url: 'http://localhost/explorer.html', pretendToBeVisual: true });
const { window } = dom, { document } = window;
window.HTMLElement.prototype.scrollIntoView = function () {};

// Hidden means hidden by computed style, not only by attribute. The drawer was once
// an <aside> caught by the rail's display rule, which overrides the UA [hidden] rule,
// and it covered the page as an empty fixed panel.
for (const id of ['drawer', 'report']) {
  const el = document.getElementById(id);
  assert.ok(el.hidden, id + ' starts hidden');
  assert.equal(window.getComputedStyle(el).display, 'none', id + ' is not displayed while hidden');
}
assert.equal(window.getComputedStyle(document.querySelector('.tabbar')).display, 'none', 'tab strip not displayed before load');

// Drive the same path the file input uses.
const ev = { target: { files: [{ text: async () => ttl }] } };
await document.getElementById('file').onchange(ev);

const tabs = document.querySelectorAll('.tabs [role=tab]');
assert.equal(tabs.length, 2, 'R3.3: two tabs');
assert.deepEqual([...tabs].map((t) => t.textContent), ['Detail', 'Raw Turtle']);

const pinned = document.querySelector('.group.pinned .item');
assert.ok(pinned, 'R4.7: pinned specification row');
assert.ok(pinned.classList.contains('active'), 'R4.6: specification selected on load');
assert.equal(document.querySelector('#panel h2').textContent, 'SPEC Specification', 'the heading names the class, and the title is a row below');
assert.ok(document.querySelector('#panel .chips'), 'specification view carries counts');
assert.ok(window.location.hash.startsWith('#spec'), 'R11.1: fragment written on load: ' + window.location.hash);

// Select a requirement; the list must not be rebuilt.
const before = [...document.querySelectorAll('#list .item')];
const r33 = before.find((d) => d.querySelector('.id').textContent === 'R3.3');
r33.click();
const after = [...document.querySelectorAll('#list .item')];
assert.ok(after.every((d, i) => d === before[i]), 'R4.9: same DOM nodes after selection');
assert.ok(r33.classList.contains('active') && !pinned.classList.contains('active'));
assert.equal(document.querySelector('#panel h2').textContent, 'REQ Requirement R3.3');
assert.ok(window.location.hash.startsWith('#R3.3'), 'R11.1: hash follows selection');
assert.equal(tabs.length, document.querySelectorAll('.tabs [role=tab]').length, 'R3.3: tab set unchanged');
// ARIA the structure actually delivers.
assert.equal(document.querySelectorAll('[role=tablist] > :not([role=tab])').length, 0, 'a tablist contains only tabs');
assert.ok([...tabs].every((t) => t.getAttribute('aria-controls') === 'panel'), 'tabs name the panel they control');
assert.equal(document.getElementById('panel').getAttribute('aria-labelledby'), 'tab-detail', 'the panel names its tab');
assert.equal(document.querySelectorAll('#list [role=option]').length, 0, 'no orphan options: the list is a plain grouped list');
assert.ok(document.querySelector('#list .item.active').getAttribute('aria-current') === 'true', 'the selected row is aria-current');

// Keyboard: Enter selects, ArrowDown moves focus to the next row.
const idx = after.indexOf(r33);
r33.focus();
after[idx].dispatchEvent(new window.KeyboardEvent('keydown', { key: 'ArrowDown', bubbles: true }));
assert.equal(document.activeElement, after[idx + 1], 'R4.9: focus moved to the adjacent row');

// Follow a backlink (D1 affects R3.3), then go back.
const link = [...document.querySelectorAll('#panel a.ref')].find((a) => a.textContent === 'D1');
assert.ok(link, 'R6.7: D1 listed under Referenced by');
link.click();
assert.equal(document.querySelector('#panel h2').textContent.split(' ').pop(), 'D1', 'R6.6: reference selected its target');
document.getElementById('back').click();
assert.equal(document.querySelector('#panel h2').textContent.split(' ').pop(), 'R3.3', 'R11.2: back returns to R3.3');
document.getElementById('fwd').click();
assert.equal(document.querySelector('#panel h2').textContent.split(' ').pop(), 'D1', 'R11.2: forward returns to D1');

// Raw Turtle, item then whole file.
tabs[1].click();
let pre = document.querySelector('#panel pre').textContent;
assert.ok(pre.startsWith('spec:D1 a specl:DecisionRecord'), 'R7.1: block starts at the subject');
assert.ok(!pre.includes('@prefix'), 'item block carries no prefixes');
document.querySelector('[data-whole="1"]').click();
pre = document.querySelector('#panel pre').textContent;
assert.ok(pre.startsWith('@prefix'), 'R7.6: whole file');
assert.ok(window.location.hash.endsWith('/ttl/whole'), 'R11.1: whole-file state in the fragment: ' + window.location.hash);

// Filter, and the header title as a way back to the specification.
const filter = document.getElementById('filter');
filter.value = 'attesting'; filter.dispatchEvent(new window.Event('input'));
const shown = [...document.querySelectorAll('#list .item .id')].map((e) => e.textContent);
assert.ok(shown.includes('spec') && shown.includes('P5') && shown.includes('US5'), 'filter narrows, pinned row stays: ' + shown.join(','));
document.getElementById('title').click();
assert.equal(document.querySelector('#panel h2').textContent, 'SPEC Specification', 'header title selects the specification');

// Report banner on a damaged file.
await document.getElementById('file').onchange({ target: { files: [{ text: async () => readFileSync(join(root, 'fixtures', 'malformed-statement.ttl'), 'utf8') }] } });
const rep = document.getElementById('report');
assert.ok(!rep.hidden && rep.textContent.includes('could not be read') && rep.textContent.includes('R2'), 'R2.9: report names the damaged statement');

console.log('DOM smoke test: all assertions passed');

// ---- Stages 7 to 10, in the built file (slots filled) -----------------------
{
  const built = readFileSync(join(root, 'dist', 'explorer.html'), 'utf8');
  const d2 = new JSDOM(built, { runScripts: 'dangerously', url: 'http://localhost/dist/explorer.html' });
  const w = d2.window, doc = w.document;
  w.HTMLElement.prototype.scrollIntoView = function () {};
  w.alert = (m) => { throw new Error('alert: ' + m); };

  // R9.4: the example loads from the empty state and states its version.
  const btn = doc.getElementById('load-example');
  assert.ok(btn && /v1\.0\.0/.test(btn.textContent), 'example button names the version: ' + (btn && btn.textContent));
  btn.click();
  assert.equal(doc.querySelector('#panel h2').textContent, 'SPEC Specification', 'example loaded');

  // R5.2 R5.3 R5.6: header figure and bar, from the embedded report.
  const mat = doc.getElementById('maturity');
  assert.ok(/maturity 94% \(from report\)/.test(mat.textContent), mat.textContent);
  assert.equal(doc.getElementById('bar').style.width, '94%');

  // R5.7 R5.8 R5.9 on the specification view.
  assert.ok(doc.querySelector('#panel details.def'), 'definition disclosure present');
  assert.ok(doc.querySelector('#panel .contrib'), 'contributors listed');
  const unclean = [...doc.querySelectorAll('#panel button.chip')].find((b) => /not clean/.test(b.textContent));
  assert.ok(unclean && unclean.textContent.startsWith('9 '), 'nine not clean: ' + (unclean && unclean.textContent));
  unclean.click();
  const listed = [...doc.querySelectorAll('#list .group:not(.pinned) .item .id')].map((e) => e.textContent);
  assert.equal(listed.length, 9, 'chip narrows the list to the population it counts');
  assert.ok(listed.every((id) => id.startsWith('OQ')), 'all open questions: ' + listed.join(','));
  assert.ok(doc.querySelector('#list .fmark'), 'R12.2: finding marker on a row');

  // R12.2 R6.4 on an item.
  [...doc.querySelectorAll('#list .item')].find((e) => e.querySelector('.id').textContent === 'OQ1').click();
  const panelText = doc.getElementById('panel').textContent;
  assert.ok(/not clean · specl-validate/.test(panelText), 'readiness chip names its source');
  assert.ok(/Findings/.test(panelText) && /Warning/.test(panelText) && /owner/.test(panelText), 'findings shown for OQ1');

  // R13.1 R13.3 R13.6: the drawer, contextual to the selection, with the composer.
  doc.getElementById('syntax').click();
  const drawer = doc.getElementById('drawer');
  assert.ok(!drawer.hidden, 'drawer opens');
  assert.ok(/specl 1\.0\.0/.test(drawer.textContent) && /contract 2/.test(drawer.textContent), 'reference states its provenance');
  const sel = drawer.querySelector('details.sel');
  assert.ok(sel && /OpenIssue/.test(sel.querySelector('summary').textContent), 'selected class opened');
  assert.ok(sel.querySelector('li.absent code').textContent === 'owner', 'the missing key is marked absent');
  assert.equal(doc.getElementById('compose-out'), null, 'R13.6 withdrawn: no composer in the drawer');
  assert.ok(/Key/.test(drawer.querySelector('table').textContent), 'front matter renders as a table, not a run of code spans');
  doc.getElementById('drawer-close').click();
  assert.ok(drawer.hidden, 'drawer closes');

  // Theme: dark by default, cycling to light and auto, with no persistence.
  const themeBtn = doc.getElementById('theme');
  assert.equal(doc.documentElement.getAttribute('data-theme'), 'dark');
  themeBtn.click(); assert.equal(doc.documentElement.getAttribute('data-theme'), 'light');
  assert.equal(themeBtn.textContent, 'light');
  themeBtn.click(); assert.equal(doc.documentElement.getAttribute('data-theme'), 'auto');
  themeBtn.click(); assert.equal(doc.documentElement.getAttribute('data-theme'), 'dark');
  console.log('DOM smoke test, built file: all assertions passed');
}
