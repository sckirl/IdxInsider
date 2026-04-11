import { test, expect } from '@playwright/test';

const FRONTEND_URL = 'http://localhost:6969';

test.describe('Killer Feature: Insider Accumulation Map & Absorption Ratio', () => {
  
  test('clicking a ticker opens the institutional drawer', async ({ page }) => {
    await page.goto(FRONTEND_URL);

    // 1. Wait for table
    await page.waitForSelector('table', { timeout: 15000 });

    // 2. Click the first ticker link (blue text)
    const firstTicker = page.locator('table td').filter({ hasText: /^[A-Z]{4}$/ }).first();
    const tickerName = await firstTicker.innerText();
    console.log(`Testing with ticker: ${tickerName}`);
    
    await firstTicker.click();

    // 3. Verify Drawer opens
    const drawer = page.locator('div.fixed.inset-0.z-50');
    await expect(drawer).toBeVisible();
    
    // 4. Verify Ticker name in drawer header
    const header = drawer.locator('h2');
    await expect(header).toContainText(tickerName);

    // 5. Verify Absorption Ratio section exists
    const absorptionSection = page.locator('section').filter({ hasText: /Absorption Ratio/i });
    await expect(absorptionSection).toBeVisible();
    
    // 6. Verify Accumulation Map section exists
    const mapSection = page.locator('section').filter({ hasText: /Accumulation Price Map/i });
    await expect(mapSection).toBeVisible();
    
    // 7. Verify price nodes exist (if any)
    const priceNodes = mapSection.locator('div.group.relative.flex.flex-col.gap-1');
    const nodeCount = await priceNodes.count();
    console.log(`Found ${nodeCount} price accumulation nodes for ${tickerName}`);
    
    // 8. Close drawer
    await page.locator('button').filter({ hasText: '✕' }).click();
    await expect(drawer).not.toBeVisible();
  });

  test('absorption ratio calculation visual check', async ({ page }) => {
    await page.goto(FRONTEND_URL);
    await page.waitForSelector('table', { timeout: 15000 });

    // Click BYAN specifically if possible, otherwise use the first one
    const byanTicker = page.locator('table td').filter({ hasText: 'BYAN' }).first();
    if (await byanTicker.isVisible()) {
        await byanTicker.click();
    } else {
        await page.locator('table td').filter({ hasText: /^[A-Z]{4}$/ }).first().click();
    }

    // Check for "x" ratio text (e.g. 0.62x or 3.5x)
    const ratioText = page.locator('span.text-5xl.font-black');
    await expect(ratioText).toContainText('x');
    
    const ratioValue = await ratioText.innerText();
    console.log(`Absorption Ratio Visualized: ${ratioValue}`);
  });
});
