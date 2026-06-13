// Описание-картинка бота (показывается до /start). 640x360, фирменный стиль.
// Рендер 2x -> суперсемплинг в 640x360.
const { chromium } = require('playwright');
const sharp = require('sharp');
const path = require('path');

const W = 640, H = 360, SCALE = 2;
const OUT = '/opt/portfolio/assistant/bot-description.png';
const THEME = '/opt/portfolio/src/theme/davidv/node_modules/@fontsource-variable';
const FONT_SG    = `file://${THEME}/space-grotesk/files/space-grotesk-latin-wght-normal.woff2`;
const FONT_ONE   = `file://${THEME}/onest/files/onest-cyrillic-wght-normal.woff2`;        // кир. фолбэк заголовков
const FONT_JBM_L = `file://${THEME}/jetbrains-mono/files/jetbrains-mono-latin-wght-normal.woff2`;
const FONT_JBM_C = `file://${THEME}/jetbrains-mono/files/jetbrains-mono-cyrillic-wght-normal.woff2`;
const A = '#3DD68C', A_DIM = '#2BA86E';

const html = `<!doctype html><html><head><meta charset="utf-8"><style>
@font-face{font-family:'SG';src:url('${FONT_SG}') format('woff2');font-weight:300 700;font-display:block}
@font-face{font-family:'ONE';src:url('${FONT_ONE}') format('woff2');font-weight:300 700;font-display:block}
@font-face{font-family:'JBM';src:url('${FONT_JBM_L}') format('woff2');font-weight:300 700;font-display:block;
  unicode-range:U+0000-00FF,U+0131,U+0152-0153,U+2000-206F,U+2212}
@font-face{font-family:'JBM';src:url('${FONT_JBM_C}') format('woff2');font-weight:300 700;font-display:block;
  unicode-range:U+0400-045F,U+0490-0491}
*{box-sizing:border-box;margin:0;padding:0}
html,body{width:${W}px;height:${H}px}
body{font-family:'SG',sans-serif;-webkit-font-smoothing:antialiased}
.c{position:relative;width:${W}px;height:${H}px;overflow:hidden;
  background:radial-gradient(120% 130% at 78% -10%, #16221d 0%, #0d1217 48%, #090c10 100%)}
.grid{position:absolute;inset:0;
  background-image:radial-gradient(rgba(255,255,255,.05) 1px,transparent 1px);
  background-size:26px 26px;opacity:.55;
  -webkit-mask-image:linear-gradient(110deg,#000 0 45%,transparent 78%)}
.glow{position:absolute;right:-60px;top:-90px;width:380px;height:380px;border-radius:50%;
  background:radial-gradient(circle, rgba(61,214,140,.20) 0%, transparent 64%);filter:blur(6px)}
.edge{position:absolute;left:0;top:0;bottom:0;width:5px;background:linear-gradient(180deg,${A},${A_DIM} 60%,transparent)}
.in{position:relative;height:100%;display:flex;align-items:center;gap:30px;padding:0 40px}
.logo{flex:none}
.txt{display:flex;flex-direction:column}
.kick{font-family:'JBM',monospace;font-size:14px;letter-spacing:.22em;text-transform:uppercase;
  color:${A};opacity:.92;margin-bottom:8px}
.kick b{color:#5C6675;font-weight:400}
.title{font-family:'SG','ONE',sans-serif;font-weight:700;font-size:52px;line-height:1.0;letter-spacing:-.02em;color:#F3F6FA}
.tag{font-family:'JBM',monospace;font-size:15px;color:#AEB7C4;margin-top:14px;letter-spacing:.01em}
.chips{display:flex;gap:8px;margin-top:18px}
.chip{font-family:'JBM',monospace;font-size:12px;color:#C7CEDA;border:1px solid #2C3542;
  border-radius:999px;padding:5px 11px;background:rgba(255,255,255,.02)}
.chip.hl{color:${A};border-color:${A_DIM}}
</style></head><body>
<div class="c">
  <div class="grid"></div><div class="glow"></div><div class="edge"></div>
  <div class="in">
    <div class="logo">
      <svg width="132" height="132" viewBox="0 0 1024 1024" fill="none">
        <defs><linearGradient id="b" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stop-color="#1B212B"/><stop offset="1" stop-color="#12161D"/></linearGradient></defs>
        <rect x="292" y="292" width="440" height="440" rx="116" fill="url(#b)" stroke="${A_DIM}" stroke-width="3"/>
        <rect x="292" y="292" width="440" height="440" rx="116" fill="none" stroke="${A}" stroke-width="14"/>
        <path d="M398 516 L482 604 L646 416" stroke="${A}" stroke-width="64"
              stroke-linecap="round" stroke-linejoin="round" fill="none"/>
      </svg>
    </div>
    <div class="txt">
      <div class="kick"><b>//</b> для двоих</div>
      <div class="title">Ассистент<br>задач</div>
      <div class="tag">задачи · дедлайны · подзадачи · напоминания</div>
      <div class="chips">
        <span class="chip hl">Gemini-разбивка</span>
        <span class="chip">ставьте друг другу</span>
        <span class="chip">прогресс</span>
      </div>
    </div>
  </div>
</div></body></html>`;

(async () => {
  const b = await chromium.launch();
  const p = await (await b.newContext({ viewport: { width: W, height: H }, deviceScaleFactor: SCALE })).newPage();
  await p.setContent(html, { waitUntil: 'load' });
  await p.evaluate(() => document.fonts.ready);
  await p.waitForTimeout(350);
  const big = await p.screenshot({ clip: { x: 0, y: 0, width: W, height: H } });
  await sharp(big).resize(W, H, { fit: 'fill', kernel: 'lanczos3' }).png({ compressionLevel: 9 }).toFile(OUT);
  console.log('OK', OUT);
  await b.close();
})().catch((e) => { console.error('ERR', e.message); process.exit(1); });
