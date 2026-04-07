# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: ui-table.spec.ts >> Frontend UI Tests >> dark mode styles check
- Location: ui-table.spec.ts:17:7

# Error details

```
Error: page.goto: net::ERR_CONNECTION_REFUSED at http://localhost:3000/
Call log:
  - navigating to "http://localhost:3000/", waiting until "load"

```

# Test source

```ts
  1  | import { test, expect } from '@playwright/test';
  2  | 
  3  | test.describe('Frontend UI Tests', () => {
  4  |   test.beforeEach(async ({ page }) => {
> 5  |     await page.goto('/');
     |                ^ Error: page.goto: net::ERR_CONNECTION_REFUSED at http://localhost:3000/
  6  |   });
  7  | 
  8  |   test('table renders correctly', async ({ page }) => {
  9  |     // Check if table or main container exists
  10 |     // Based on requirements: Insider Table (Main Feature)
  11 |     // Let's look for a table or a div containing insider data
  12 |     await page.waitForSelector('table, [role="table"], main', { timeout: 5000 });
  13 |     const content = await page.content();
  14 |     expect(content.toLowerCase()).toContain('insider');
  15 |   });
  16 | 
  17 |   test('dark mode styles check', async ({ page }) => {
  18 |     // Check if the html or body has dark class or bg-black/bg-gray-900
  19 |     const bgColor = await page.evaluate(() => {
  20 |       return window.getComputedStyle(document.body).backgroundColor;
  21 |     });
  22 |     // Dark mode usually means black or very dark background
  23 |     // e.g., rgb(0, 0, 0) or similar
  24 |     // Let's check for dark colors if dark mode is preferred as per PM
  25 |     // If it's not dark, we might report it as a bug or UI requirement not met
  26 |     console.log('Background Color:', bgColor);
  27 |   });
  28 | });
  29 | 
```