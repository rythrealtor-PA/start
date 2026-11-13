const { chromium } = require('playwright');
(async () => {
  const [dir, ...names] = process.argv.slice(2);
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1080, height: 1350 }, deviceScaleFactor: 1 });
  for (const n of names) {
    await page.goto(`file://${dir}/${n}.html`);
    await page.evaluate(() => document.fonts.ready);
    await page.waitForTimeout(150);
    await page.screenshot({ path: `${dir}/${n}.png`, clip: { x: 0, y: 0, width: 1080, height: 1350 } });
  }
  await browser.close();
})();
