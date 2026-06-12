/**
 * Универсальный скриншоттер на Playwright.
 *
 * Примеры:
 *   node shot.js --url https://site --out out/a.png
 *   node shot.js --url https://panel --out out/b.png --selector "#dashboard"
 *   node shot.js --url https://n8n/home --out out/c.png \
 *       --login-url https://n8n/signin --login-user me --login-pass secret \
 *       --user-sel "input[name=email]" --pass-sel "input[name=password]" --submit-sel "button[type=submit]"
 */
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

function arg(name, def) {
  const i = process.argv.indexOf('--' + name);
  if (i === -1) return def;
  const v = process.argv[i + 1];
  if (v === undefined || v.startsWith('--')) return true; // флаг без значения
  return v;
}

(async () => {
  const url = arg('url');
  if (!url) { console.error('Нужен --url'); process.exit(1); }

  const out      = arg('out', 'out/shot.png');
  const selector = arg('selector', null);
  const fullPage = String(arg('full', 'true')) !== 'false';
  const width    = parseInt(arg('width', '1440'), 10);
  const height   = parseInt(arg('height', '900'), 10);
  const scale    = parseFloat(arg('scale', '2'));
  const waitMs   = parseInt(arg('wait', '1400'), 10);
  const color    = arg('color', 'dark') === 'light' ? 'light' : 'dark';

  const authUser = arg('auth-user', null);
  const authPass = arg('auth-pass', null);
  const loginUrl = arg('login-url', null);

  const browser = await chromium.launch();
  const reducedMotion = arg('reduced-motion', null) ? 'reduce' : 'no-preference';
  const ctx = await browser.newContext({
    viewport: { width, height },
    deviceScaleFactor: scale,
    colorScheme: color,
    reducedMotion,
    httpCredentials: authUser ? { username: authUser, password: authPass || '' } : undefined,
  });
  const page = await ctx.newPage();

  try {
    // Форм-логин для веб-панелей (n8n, Grafana, FreePBX и т.п.)
    if (loginUrl) {
      await page.goto(loginUrl, { waitUntil: 'networkidle', timeout: 30000 });
      await page.fill(arg('user-sel', 'input[name=username]'), String(arg('login-user', '')));
      await page.fill(arg('pass-sel', 'input[name=password]'), String(arg('login-pass', '')));
      await page.click(arg('submit-sel', 'button[type=submit]'));
      await page.waitForLoadState('networkidle', { timeout: 30000 }).catch(() => {});
    }

    await page.goto(url, { waitUntil: 'networkidle', timeout: 45000 });
    await page.waitForTimeout(waitMs);

    fs.mkdirSync(path.dirname(out), { recursive: true });

    if (selector) {
      const el = await page.waitForSelector(selector, { timeout: 10000 });
      await el.screenshot({ path: out });
    } else {
      await page.screenshot({ path: out, fullPage });
    }
    console.log('OK ' + out);
  } finally {
    await browser.close();
  }
})().catch((e) => { console.error(e.message); process.exit(1); });
