/**
 * Authenticated multi-page screenshotter for the local FreePBX admin
 * (http://127.0.0.1:8088). Logs in once via the FreePBX form, then captures
 * each admin page for the telephony portfolio case.
 *
 * Usage: node freepbx-capture.js <password>   (username is "admin")
 */
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const BASE = 'http://127.0.0.1:8088';
const USER = 'admin';
const PASS = process.argv[2];
const SID  = process.argv[3];   // a valid PHPSESSID obtained via curl form-login
const OUT = path.join(__dirname, 'out');

if (!PASS || !SID) { console.error('usage: node freepbx-capture.js <password> <PHPSESSID>'); process.exit(1); }

const TARGETS = [
  { name: 'pbx-extensions.png', url: '/admin/config.php?display=extensions',
    desc: 'Extensions list' },
  { name: 'pbx-ivr.png',        url: '/admin/config.php?display=ivr&view=form&id=2&action=edit',
    desc: 'IVR builder' },
  { name: 'pbx-queue.png',      url: '/admin/config.php?display=queues&view=form&extdisplay=2001',
    desc: 'Queue settings' },
  { name: 'pbx-recording.png',  url: '/admin/config.php?display=callrecording',
    desc: 'Call recording settings' },
  { name: 'pbx-timecondition.png', url: '/admin/config.php?display=timeconditions&view=form&itemid=2',
    desc: 'Time condition (office hours)' },
  { name: 'pbx-cdr.png',        url: '/admin/config.php?display=cdr',
    desc: 'CDR report', clickText: 'Search' },
  { name: 'pbx-recordings.png', url: '/admin/config.php?display=recordings',
    desc: 'System recordings' },
];

async function dismissOverlays(page) {
  // close any FreePBX modal / browser-outdated / notice popovers that block the view
  for (const sel of ['#btnCloseUpdateBrowser', '.close[data-dismiss=modal]', 'button[data-dismiss=modal]']) {
    const els = await page.$$(sel);
    for (const e of els) { try { await e.click({ timeout: 500 }); } catch (_) {} }
  }
  await page.keyboard.press('Escape').catch(() => {});
}

(async () => {
  fs.mkdirSync(OUT, { recursive: true });
  const browser = await chromium.launch();
  const ctx = await browser.newContext({
    viewport: { width: 1500, height: 1050 },
    deviceScaleFactor: 2,
    colorScheme: 'light',
    // FreePBX serves a stripped "update your browser" portal to the default
    // HeadlessChrome UA — present as a normal desktop Chrome so the real admin renders.
    userAgent: 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36',
  });
  // Use a session established out-of-band via a real form POST (the JS login form
  // does not submit cleanly under automation). ajax.php is session-authenticated.
  await ctx.addCookies([{ name: 'PHPSESSID', value: SID, domain: '127.0.0.1', path: '/' }]);
  const page = await ctx.newPage();
  page.setDefaultTimeout(45000);

  // ---- complete one-time first-run "locale" setup that otherwise intercepts nav ----
  await page.goto(BASE + '/admin/config.php', { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(2500);
  const submitBtn = page.locator('button:has-text("Submit"), input[type=submit]').first();
  if (await page.locator('text=default locales').count()) {
    try {
      await submitBtn.click();
      await page.waitForTimeout(3000);
      console.log('completed first-run locale setup');
    } catch (e) { console.log('locale submit skipped: ' + e.message); }
  }
  const loggedIn = await page.locator('text=Connectivity').count() > 0;
  console.log('admin session ' + (loggedIn ? 'OK' : 'NOT rendering menu'));

  // ---- capture each page ----
  for (const t of TARGETS) {
    try {
      await page.goto(BASE + t.url, { waitUntil: 'domcontentloaded', referer: BASE + '/admin/config.php' });
      await page.waitForTimeout(4500);     // let JS grids/forms render (no networkidle: pages poll)
      if (t.clickText) {
        // e.g. CDR report: submit the search form to load the results table
        try {
          await page.locator('button:has-text("' + t.clickText + '"), input[type=submit][value="' + t.clickText + '"]').first().click();
          await page.waitForTimeout(4000);
        } catch (e) { console.log('    (clickText "' + t.clickText + '" skipped: ' + e.message + ')'); }
      }
      await dismissOverlays(page);
      // hide cosmetic nag banners (unsigned-modules / browser-update notices) for clean shots
      await page.addStyleTag({ content:
        '#notification_bar,.fpbx-notification,#browser-update,#outdated,.signature-check,.fpbxregreminder,.global-message-banner,.alert.signature{display:none!important}'
      }).catch(() => {});
      await page.evaluate(() => {
        document.querySelectorAll('div,tr,li').forEach(el => {
          if (el.children.length <= 2 && /Unsigned Module|Update my browser|out of date|no sound packages|Potential Security/i.test(el.textContent || '')) {
            el.style.display = 'none';
          }
        });
      }).catch(() => {});
      await page.waitForTimeout(600);
      await page.screenshot({ path: path.join(OUT, t.name), fullPage: true });
      const title = await page.title();
      console.log('  + ' + t.name + '  (' + t.desc + ')  [' + title + ']');
    } catch (e) {
      console.log('  ! ' + t.name + ' FAILED: ' + e.message);
    }
  }
  await browser.close();
})().catch((e) => { console.error('ERR', e.message); process.exit(1); });
