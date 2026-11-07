// usage: node shoot.js stills t1 t2 ...   |   node shoot.js frames fps duration outdir
const { chromium } = require('playwright');
const path = require('path');
(async () => {
  const [mode, ...rest] = process.argv.slice(2);
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1080, height: 1920 }, deviceScaleFactor: 1 });
  await page.goto('file://' + path.resolve(__dirname, 'reel.html'));
  await page.evaluate(() => document.fonts.ready);
  await page.waitForTimeout(300);
  if (mode === 'stills') {
    for (const t of rest) {
      await page.evaluate(x => window.setTime(x), +t);
      await page.screenshot({ path: path.resolve(__dirname, `still-${t}.png`) });
    }
  } else {
    const [fps, dur, out] = rest; const n = Math.round(+fps * +dur);
    for (let i = 0; i < n; i++) {
      await page.evaluate(x => window.setTime(x), i / +fps);
      await page.screenshot({ path: `${out}/f${String(i).padStart(4,'0')}.jpg`, type: 'jpeg', quality: 93 });
    }
  }
  await browser.close();
})();
