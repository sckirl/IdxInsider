const { chromium } = require('@playwright/test');

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();
  
  console.log("Navigating to IDX Keterbukaan Informasi...");
  await page.goto('https://www.idx.co.id/id/perusahaan-tercatat/keterbukaan-informasi/', { waitUntil: 'networkidle' });
  
  console.log("Waiting for announcements to load...");
  // Wait for the announcement list to appear
  await page.waitForSelector('.table-responsive', { timeout: 30000 });
  
  console.log("Extracting latest announcement headers...");
  const announcements = await page.evaluate(() => {
    const rows = Array.from(document.querySelectorAll('table tbody tr'));
    return rows.slice(0, 10).map(row => {
      const cols = row.querySelectorAll('td');
      return {
        date: cols[0]?.innerText.trim(),
        ticker: cols[1]?.innerText.trim(),
        title: cols[2]?.innerText.trim(),
        url: cols[2]?.querySelector('a')?.href
      };
    });
  });
  
  console.log("Latest Announcements:");
  console.log(JSON.stringify(announcements, null, 2));
  
  // Also try to intercept the API call
  console.log("Intercepting API calls...");
  page.on('response', response => {
    if (response.url().includes('GetAnnouncement')) {
      console.log(`API Call Found: ${response.url()}`);
      console.log(`Status: ${response.status()}`);
    }
  });
  
  // Trigger a refresh or search to capture API call
  await page.click('button:has-text("Cari")');
  await page.waitForTimeout(5000);
  
  await browser.close();
})();
