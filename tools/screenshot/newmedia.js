// Обложки (1280×853) + галерейные рамки (1600×900) для кейсов status/observability/rag.
// Тот же бренд-шаблон, что и у bot-кейса (см. botmedia.js), но окно под landscape-скрины.
const { chromium } = require('playwright');
const sharp = require('sharp');
const fs = require('fs');
const path = require('path');

const OUT = path.join(__dirname, 'out');
const THEME = '/opt/portfolio/src/theme/davidv/node_modules/@fontsource-variable';
const SG  = `file://${THEME}/space-grotesk/files/space-grotesk-latin-wght-normal.woff2`;
const ONE = `file://${THEME}/onest/files/onest-cyrillic-wght-normal.woff2`;
const JBL = `file://${THEME}/jetbrains-mono/files/jetbrains-mono-latin-wght-normal.woff2`;
const A = '#3DD68C', A_DIM = '#2BA86E';

const img = (f) => {
  const ext = path.extname(f).slice(1).toLowerCase();
  const mime = ext === 'png' ? 'image/png' : 'image/jpeg';
  return `data:${mime};base64,` + fs.readFileSync(path.join(OUT, f)).toString('base64');
};

const FONTS = `
@font-face{font-family:'SG';src:url('${SG}') format('woff2');font-weight:300 700;font-display:block}
@font-face{font-family:'ONE';src:url('${ONE}') format('woff2');font-weight:300 700;font-display:block}
@font-face{font-family:'JBM';src:url('${JBL}') format('woff2');font-weight:300 700;font-display:block}
*{box-sizing:border-box;margin:0;padding:0}`;

const BG = `radial-gradient(120% 120% at 82% -10%, #16221d 0%, #0d1217 48%, #090c10 100%)`;
const GRID = `background-image:radial-gradient(rgba(255,255,255,.05) 1px,transparent 1px);background-size:30px 30px;`;

const coverHtml = (c) => `<!doctype html><html><head><meta charset="utf-8"><style>${FONTS}
html,body{width:1280px;height:853px}
body{font-family:'SG','ONE',sans-serif;-webkit-font-smoothing:antialiased}
.c{position:relative;width:1280px;height:853px;overflow:hidden;background:${BG}}
.grid{position:absolute;inset:0;${GRID}opacity:.55;-webkit-mask-image:linear-gradient(105deg,#000 0 40%,transparent 72%)}
.glow{position:absolute;right:-120px;top:-150px;width:680px;height:680px;border-radius:50%;
 background:radial-gradient(circle,rgba(61,214,140,.20)0%,transparent 64%);filter:blur(8px)}
.edge{position:absolute;left:0;top:0;bottom:0;width:6px;background:linear-gradient(180deg,${A},${A_DIM} 60%,transparent)}
.in{position:relative;height:100%;display:flex;align-items:stretch}
.l{width:560px;flex:none;display:flex;flex-direction:column;justify-content:center;padding:64px 36px 64px 80px}
.kick{font-family:'JBM',monospace;font-size:19px;letter-spacing:.22em;text-transform:uppercase;color:${A};margin-bottom:24px}
.kick b{color:#5C6675;font-weight:400}
.t{font-family:'SG';font-weight:700;font-size:74px;line-height:.98;letter-spacing:-.02em;color:#F3F6FA}
.sub{font-family:'JBM',monospace;font-size:21px;color:#AEB7C4;margin-top:26px}
.tech{font-family:'JBM',monospace;font-size:15px;color:#6B7585;margin-top:11px}
.tag{align-self:flex-start;display:inline-flex;align-items:center;gap:11px;margin-top:34px;font-family:'JBM',monospace;
 font-size:19px;color:${A};border:1.5px solid ${A_DIM};border-radius:999px;padding:11px 20px;
 background:linear-gradient(180deg,rgba(61,214,140,.12),rgba(61,214,140,.04))}
.tag .d{width:11px;height:11px;border-radius:50%;background:${A};box-shadow:0 0 12px ${A}}
.r{position:relative;flex:1;overflow:hidden}
.win{position:absolute;top:50%;left:46%;transform:translate(-46%,-50%) rotate(-3deg);width:660px;height:452px;
 border-radius:14px;overflow:hidden;border:1px solid #2C3542;background:#0B0E12;
 box-shadow:0 40px 90px -28px #000,0 0 0 1px rgba(61,214,140,.10)}
.win .bar{height:30px;background:#0B0E12;border-bottom:1px solid #232A34;display:flex;align-items:center;gap:6px;padding:0 12px}
.win .bar i{width:9px;height:9px;border-radius:50%;background:#2C3542}
.win .bar i:first-child{background:#E0A33E}.win .bar i:nth-child(2){background:${A}}
.win img{width:100%;height:calc(100% - 30px);object-fit:cover;object-position:top center;display:block}
.mark{position:absolute;left:80px;bottom:46px;display:flex;align-items:center;gap:13px}
.mono{width:40px;height:40px;border:1.5px solid ${A_DIM};border-radius:9px;display:flex;align-items:center;justify-content:center;
 font-family:'SG';font-weight:700;font-size:19px;color:${A}}
.who{font-family:'JBM',monospace;font-size:14px;line-height:1.25;color:#8B94A3}
.who b{color:#E6EAF0;font-weight:600;display:block}
</style></head><body><div class="c">
 <div class="grid"></div><div class="glow"></div><div class="edge"></div>
 <div class="in">
  <div class="l">
   <div class="kick"><b>//</b> ${c.kick}</div>
   <div class="t">${c.title}</div>
   <div class="sub">${c.sub}</div>
   <div class="tech">${c.tech}</div>
   <div class="tag"><span class="d"></span>${c.tag}</div>
  </div>
  <div class="r"><div class="win"><div class="bar"><i></i><i></i><i></i></div><img src="${img(c.shot)}"></div></div>
 </div>
 <div class="mark"><div class="mono">DV</div><div class="who"><b>David Vasutenko</b>infrastructure engineer</div></div>
</div></body></html>`;

