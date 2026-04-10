const { chromium } = require('playwright');
(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();
  page.on('request', request => {
    if (request.url().includes('GetAnnouncement')) {
      console.log('URL:', request.url());
    }
  });
  await page.goto("https://www.idx.co.id/id/perusahaan-tercatat/keterbukaan-informasi/", { waitUntil: "networkidle" });
  await page.fill("#FilterSearch", "Laporan Kepemilikan");
  await page.keyboard.press("Enter");
  await page.waitForTimeout(5000);
  await browser.close();
})();
