// R9.4, second criterion: the embedded example must be identical to the
// graph emitted from the specification. Exits 1 on divergence.
//   node build/check-example.mjs dist/explorer.html fixtures/explorer-spec.ttl
import { readFileSync } from 'node:fs';
const [html, ttl] = process.argv.slice(2).map((p) => readFileSync(p, 'utf8'));
const m = html.match(/<script type="application\/json" id="slot-example">([\s\S]*?)<\/script>/);
if (!m || !m[1].trim()) { console.error('no embedded example in the built file'); process.exit(1); }
const embedded = JSON.parse(m[1].replace(/<\\\//g, '</')).turtle;
if (embedded !== ttl) {
  const at = [...embedded].findIndex((ch, i) => ch !== ttl[i]);
  console.error(`embedded example diverges from the emitted graph at byte ${at < 0 ? Math.min(embedded.length, ttl.length) : at}; rebuild`);
  process.exit(1);
}
console.log(`embedded example matches the emitted graph (${ttl.length} bytes)`);
