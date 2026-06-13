const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const data = JSON.parse(fs.readFileSync('/tmp/lh-home.json', 'utf8'));
const OUT = path.join(__dirname, 'out', 'web-lighthouse.png');

const cats = [
  { label: 'Performance',    score: data.performance },
  { label: 'Accessibility',  score: data.accessibility },
  { label: 'Best Practices', score: data['best-practices'] },
  { label: 'SEO',            score: data.seo },
];
const col = (s) => (s >= 90 ? '#3DD68C' : s >= 50 ? '#E0A33E' : '#E5484D');

const gauge = (c) => {
  const r = 54, circ = 2 * Math.PI * r, off = circ * (1 - c.score / 100), color = col(c.score);
  return `<div class="g">
    <svg width="132" height="132" viewBox="0 0 132 132">
      <circle cx="66" cy="66" r="${r}" fill="none" stroke="#222a35" stroke-width="8"/>
      <circle cx="66" cy="66" r="${r}" fill="none" stroke="${color}" stroke-width="8"
        stroke-dasharray="${circ}" stroke-dashoffset="${off}" stroke-linecap="round"
        transform="rotate(-90 66 66)"/>
      <text x="66" y="66" text-anchor="middle" dy=".35em" fill="${color}"
        font-size="38" font-family="JetBrains Mono, monospace" font-weight="600">${c.score}</text>
    </svg>
    <div class="lab">${c.label}</div>
  </div>`;
};

const metrics = data.metrics;
const html = `<!doctype html><html><head><meta charset="utf-8"><style>
*{box-sizing:border-box} body{margin:0;background:#0B0E12;display:flex;justify-content:center;padding:40px;
font-family:'JetBrains Mono',ui-monospace,monospace}
.card{width:900px;background:linear-gradient(180deg,#161A21,#1B212B);border:1px solid #2C3542;border-radius:16px;overflow:hidden;box-shadow:0 30px 70px -30px #000}
.bar{display:flex;align-items:center;gap:.6rem;padding:.85rem 1.2rem;background:#0B0E12;border-bottom:1px solid #232A34}
.dots{display:inline-flex;gap:.4rem}.dots i{width:11px;height:11px;border-radius:50%;background:#2C3542}
.dots i:first-child{background:#E0A33E}.dots i:nth-child(2){background:#3DD68C}
.t{color:#8B94A3;font-size:13px;margin-left:.4rem}
.badge{margin-left:auto;color:#3DD68C;font-size:12px;border:1px solid #2BA86E;border-radius:6px;padding:.15rem .55rem}
.gauges{display:flex;justify-content:space-around;padding:2rem 1.5rem 1rem}
.g{text-align:center}.lab{color:#C7CEDA;font-size:14px;margin-top:.5rem}
.metrics{display:flex;justify-content:center;gap:2.2rem;padding:.6rem 1rem 1.8rem;color:#8B94A3;font-size:13px;flex-wrap:wrap}
.metrics b{color:#E6EAF0;font-weight:600}
.foot{color:#5C6675;font-size:12px;text-align:center;padding-bottom:1.3rem}
</style></head><body>
<div class="card">
  <div class="bar"><span class="dots"><i></i><i></i><i></i></span>
    <span class="t">Lighthouse — davidvasutenko.fun · desktop</span>
    <span class="badge">● real run</span></div>
  <div class="gauges">${cats.map(gauge).join('')}</div>
  <div class="metrics">
    <span>FCP <b>${metrics.FCP}</b></span>
    <span>LCP <b>${metrics.LCP}</b></span>
    <span>TBT <b>${metrics.TBT}</b></span>
    <span>CLS <b>${metrics.CLS}</b></span>
  </div>
  <div class="foot">Lighthouse ${data.lhVersion} · custom WordPress block theme · no page builder</div>
</div></body></html>`;

(async () => {
  const b = await chromium.launch();
  const p = await (await b.newContext({ viewport: { width: 980, height: 480 }, deviceScaleFactor: 2 })).newPage();
  await p.setContent(html, { waitUntil: 'load' });
  await p.waitForTimeout(300);
  await (await p.$('.card')).screenshot({ path: OUT });
  console.log('OK ' + OUT);
  await b.close();
})().catch((e) => { console.error(e.message); process.exit(1); });
