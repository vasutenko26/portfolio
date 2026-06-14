/**
 * Скриншоты RAG-ассистента с реальным диалогом:
 *   1) grounded-вопрос → ответ с раскрытой цитатой  (out/case-rag-answer.png)
 *   2) вопрос вне корпуса → честное «не нашёл»        (out/case-rag-notfound.png)
 *
 * node tools/screenshot/rag-capture.js [base-url]
 */
const { chromium } = require('playwright');
const fs = require('fs');

const BASE = process.argv[2] || 'https://rag.davidvasutenko.fun';
const OUT = 'tools/screenshot/out';

async function ask(page, q) {
  await page.fill('#q', q);
  await page.click('#send');
}

(async () => {
  fs.mkdirSync(OUT, { recursive: true });
  const browser = await chromium.launch();
  const ctx = await browser.newContext({
    viewport: { width: 1280, height: 1000 }, deviceScaleFactor: 2, colorScheme: 'dark',
  });
  const page = await ctx.newPage();
  try {
    await page.goto(BASE + '/', { waitUntil: 'networkidle', timeout: 45000 });
    await page.waitForTimeout(1200); // подтянуть список загруженных файлов

    // 1) grounded-вопрос → ждём ответ с источниками
    await ask(page, 'What is the maximum operating pressure of the X200 boiler?');
    await page.waitForSelector('.msg.bot .sources', { timeout: 45000 });
    await page.waitForTimeout(600);
    // раскрыть первую цитату, чтобы показать фрагмент-источник
    await page.$$eval('details.src', els => { if (els[0]) els[0].open = true; });
    await page.waitForTimeout(500);
    await page.screenshot({ path: `${OUT}/case-rag-answer.png`, fullPage: true });
    console.log('OK case-rag-answer.png');

    // 2) вопрос вне корпуса → «не нашёл»
    await ask(page, 'What is the capital of France?');
    await page.waitForSelector('.msg.bot.notfound', { timeout: 45000 });
    await page.waitForTimeout(600);
    await page.screenshot({ path: `${OUT}/case-rag-notfound.png`, fullPage: true });
    console.log('OK case-rag-notfound.png');
  } finally {
    await browser.close();
  }
})().catch(e => { console.error(e.message); process.exit(1); });
