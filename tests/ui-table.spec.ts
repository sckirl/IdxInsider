import { test, expect } from '@playwright/test';
import * as fs from 'fs';
import * as path from 'path';

const FRONTEND_URL = 'http://localhost:3000';
const TEST_CASES_PATH = path.resolve(__dirname, '../docs/TEST_CASES.json');

test.describe('Frontend UI Table Rendering', () => {
  test('table renders correctly with data from TEST_CASES.json', async ({ page }) => {
    const testCases = JSON.parse(fs.readFileSync(TEST_CASES_PATH, 'utf-8'));
    await page.goto(FRONTEND_URL);

    // Wait for the table to load
    await page.waitForSelector('table, [role="table"]', { timeout: 10000 });

    for (const expected of testCases) {
      // Check for ticker and insider name in the table
      const tickerFound = await page.locator('table, [role="table"]').filter({ hasText: expected.ticker }).isVisible();
      const nameFound = await page.locator('table, [role="table"]').filter({ hasText: expected.insider_name }).isVisible();
      
      if (!tickerFound || !nameFound) {
        await page.screenshot({ path: `test-results/ui-fail-${expected.ticker}.png` });
      }
      
      expect(tickerFound).toBeTruthy();
      expect(nameFound).toBeTruthy();
    }
  });

  test('dark mode preference', async ({ page }) => {
    await page.goto(FRONTEND_URL);
    const bgColor = await page.evaluate(() => {
      return window.getComputedStyle(document.body).backgroundColor;
    });
    console.log('Background Color:', bgColor);
    // Simple check: check if it's dark (not white)
    // white is rgb(255, 255, 255)
    expect(bgColor).not.toBe('rgb(255, 255, 255)');
  });
});