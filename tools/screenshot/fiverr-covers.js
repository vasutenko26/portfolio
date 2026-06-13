// Fiverr gig covers — one studio system across all 5 services.
// Renders at 2x then supersamples down to EXACTLY 1280x769 PNG.
// Brand: graphite base + one signal accent, Space Grotesk (title) + JetBrains Mono (tech/proof).
// Fiverr-safe: no URLs/contacts, no third-party brand logo as the hero element.
const { chromium } = require('playwright');
const sharp = require('sharp');
const fs = require('fs');
const path = require('path');

const W = 1280, H = process.env.COVER_H ? +process.env.COVER_H : 769, SCALE = 2;
const SUFFIX = process.env.COVER_SUFFIX || '';
const THEME = '/opt/portfolio/src/theme/davidv/node_modules/@fontsource-variable';
const FONT_SG  = `file://${THEME}/space-grotesk/files/space-grotesk-latin-wght-normal.woff2`;
const FONT_JBM = `file://${THEME}/jetbrains-mono/files/jetbrains-mono-latin-wght-normal.woff2`;
const SHOTS = path.join(__dirname, 'out');
const OUT = '/opt/portfolio/fiverr-covers';
fs.mkdirSync(OUT, { recursive: true });

const only = process.argv[2]; // optional: render a single gig by key

// proof image -> base64 data uri (file:// can be flaky for <img> in setContent)
const img = (f) => {
  const p = path.join(SHOTS, f);
  return 'data:image/png;base64,' + fs.readFileSync(p).toString('base64');
};

const GIGS = [
  {
    key: 'telephony', kicker: 'telephony',
    title: 'Office<br>IP-PBX',
    sub: 'Asterisk 21 · FreePBX 17',
    tech: 'IVR · call queue · recording · CDR',
    proof: 'real CDR + recording',
    shot: 'tel-card-proof.png', fit: 'contain', tilt: -2,
  },
  {
    key: 'devops', kicker: 'devops',
    title: 'Dockerize<br>+ CI/CD',
    sub: 'Docker · GitHub Actions',
    tech: 'Compose · pipeline · Grafana',
    proof: 'push → deploy in 2 min',
    shot: 'dv-grafana.png', fit: 'cover', tilt: -2,
  },
  {
    key: 'linux', kicker: 'linux',
    title: 'VPS setup<br>& hardening',
    sub: 'Debian · SSH · ufw · fail2ban',
    tech: 'TLS · firewall · backups',
    proof: 'SSL Labs A+',
    shot: 'lx-ssllabs-crop.png', fit: 'cover', pos: 'center', tilt: -2,
  },
  {
    key: 'automation', kicker: 'automation',
    title: 'Self-hosted<br>n8n flows',
    sub: 'n8n · webhooks · Telegram',
    tech: 'workflows · APIs · no SaaS lock-in',
    proof: 'runs on your own server',
    shot: 'auto-n8n-canvas.png', fit: 'cover', pos: 'center', tilt: -2,
  },
  {
    key: 'web', kicker: 'web',
    title: 'Website +<br>deployment',
    sub: 'WordPress · custom theme',
    tech: 'block theme · Docker · auto-SSL',
    proof: 'Lighthouse 100',
    shot: 'web-hero.png', fit: 'cover', tilt: -2,
  },
];

const A = '#3DD68C';       // signal accent
const A_DIM = '#2BA86E';

