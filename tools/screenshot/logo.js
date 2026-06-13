// Логотип бота-ассистента — фирменный стиль (графит + сигнальный зелёный).
// Квадрат 1024x1024 (годится как аватар: важное держим в центральном круге).
// Рендер 2x -> суперсемплинг в 1024.
const { chromium } = require('playwright');
const sharp = require('sharp');
const path = require('path');

const S = 1024, SCALE = 2;
const OUT = '/opt/portfolio/assistant/bot-logo.png';
const A = '#3DD68C', A_DIM = '#2BA86E';

const html = `<!doctype html><html><head><meta charset="utf-8"><style>
*{box-sizing:border-box;margin:0;padding:0}
html,body{width:${S}px;height:${S}px}
.c{position:relative;width:${S}px;height:${S}px;overflow:hidden;
  background:radial-gradient(120% 120% at 50% 38%, #18241f 0%, #0e1318 46%, #090c10 100%)}
.grid{position:absolute;inset:0;
  background-image:radial-gradient(rgba(255,255,255,.05) 1.5px,transparent 1.5px);
  background-size:42px 42px;opacity:.5;
  -webkit-mask-image:radial-gradient(circle at 50% 50%, #000 55%, transparent 78%)}
.glow{position:absolute;left:50%;top:48%;transform:translate(-50%,-50%);
  width:680px;height:680px;border-radius:50%;
  background:radial-gradient(circle, rgba(61,214,140,.28) 0%, transparent 62%);filter:blur(6px)}
svg{position:absolute;inset:0}
</style></head><body>
<div class="c">
  <div class="grid"></div>
  <div class="glow"></div>
  <svg width="${S}" height="${S}" viewBox="0 0 1024 1024" fill="none">
    <defs>
      <linearGradient id="box" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0" stop-color="#1B212B"/>
        <stop offset="1" stop-color="#12161D"/>
      </linearGradient>
      <filter id="sh" x="-40%" y="-40%" width="180%" height="180%">
        <feDropShadow dx="0" dy="26" stdDeviation="34" flood-color="#000" flood-opacity="0.55"/>
      </filter>
    </defs>

    <!-- фирменный чек-бокс -->
    <rect x="292" y="292" width="440" height="440" rx="116"
          fill="url(#box)" stroke="${A_DIM}" stroke-width="3" filter="url(#sh)"/>
    <rect x="292" y="292" width="440" height="440" rx="116"
          fill="none" stroke="${A}" stroke-width="14"/>

    <!-- жирная зелёная галочка -->
    <path d="M398 516 L482 604 L646 416" stroke="${A}" stroke-width="64"
          stroke-linecap="round" stroke-linejoin="round" fill="none"/>
  </svg>
</div></body></html>`;

(async () => {
  const b = await chromium.launch();
  const p = await (await b.newContext({ viewport: { width: S, height: S }, deviceScaleFactor: SCALE })).newPage();
  await p.setContent(html, { waitUntil: 'load' });
  await p.waitForTimeout(300);
  const big = await p.screenshot({ clip: { x: 0, y: 0, width: S, height: S } });
  await sharp(big).resize(S, S, { fit: 'fill', kernel: 'lanczos3' }).png({ compressionLevel: 9 }).toFile(OUT);
  console.log('OK', OUT);
  await b.close();
})().catch((e) => { console.error('ERR', e.message); process.exit(1); });
