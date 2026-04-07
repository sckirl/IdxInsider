import { test, expect } from '@playwright/test';
import * as fs from 'fs';
import * as path from 'path';

const BACKEND_URL = 'http://localhost:8000';
const TEST_CASES_PATH = path.resolve(__dirname, '../docs/TEST_CASES.json');

test('Scraper Integration: Database matches TEST_CASES.json', async ({ request }) => {
  if (!fs.existsSync(TEST_CASES_PATH)) {
    throw new Error('TEST_CASES.json not found');
  }

  const testCases = JSON.parse(fs.readFileSync(TEST_CASES_PATH, 'utf-8'));
  const response = await request.get(`${BACKEND_URL}/insider/latest`);
  expect(response.ok()).toBeTruthy();

  const actualData = await response.json();

  // Check if each expected test case exists in actual data
  for (const expected of testCases) {
    const matching = actualData.find((a: any) => 
      a.ticker === expected.ticker && 
      a.insider_name === expected.insider_name &&
      a.date === expected.date
    );
    
    if (!matching) {
      console.error(`Missing data for ticker: ${expected.ticker}, insider: ${expected.insider_name}`);
    }
    
    expect(matching).toBeDefined();
    
    if (matching) {
      expect(matching.transaction_type).toBe(expected.transaction_type);
      expect(matching.shares).toBe(expected.shares);
      expect(matching.price).toBe(expected.price);
      expect(matching.value).toBe(expected.value);
      expect(matching.role).toBe(expected.role);
    }
  }
});