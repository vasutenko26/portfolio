const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const DIR = path.join(__dirname, 'cards-data');
const OUT = path.join(__dirname, 'out');

const CARDS = [
  { title: 'Asterisk / FreePBX — office PBX, live objects', file: 'tel-pbx.txt', out: 'tel-card-pbx.png' },
  { title: 'Proof — one real local test-call (CDR + recording)', file: 'tel-proof.txt', out: 'tel-card-proof.png' },
];

const esc = (s) => s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');

function colorize(text) {
  return text.split('\n').map((line) => {
    const e = esc(line);
    if (/^#/.test(line)) return `<span class="c">${e}</span>`;
    if (/^\$ /.test(line)) return `<span class="p">$</span>${e.slice(1)}`;
    if (/✅|VERDICT|RESTORE VERIFIED|ZERO DOWNTIME|active \(running\)/.test(line)) return `<span class="g">${e}</span>`;
    if (/⚠️|❌|FAIL|reached/.test(line)) return `<span class="w">${e}</span>`;
    if (/x[0-9.]+|AFTER|BEFORE|потерь\s*:\s*0|успешных/.test(line)) return `<span class="a">${e}</span>`;
    return e;
  }).join('\n');
}

const html = (title, body) => `<!doctype html><html><head><meta charset="utf-8">
<style>
@font-face{font-family:JBM;src:local('JetBrains Mono')}
*{box-sizing:border-box}
body{margin:0;background:#0B0E12;display:flex;justify-content:center;padding:34px;font-family:'JetBrains Mono',ui-monospace,monospace}
.card{width:860px;background:linear-gradient(180deg,#161A21,#1B212B);border:1px solid #2C3542;border-radius:14px;overflow:hidden;box-shadow:0 30px 70px -30px #000}
.bar{display:flex;align-items:center;gap:.6rem;padding:.7rem 1rem;background:#0B0E12;border-bottom:1px solid #232A34}
.dots{display:inline-flex;gap:.4rem}.dots i{width:11px;height:11px;border-radius:50%;background:#2C3542}
.dots i:first-child{background:#E0A33E}.dots i:nth-child(2){background:#3DD68C}
.t{color:#8B94A3;font-size:13px;margin-left:.4rem}
.badge{margin-left:auto;color:#3DD68C;font-size:12px;border:1px solid #2BA86E;border-radius:6px;padding:.15rem .5rem}
pre{margin:0;padding:1.1rem 1.2rem;color:#E6EAF0;font-size:13px;line-height:1.55;white-space:pre-wrap;word-break:break-word}
.p{color:#3DD68C}.g{color:#3DD68C}.a{color:#7fd8b0}.c{color:#5C6675}.w{color:#E0A33E}
</style></head><body>
<div class="card"><div class="bar"><span class="dots"><i></i><i></i><i></i></span>
<span class="t">${esc(title)}</span><span class="badge">● verified</span></div>
<pre>${body}</pre></div></body></html>`;

(async () => {
  const b = await chromium.launch();
  const p = await (await b.newContext({ viewport: { width: 940, height: 1200 }, deviceScaleFactor: 2 })).newPage();
  for (const c of CARDS) {
    const text = fs.readFileSync(path.join(DIR, c.file), 'utf8').replace(/\n+$/, '');
    await p.setContent(html(c.title, colorize(text)), { waitUntil: 'load' });
    await p.waitForTimeout(300);
    const el = await p.$('.card');
    await el.screenshot({ path: path.join(OUT, c.out) });
    console.log('  +', c.out);
  }
  await b.close();
})().catch((e) => { console.error('ERR', e.message); process.exit(1); });
