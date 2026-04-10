const { chromium } = require('playwright');
(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();
  await page.goto("https://www.idx.co.id/id/perusahaan-tercatat/keterbukaan-informasi/", { waitUntil: "networkidle" });
  const inputs = await page.evaluate(() => {
    return Array.from(document.querySelectorAll('input')).map(el => ({id: el.id, type: el.type, class: el.className}));
  });
  console.log(inputs);
  await browser.close();
})();
