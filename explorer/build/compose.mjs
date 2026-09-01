// One command from a specl markdown specification to a self-contained explorer
// that opens on it, with its validation findings attached. This is the shape of
// S4 until specl carries it (UP-3, UP-4); it shells out to the specl CLI for the
// inputs and to build.mjs for the assembly.
//
//   node build/compose.mjs path/to/spec.md [--out composed.html] [--grammar build/grammar.json] [--src explorer.html]
//
// Needs specl-translate and specl-validate on PATH. No network.
import { execFileSync } from 'node:child_process';
import { mkdtempSync, readFileSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join, dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const here = dirname(fileURLToPath(import.meta.url));
const argv = process.argv.slice(2);
const spec = argv.find((a) => !a.startsWith('--'));
if (!spec) { console.error('usage: node build/compose.mjs spec.md [--out composed.html] [--grammar build/grammar.json]'); process.exit(2); }
const opt = (k, d) => { const i = argv.indexOf('--' + k); return i >= 0 ? argv[i + 1] : d; };
const out = opt('out', 'composed.html'), grammar = opt('grammar', join(here, 'grammar.json')), src = opt('src', join(here, '..', 'explorer.html'));

const tmp = mkdtempSync(join(tmpdir(), 'specl-compose-'));
try {
  const ttl = join(tmp, 'spec.ttl'), rep = join(tmp, 'report.json');
  const t = execFileSync('specl-translate', [resolve(spec), ttl], { encoding: 'utf8' });
  process.stdout.write(t);
  try { execFileSync('specl-validate', ['validate', ttl, '--json', rep], { encoding: 'utf8', stdio: ['ignore', 'pipe', 'inherit'] }); }
  catch (e) { /* a failing gate still writes the report; the explorer shows the findings */ }
  const args = ['--src', src, '--grammar', grammar, '--example', ttl, '--autoload', '--out', out];
  try { readFileSync(rep); args.push('--report', rep); } catch { console.error('no validation report produced; composing without findings'); }
  process.stdout.write(execFileSync('node', [join(here, 'build.mjs'), ...args], { encoding: 'utf8' }));
} finally {
  rmSync(tmp, { recursive: true, force: true });
}
