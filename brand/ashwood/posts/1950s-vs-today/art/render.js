const { chromium } = require('playwright');
const fs = require('fs');
(async () => {
  const [dir, scale, ...names] = process.argv.slice(2);
  const browser = await chromium.launch();
  for (const n of names) {
    const svg = fs.readFileSync(`${dir}/${n}.svg`, 'utf8');
    const m = svg.match(/width="(\d+)" height="(\d+)"/);
    const w = +m[1], h = +m[2];
    const page = await browser.newPage({ viewport: { width: w, height: h }, deviceScaleFactor: +scale });
    await page.setContent(`<html><body style="margin:0;background:transparent">${svg}</body></html>`);
    await page.waitForTimeout(200);
    await page.screenshot({ path: `${dir}/${n}.png`, clip: { x: 0, y: 0, width: w, height: h }, omitBackground: true });
    await page.close();
  }
  await browser.close();
})();
