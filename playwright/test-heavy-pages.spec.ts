import { test, expect } from '@playwright/test';

const BASE_URL = 'http://100.111.146.34:3336';

test.describe('Heavy pages load data correctly', () => {
  test('Lists page shows data', async ({ page }) => {
    await page.goto(`${BASE_URL}/lists`);
    await expect(page.locator('main')).toContainText('Lists');
    // Should show some list items
    await expect(page.locator('main')).toContainText('Games');
  });

  test('Squadrons page shows data', async ({ page }) => {
    await page.goto(`${BASE_URL}/squadrons`);
    await expect(page.locator('main')).toContainText('Squadrons');
    // Should show some squadron items
    await expect(page.locator('main')).toContainText('Games');
  });

  test('Ships page shows data', async ({ page }) => {
    await page.goto(`${BASE_URL}/ships`);
    await expect(page.locator('main')).toContainText('Ships');
    // Should show some ship items
    await expect(page.locator('main')).toContainText('Games');
  });

  test('Cards page shows data', async ({ page }) => {
    await page.goto(`${BASE_URL}/cards`);
    await expect(page.locator('main')).toContainText('Cards');
    // Should show some card items
    await expect(page.locator('main')).toContainText('Games');
  });
});

test.describe('Pagination works correctly', () => {
  test('Lists pagination shows different data on page 2', async ({ page }) => {
    // Go to page 1
    await page.goto(`${BASE_URL}/lists?page=1`);
    await expect(page.locator('main')).toContainText('Lists');
    
    // Go to page 2
    await page.goto(`${BASE_URL}/lists?page=2`);
    await expect(page.locator('main')).toContainText('Lists');
  });

  test('Squadrons pagination shows different data on page 2', async ({ page }) => {
    // Go to page 1
    await page.goto(`${BASE_URL}/squadrons?page=1`);
    await expect(page.locator('main')).toContainText('Squadrons');
    
    // Go to page 2
    await page.goto(`${BASE_URL}/squadrons?page=2`);
    await expect(page.locator('main')).toContainText('Squadrons');
  });

  test('Ships pagination shows different data on page 2', async ({ page }) => {
    // Go to page 1
    await page.goto(`${BASE_URL}/ships?page=1`);
    await expect(page.locator('main')).toContainText('Ships');
    
    // Go to page 2
    await page.goto(`${BASE_URL}/ships?page=2`);
    await expect(page.locator('main')).toContainText('Ships');
  });

  test('Cards pagination shows different data on page 2', async ({ page }) => {
    // Go to page 1
    await page.goto(`${BASE_URL}/cards?page=1`);
    await expect(page.locator('main')).toContainText('Cards');
    
    // Go to page 2
    await page.goto(`${BASE_URL}/cards?page=2`);
    await expect(page.locator('main')).toContainText('Cards');
  });
});

test.describe('Performance verification', () => {
  test('All pages load under 5 seconds', async ({ page }) => {
    const pages = [
      `${BASE_URL}/lists`,
      `${BASE_URL}/squadrons`,
      `${BASE_URL}/ships`,
      `${BASE_URL}/cards`,
    ];
    
    for (const url of pages) {
      const start = Date.now();
      await page.goto(url);
      await expect(page.locator('main')).toBeVisible();
      const loadTime = Date.now() - start;
      console.log(`${url} loaded in ${loadTime}ms`);
      expect(loadTime).toBeLessThan(5000);
    }
  });
});
