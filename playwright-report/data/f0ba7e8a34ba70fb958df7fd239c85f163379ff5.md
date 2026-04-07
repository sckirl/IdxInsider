# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: ui-table.spec.ts >> Frontend UI Table Rendering >> dark mode preference
- Location: tests/ui-table.spec.ts:30:7

# Error details

```
Error: page.goto: net::ERR_CONNECTION_REFUSED at http://localhost:3000/
Call log:
  - navigating to "http://localhost:3000/", waiting until "load"

```

# Test source

```ts
  1  | import { test, expect } from '@playwright/test';
  2  | import * as fs from 'fs';
  3  | import * as path from 'path';
  4  | 
  5  | const FRONTEND_URL = 'http://localhost:3000';
  6  | const TEST_CASES_PATH = path.resolve(__dirname, '../docs/TEST_CASES.json');
  7  | 
  8  | test.describe('Frontend UI Table Rendering', () => {
  9  |   test('table renders correctly with data from TEST_CASES.json', async ({ page }) => {
  10 |     const testCases = JSON.parse(fs.readFileSync(TEST_CASES_PATH, 'utf-8'));
  11 |     await page.goto(FRONTEND_URL);
  12 | 
  13 |     // Wait for the table to load
  14 |     await page.waitForSelector('table, [role="table"]', { timeout: 10000 });
  15 | 
  16 |     for (const expected of testCases) {
  17 |       // Check for ticker and insider name in the table
  18 |       const tickerFound = await page.locator('table, [role="table"]').filter({ hasText: expected.ticker }).isVisible();
  19 |       const nameFound = await page.locator('table, [role="table"]').filter({ hasText: expected.insider_name }).isVisible();
  20 |       
  21 |       if (!tickerFound || !nameFound) {
  22 |         await page.screenshot({ path: `test-results/ui-fail-${expected.ticker}.png` });
  23 |       }
  24 |       
  25 |       expect(tickerFound).toBeTruthy();
  26 |       expect(nameFound).toBeTruthy();
  27 |     }
  28 |   });
  29 | 
  30 |   test('dark mode preference', async ({ page }) => {
> 31 |     await page.goto(FRONTEND_URL);
     |                ^ Error: page.goto: net::ERR_CONNECTION_REFUSED at http://localhost:3000/
  32 |     const bgColor = await page.evaluate(() => {
  33 |       return window.getComputedStyle(document.body).backgroundColor;
  34 |     });
  35 |     console.log('Background Color:', bgColor);
  36 |     // Simple check: check if it's dark (not white)
  37 |     // white is rgb(255, 255, 255)
  38 |     expect(bgColor).not.toBe('rgb(255, 255, 255)');
  39 |   });
  40 | });
```