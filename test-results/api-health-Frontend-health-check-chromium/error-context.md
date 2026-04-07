# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: api-health.spec.ts >> Frontend health check
- Location: tests/api-health.spec.ts:13:5

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
  3  | const BACKEND_URL = 'http://localhost:8000';
  4  | const FRONTEND_URL = 'http://localhost:3000';
  5  | 
  6  | test('Backend API health check', async ({ request }) => {
  7  |   const response = await request.get(`${BACKEND_URL}/`);
  8  |   expect(response.ok()).toBeTruthy();
  9  |   const data = await response.json();
  10 |   expect(data.message).toBe('Welcome to IDX OpenInsider API');
  11 | });
  12 | 
  13 | test('Frontend health check', async ({ page }) => {
> 14 |   const response = await page.goto(FRONTEND_URL);
     |                               ^ Error: page.goto: net::ERR_CONNECTION_REFUSED at http://localhost:3000/
  15 |   expect(response?.ok()).toBeTruthy();
  16 | });
  17 | 
  18 | test('Latest insider activity endpoint structure', async ({ request }) => {
  19 |   const response = await request.get(`${BACKEND_URL}/insider/latest`);
  20 |   expect(response.ok()).toBeTruthy();
  21 |   const data = await response.json();
  22 |   expect(Array.isArray(data)).toBeTruthy();
  23 |   
  24 |   if (data.length > 0) {
  25 |     const item = data[0];
  26 |     expect(item).toHaveProperty('ticker');
  27 |     expect(item).toHaveProperty('insider_name');
  28 |     expect(item).toHaveProperty('transaction_type');
  29 |   }
  30 | });
```