const html = (g) => `<!doctype html><html><head><meta charset="utf-8"><style>
@font-face{font-family:'SG';src:url('${FONT_SG}') format('woff2');font-weight:300 700;font-display:block}
@font-face{font-family:'JBM';src:url('${FONT_JBM}') format('woff2');font-weight:300 700;font-display:block}
*{box-sizing:border-box;margin:0;padding:0}
html,body{width:${W}px;height:${H}px}
body{font-family:'SG',sans-serif;-webkit-font-smoothing:antialiased;overflow:hidden}
.cover{position:relative;width:${W}px;height:${H}px;
  background:radial-gradient(120% 90% at 88% -10%, #16201d 0%, #0c1014 45%, #090c10 100%);
  overflow:hidden}
/* faint dotted grid */
.grid{position:absolute;inset:0;
  background-image:radial-gradient(rgba(255,255,255,.05) 1px,transparent 1px);
  background-size:26px 26px;opacity:.6;
  -webkit-mask-image:linear-gradient(105deg,#000 0 38%,transparent 70%)}
/* accent glow behind proof */
.glow{position:absolute;right:-120px;top:-140px;width:620px;height:620px;border-radius:50%;
  background:radial-gradient(circle, rgba(61,214,140,.20) 0%, transparent 65%);filter:blur(8px)}
.edge{position:absolute;left:0;top:0;bottom:0;width:6px;background:linear-gradient(180deg,${A},${A_DIM} 60%,transparent)}
.inner{position:relative;height:100%;display:flex;align-items:stretch}
.left{width:560px;flex:none;display:flex;flex-direction:column;justify-content:center;
  padding:64px 40px 64px 78px;gap:0}
.kicker{font-family:'JBM',monospace;font-size:19px;letter-spacing:.22em;text-transform:uppercase;
  color:${A};opacity:.92;margin-bottom:26px}
.kicker b{color:#5C6675;font-weight:400}
.title{font-family:'SG';font-weight:700;font-size:86px;line-height:.98;letter-spacing:-.02em;
  color:#F3F6FA}
.sub{font-family:'JBM',monospace;font-size:22px;color:#AEB7C4;margin-top:30px;letter-spacing:.01em}
.tech{font-family:'JBM',monospace;font-size:16px;color:#6B7585;margin-top:12px;letter-spacing:.02em}
.tag{align-self:flex-start;display:inline-flex;align-items:center;gap:11px;margin-top:40px;
  font-family:'JBM',monospace;font-size:20px;font-weight:500;color:${A};
  border:1.5px solid ${A_DIM};border-radius:999px;padding:12px 22px;
  background:linear-gradient(180deg,rgba(61,214,140,.12),rgba(61,214,140,.04))}
.tag .dot{width:11px;height:11px;border-radius:50%;background:${A};box-shadow:0 0 12px ${A}}
.right{position:relative;flex:1;overflow:hidden}
.frame{position:absolute;top:50%;left:46%;transform:translate(-46%,-50%) rotate(${g.tilt}deg);
  width:660px;height:430px;border-radius:16px;overflow:hidden;
  border:1px solid #2C3542;box-shadow:0 40px 90px -28px #000, 0 0 0 1px rgba(61,214,140,.10);
  background:#0B0E12}
.frame img{width:100%;height:100%;object-fit:${g.fit};object-position:${g.pos || 'top left'};display:block}
.frame::after{content:'';position:absolute;inset:0;border-radius:16px;
  box-shadow:inset 0 0 0 1px rgba(255,255,255,.04), inset 0 -60px 80px -40px rgba(0,0,0,.6)}
/* own studio mark (no url / no contact) */
.mark{position:absolute;left:78px;bottom:46px;display:flex;align-items:center;gap:13px;z-index:3}
.mono{width:40px;height:40px;border:1.5px solid ${A_DIM};border-radius:9px;
  display:flex;align-items:center;justify-content:center;font-family:'SG';font-weight:700;
  font-size:19px;color:${A};letter-spacing:-.03em}
.mark .who{font-family:'JBM',monospace;font-size:14px;line-height:1.25;color:#8B94A3}
.mark .who b{color:#E6EAF0;font-weight:600;display:block;letter-spacing:.01em}
</style></head><body>
<div class="cover">
  <div class="grid"></div>
  <div class="glow"></div>
  <div class="edge"></div>
  <div class="inner">
    <div class="left">
      <div class="kicker"><b>//</b> ${g.kicker} service</div>
      <div class="title">${g.title}</div>
      <div class="sub">${g.sub}</div>
      <div class="tech">${g.tech}</div>
      <div class="tag"><span class="dot"></span>${g.proof}</div>
    </div>
    <div class="right">
      <div class="frame"><img src="${img(g.shot)}"></div>
    </div>
  </div>
  <div class="mark">
    <div class="mono">DV</div>
    <div class="who"><b>David Vasutenko</b>infrastructure engineer</div>
  </div>
</div>
</body></html>`;

(async () => {
  const b = await chromium.launch();
  const ctx = await b.newContext({ viewport: { width: W, height: H }, deviceScaleFactor: SCALE });
  const p = await ctx.newPage();
  const list = only ? GIGS.filter((g) => g.key === only) : GIGS;
  for (const g of list) {
    await p.setContent(html(g), { waitUntil: 'load' });
    await p.evaluate(() => document.fonts.ready);
    await p.waitForTimeout(400);
    const big = await p.screenshot({ clip: { x: 0, y: 0, width: W, height: H } });
    const dst = path.join(OUT, `fiverr-${g.key}${SUFFIX}.png`);
    await sharp(big).resize(W, H, { fit: 'fill', kernel: 'lanczos3' }).png({ compressionLevel: 9 }).toFile(dst);
    console.log('  +', dst);
  }
  await b.close();
})().catch((e) => { console.error('ERR', e.message); process.exit(1); });
