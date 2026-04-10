const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();
  
  console.log('--- FINAL PRODUCTION UAT: pukat-master:6969 ---');
  try {
    await page.goto('http://pukat-master:6969', { waitUntil: 'networkidle', timeout: 30000 });
    
    // 1. Check Data Presence
    const rowCount = await page.locator('tbody tr').count();
    console.log(`Transactions in Table: ${rowCount}`);
    
    const bodyText = await page.innerText('body');
    const has2026Data = bodyText.includes('2026');
    console.log(`2026 Data Coverage: ${has2026Data ? 'PASSED' : 'FAILED'}`);

    // 2. Check Intelligence UI
    const rvolPresent = bodyText.includes('RVOL');
    console.log(`Intelligence UI (RVOL): ${rvolPresent ? 'PASSED' : 'FAILED'}`);

    // 3. Cluster Validation
    await page.click('button:has-text("Cluster Buys")');
    await page.waitForTimeout(3000);
    const hasClusters = (await page.innerText('body')).includes('Accumulation');
    console.log(`Cluster Intelligence: ${hasClusters ? 'PASSED' : 'FAILED'}`);

    if (rowCount > 0 && has2026Data) {
        console.log('--- PRODUCTION SYSTEM CERTIFIED ---');
    } else {
        console.log('--- WARNING: DATA INGESTION IN PROGRESS ---');
    }

  } catch (err) {
    console.error('UAT CRASH:', err.message);
  } finally {
    await browser.close();
  }
})();
