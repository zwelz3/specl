// Mobile smoke test. jsdom does no layout, so this checks the two things a
// narrow screen changes that are testable without rendering: the stylesheet
// carries a single-column breakpoint with touch-sized targets, and the pane
// switching behaves (load lands on the selection, selecting an item shows
// it, the "items" control brings the list back with focus on the active
// row). matchMedia is simulated as narrow.
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';
import { createRequire } from 'node:module';
import assert from 'node:assert/strict';

const here = dirname(fileURLToPath(import.meta.url));
const root = join(here, '..');
let JSDOM;
try { JSDOM = createRequire(process.env.JSDOM_FROM || import.meta.url)('jsdom').JSDOM; }
catch { console.log('jsdom not available; mobile smoke test skipped'); process.exit(0); }

const html = readFileSync(join(root, 'dist', 'explorer.html'), 'utf8');

// ---- Static: the stylesheet -----------------------------------------------
assert.ok(/<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">/.test(html), 'viewport meta');
assert.ok(/height:100dvh/.test(html), 'dynamic viewport height so the bottom is not under the browser chrome');
const css = html.match(/<style>([\s\S]*?)<\/style>/)[1];
// Extract the breakpoint block by brace matching; regexes trip over the nested :root override.
function block(css, opener) { const i = css.indexOf(opener); if (i < 0) return null; let d = 0, j = i + opener.length - 1; for (; j < css.length; j++) { if (css[j] === '{') d++; else if (css[j] === '}' && --d === 0) break; } return css.slice(i + opener.length, j); }
const narrow = block(css, '@media (max-width:720px){');
assert.ok(narrow, 'a narrow breakpoint exists');
assert.ok(/main\{grid-template-columns:1fr/.test(narrow) || /main\{display:block/.test(narrow), 'single column at the breakpoint (grid or block flow)');
assert.ok(/body\{display:block;height:auto/.test(narrow), 'one page scroll on a phone, no nested scroll regions');
assert.ok(/\.hrow\{display:flex/.test(narrow) && /\.hrow\{display:contents\}/.test(css), 'two header rows on a phone, flat header on desktop');
assert.ok(!/pointer:coarse/.test(css), 'no touch-device trigger: the breakpoint is width alone');
assert.ok(/main:not\(\.mode-list\)>aside\{display:none\}/.test(narrow) && /main\.mode-list section\{display:none\}/.test(narrow), 'one pane at a time, selection by default, decided by the stylesheet alone');
for (const sel of ['.item', '.btn', '.tabs [role=tab]', 'main>aside input']) assert.ok(new RegExp(sel.replace(/[.[\]]/g, '\\$&') + '\\{[^}]*min-height:4[04]px').test(narrow), 'touch target for ' + sel);
assert.ok(/main>aside input\{[^}]*font-size:16px/.test(narrow), '16px inputs so iOS does not zoom on focus');
assert.ok(/dl\{grid-template-columns:1fr/.test(narrow) || /dl\{display:block/.test(narrow), 'definition lists stack');
assert.ok(/\.drawer\{width:100vw/.test(narrow), 'drawer is full width');
assert.ok(/\.item \.preview\{white-space:normal\}/.test(narrow), 'labels wrap instead of truncating');
assert.ok(/\.nav \.lbl\{display:none\}/.test(narrow), 'back and forward are icon-only on narrow screens');

// ---- Behaviour: pane switching under a simulated narrow screen -----------
const dom = new JSDOM(html, { runScripts: 'dangerously', url: 'http://localhost/dist/explorer.html',
  pretendToBeVisual: true, beforeParse(w) { delete w.matchMedia; } });   // no matchMedia at all: the pane logic must not need it
const { window } = dom, { document } = window;
window.HTMLElement.prototype.scrollIntoView = function () {};
const main = document.querySelector('main');
const panes = document.getElementById('panes');
assert.equal(window.getComputedStyle(document.getElementById('drawer')).display, 'none', 'drawer not displayed while hidden');
assert.ok(panes, 'the items control exists in the tab strip');

assert.ok(document.querySelector('.tabbar').hidden, 'no tab strip (and no items control) before a file is loaded');
assert.ok(document.getElementById('file2') && document.getElementById('file2').type === 'file', 'the empty state carries a real file input, not a proxied click');
assert.ok(/No specification loaded/.test(document.getElementById('list').textContent), 'the rail explains itself when nothing is loaded');
assert.equal(document.getElementById('file2').onchange, document.getElementById('file').onchange, 'both inputs load the same way');
document.getElementById('load-example').click();
assert.ok(!main.classList.contains('mode-list'), 'loading lands on the specification view, not the list');
assert.ok(/Open a/.test(html.match(/<div id="panel"[^>]*>([\s\S]*?)<\/div>/)[1]), 'a static empty state is in the markup for a render with scripts blocked');
assert.ok(!document.querySelector('.tabbar').hidden, 'tab strip appears once a file is loaded');
assert.equal(document.querySelector('#panel h2').textContent, 'SPEC Specification', 'the heading names the class, and the title is a row below');

panes.click();
assert.ok(main.classList.contains('mode-list'), 'items control shows the list');
assert.ok(document.activeElement && document.activeElement.classList.contains('item') && document.activeElement.classList.contains('active'), 'focus lands on the active row');

const r33 = [...document.querySelectorAll('#list .item')].find((d) => d.querySelector('.id').textContent === 'R3.3');
r33.click();
assert.ok(!main.classList.contains('mode-list'), 'selecting an item shows it');
assert.equal(document.querySelector('#panel h2').textContent.split(' ').pop(), 'R3.3');

// Back and forward do not bounce the panes; the reader is reading the trail.
document.getElementById('back').click();
assert.ok(!main.classList.contains('mode-list'), 'trail navigation stays on the detail pane');

// The drawer is reachable and closes with Escape.
document.getElementById('syntax').click();
assert.ok(!document.getElementById('drawer').hidden);
document.dispatchEvent(new window.KeyboardEvent('keydown', { key: 'Escape' }));
assert.ok(document.getElementById('drawer').hidden, 'Escape closes the drawer');

// The tab strip still holds exactly two tabs plus the items control (R3.3 unchanged).
assert.equal(document.querySelectorAll('.tabs [role=tab]').length, 2);

console.log('mobile smoke test: stylesheet breakpoint and pane switching pass');
console.log('not verifiable here: rendered layout, touch scrolling, sticky tab strip, safe-area insets, real device fonts');

// ---- Chips open the population they count, on a phone too (R5.8) --------------
{
  // Back to the specification view by the header title.
  document.getElementById('title').click();
  assert.ok(!main.classList.contains('mode-list'));
  const chips = () => [...document.querySelectorAll('#panel button.chip')];
  const req = chips().find((b) => b.dataset.cls === 'Requirement');
  req.click();
  assert.ok(main.classList.contains('mode-list'), 'a class chip shows the list pane');
  const rows = () => [...document.querySelectorAll('#list .group:not(.pinned) .item')];
  assert.equal(rows().length, 78, 'narrowed to the requirements');
  const fb = document.getElementById('filterbar');
  assert.ok(!fb.hidden && /Requirements/.test(fb.textContent), 'the list says what it is showing');
  assert.ok(document.activeElement && document.activeElement.classList.contains('item'), 'focus moves into the list');

  document.getElementById('clearfilter').click();
  assert.ok(fb.hidden && rows().length === 113, 'show all clears the narrowing');

  document.getElementById('title').click();
  const notClean = chips().find((b) => b.dataset.state === 'unclean');
  notClean.click();
  assert.ok(main.classList.contains('mode-list') && rows().length === 9 && rows().every((r) => r.querySelector('.id').textContent.startsWith('OQ')), 'not-clean chip lists the nine open questions');

  document.getElementById('title').click();
  const fig = chips().find((b) => b.dataset.raise);
  assert.ok(fig, 'the maturity figure is a control');
  fig.click();
  assert.ok(!main.classList.contains('mode-list') && document.getElementById('raise'), 'the figure reaches its contributors on the same pane');
  console.log('chips: class, state and figure all open what they count');
}
