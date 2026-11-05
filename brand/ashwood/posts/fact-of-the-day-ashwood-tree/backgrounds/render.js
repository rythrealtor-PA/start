const { chromium } = require('playwright');
const fs = require('fs');
(async () => {
  const dir = process.argv[2]; const scale = parseFloat(process.argv[3] || '1');
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1080, height: 1350 }, deviceScaleFactor: scale });
  for (const n of ['slide1', 'slide2', 'slide3']) {
    const svg = fs.readFileSync(`${dir}/${n}.svg`, 'utf8');
    await page.setContent(`<html><body style="margin:0;background:#000">${svg}</body></html>`);
    await page.waitForTimeout(300);
    await page.screenshot({ path: `${dir}/${n}${scale > 1 ? '@2x' : ''}.png`, clip: { x: 0, y: 0, width: 1080, height: 1350 } });
  }
  await browser.close();
})();
