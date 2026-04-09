const { chromium } = require('playwright');
(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();
  page.on('request', request => {
    if (request.url().includes('GetAnnouncement') || request.url().includes('ListingData')) {
       console.log('API Request:', request.url());
    }
  });
  await page.goto('https://www.idx.co.id/id/perusahaan-tercatat/keterbukaan-informasi/', { waitUntil: 'networkidle' });
  await page.click('button:has-text("Cari")');
  await page.waitForTimeout(5000);
  await browser.close();
})();
