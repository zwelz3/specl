// Fill the explorer's slots and write the built file. Plain Node, no deps.
//
//   node build/build.mjs --grammar build/grammar.json --example fixtures/explorer-spec.ttl \
//        [--report report.json] [--score score.json] [--autoload] [--src explorer.html] --out dist/explorer.html
//
// --autoload marks the embedded graph to open on load (a composed copy for a
// reviewer) rather than to be offered from the empty state (the example).
//
// Each --flag names a file whose content goes into the matching slot. The
// example is Turtle; the rest are JSON. Anything the build can prove wrong
// about its inputs fails the build rather than the reader.
import { readFileSync, writeFileSync, mkdirSync } from 'node:fs';
import { dirname } from 'node:path';

const args = Object.fromEntries(process.argv.slice(2).reduce((a, x, i, arr) => (x.startsWith('--') ? [...a, [x.slice(2), arr[i + 1]]] : a), []));
const src = args.src || 'explorer.html';
const out = args.out || 'dist/explorer.html';
let html = readFileSync(src, 'utf8');

const safe = (s) => s.replace(/<\//g, '<\\/');          // never close the script early
function fill(id, json) {
  const tag = `<script type="application/json" id="slot-${id}"></script>`;
  if (!html.includes(tag)) throw new Error(`slot-${id} not found in ${src}; is it already filled?`);
  html = html.replace(tag, `<script type="application/json" id="slot-${id}">${safe(JSON.stringify(json))}</script>`);
}
function readJson(path, what) {
  const j = JSON.parse(readFileSync(path, 'utf8'));
  return j;
}

const filled = [];
if (args.grammar) {
  const g = readJson(args.grammar);
  for (const k of ['specl', 'contract', 'generated', 'keys', 'expectations', 'sections']) if (!(k in g)) throw new Error(`grammar lacks ${k}`);
  fill('grammar', g); filled.push(`grammar (specl ${g.specl})`);
}
if (args.example) {
  const turtle = readFileSync(args.example, 'utf8');
  const spec = turtle.match(/a specl:Specification\s*;[\s\S]*?\n\n/);
  if (!spec) throw new Error('example carries no specl:Specification block');
  const title = (spec[0].match(/dct:title "((?:[^"\\]|\\.)*)"/) || [])[1];
  const version = (spec[0].match(/dct:hasVersion "([^"]*)"/) || [])[1];
  if (!title || !version) throw new Error('example specification lacks dct:title or dct:hasVersion (R9.4 requires the version stated)');
  fill('example', { title, version, source: args.example, built: new Date().toISOString().slice(0, 19) + 'Z', autoload: 'autoload' in args, turtle });
  filled.push(`example (${title} v${version}, ${turtle.length} bytes)`);
}
if (args.report) { const r = readJson(args.report); if (!Array.isArray(r.results)) throw new Error('report has no results array'); fill('report', r); filled.push(`report (${r.results.length} results)`); }
if (args.score) { const s = readJson(args.score); if (!('score' in s)) throw new Error('score lacks score'); fill('score', s); filled.push('score'); }

mkdirSync(dirname(out), { recursive: true });
writeFileSync(out, html);
console.log(`wrote ${out} (${html.length} bytes): ${filled.join('; ') || 'no slots filled'}`);
