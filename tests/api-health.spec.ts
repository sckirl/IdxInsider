import { test, expect } from '@playwright/test';

const BACKEND_URL = 'http://localhost:8000';
const FRONTEND_URL = 'http://localhost:6969';

test('Backend API health check', async ({ request }) => {
  const response = await request.get(`${BACKEND_URL}/`);
  expect(response.ok()).toBeTruthy();
  const data = await response.json();
  expect(data.message).toBe('Welcome to IDX OpenInsider API');
});

test('Frontend health check', async ({ page }) => {
  const response = await page.goto(FRONTEND_URL);
  expect(response?.ok()).toBeTruthy();
});

test('Latest insider activity endpoint structure', async ({ request }) => {
  const response = await request.get(`${BACKEND_URL}/insider/latest`);
  expect(response.ok()).toBeTruthy();
  const data = await response.json();
  expect(Array.isArray(data)).toBeTruthy();
  
  if (data.length > 0) {
    const item = data[0];
    expect(item).toHaveProperty('ticker');
    expect(item).toHaveProperty('insider_name');
    expect(item).toHaveProperty('transaction_type');
  }
});