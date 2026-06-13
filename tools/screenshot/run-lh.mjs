import lighthouse from 'lighthouse';
import * as chromeLauncher from 'chrome-launcher';

const url = process.argv[2] || 'https://davidvasutenko.fun/';
const chrome = await chromeLauncher.launch({
  chromePath: '/home/dev/.cache/ms-playwright/chromium-1223/chrome-linux64/chrome',
  chromeFlags: ['--headless=new','--no-sandbox','--disable-gpu','--disable-dev-shm-usage'],
});
const opts = { port: chrome.port, output: 'json',
  onlyCategories: ['performance','accessibility','best-practices','seo'],
  formFactor: 'desktop', screenEmulation: { mobile:false, width:1350, height:940, deviceScaleFactor:1, disabled:false },
  throttling: { rttMs:40, throughputKbps:10240, cpuSlowdownMultiplier:1 } };
const res = await lighthouse(url, opts);
const c = res.lhr.categories;
const out = {};
for (const k of ['performance','accessibility','best-practices','seo']) out[k] = Math.round(c[k].score*100);
const a = res.lhr.audits;
out.metrics = {
  FCP: a['first-contentful-paint'].displayValue,
  LCP: a['largest-contentful-paint'].displayValue,
  TBT: a['total-blocking-time'].displayValue,
  CLS: a['cumulative-layout-shift'].displayValue,
};
out.lhVersion = res.lhr.lighthouseVersion;
out.url = url;
console.log(JSON.stringify(out, null, 2));
await chrome.kill();