const galleryHtml = (file, caption) => `<!doctype html><html><head><meta charset="utf-8"><style>${FONTS}
html,body{width:1600px;height:900px}
body{font-family:'JBM',monospace;-webkit-font-smoothing:antialiased}
.c{position:relative;width:1600px;height:900px;overflow:hidden;background:${BG};display:flex;align-items:center;justify-content:center}
.grid{position:absolute;inset:0;${GRID}opacity:.5;-webkit-mask-image:radial-gradient(circle at 50% 45%,#000 55%,transparent 85%)}
.win{position:relative;width:1480px;height:792px;border-radius:16px;overflow:hidden;border:1px solid #2C3542;
 background:#0B0E12;box-shadow:0 36px 80px -30px #000,0 0 0 1px rgba(61,214,140,.08)}
.bar{display:flex;align-items:center;gap:.6rem;padding:.7rem 1.1rem;background:#0B0E12;border-bottom:1px solid #232A34}
.dots{display:inline-flex;gap:.4rem}.dots i{width:11px;height:11px;border-radius:50%;background:#2C3542}
.dots i:first-child{background:#E0A33E}.dots i:nth-child(2){background:${A}}
.cap{color:#C7CEDA;font-size:15px;margin-left:.5rem}
.badge{margin-left:auto;color:${A};font-size:12px;border:1px solid ${A_DIM};border-radius:6px;padding:.15rem .55rem}
.body{position:absolute;top:46px;left:0;right:0;bottom:0;display:flex;align-items:center;justify-content:center;background:#0B0E12;padding:14px}
.body img{max-width:100%;max-height:100%;object-fit:contain;display:block;border-radius:4px}
</style></head><body><div class="c"><div class="grid"></div>
 <div class="win"><div class="bar"><span class="dots"><i></i><i></i><i></i></span>
  <span class="cap">${caption}</span><span class="badge">● live</span></div>
  <div class="body"><img src="${img(file)}"></div></div>
</div></body></html>`;

const CASES = {
  status: {
    cover: { kick: 'monitoring', title: 'Public status<br>page', sub: 'Uptime Kuma · Docker · Caddy',
      tech: 'HTTP + TLS checks · incidents · Telegram alerts', tag: '6 services · live', shot: 'case-status-page.png' },
    gallery: [ ['case-status-page.png', 'Public status page · per-service uptime 24h / 7d / 30d'] ],
  },
  observability: {
    cover: { kick: 'observability', title: 'Observability<br>stack', sub: 'Prometheus · Grafana · Alertmanager',
      tech: 'host · containers · endpoints · blackbox', tag: 'alert → Telegram in ~90s', shot: 'case-obs-host.png' },
    gallery: [
      ['case-obs-host.png', 'Host overview · CPU / RAM / disk / network'],
      ['case-obs-containers.png', 'Containers · per-container CPU / RAM / network, by name'],
      ['case-obs-endpoints.png', 'Endpoints / Uptime · HTTP + TLS-expiry per endpoint'],
    ],
  },
  rag: {
    cover: { kick: 'ai assistant', title: 'Chat with<br>your documents', sub: 'FastAPI · Qdrant · self-hosted',
      tech: 'RAG · cited answers · data stays on-prem', tag: 'answers cite the source', shot: 'case-rag-answer.png' },
    gallery: [
      ['case-rag-answer.png', 'Answer with a citation to the source document & page'],
      ['case-rag-notfound.png', 'Out-of-corpus question → honest “not found”'],
    ],
  },
};

(async () => {
  const b = await chromium.launch();
  const render = async (html, w, h, out) => {
    const p = await (await b.newContext({ viewport: { width: w, height: h }, deviceScaleFactor: 2 })).newPage();
    await p.setContent(html, { waitUntil: 'load' });
    await p.evaluate(() => document.fonts.ready);
    await p.waitForTimeout(350);
    const big = await p.screenshot({ clip: { x: 0, y: 0, width: w, height: h } });
    await sharp(big).resize(w, h, { fit: 'fill', kernel: 'lanczos3' }).png({ compressionLevel: 9 }).toFile(out);
    await p.close();
    console.log('  +', path.basename(out));
  };
  for (const [key, c] of Object.entries(CASES)) {
    await render(coverHtml(c.cover), 1280, 853, path.join(OUT, `cover-${key}.png`));
    let i = 1;
    for (const [f, cap] of c.gallery) { await render(galleryHtml(f, cap), 1600, 900, path.join(OUT, `gal-${key}-${i}.png`)); i++; }
  }
  await b.close();
})().catch((e) => { console.error('ERR', e.message); process.exit(1); });
