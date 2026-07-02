import { test, expect } from '@playwright/test';

const FRONTEND_URL = process.env.LIGHTHOUSE_URL || 'http://localhost:3333';

interface WebVitals {
  lcp?: number;
  inp?: number;
  cls?: number;
  ttfb?: number;
}

async function collectWebVitals(page: any): Promise<WebVitals> {
  return page.evaluate(() => {
    return new Promise((resolve) => {
      const vitals: WebVitals = {};
      let resolved = false;

      function tryResolve() {
        if (!resolved && vitals.lcp !== undefined && vitals.cls !== undefined) {
          resolved = true;
          resolve(vitals);
        }
      }

      const perfObserver = new PerformanceObserver((list) => {
        for (const entry of list.getEntries()) {
          if (entry.entryType === 'largest-contentful-paint') {
            vitals.lcp = entry.startTime;
            tryResolve();
          }
        }
      });
      perfObserver.observe({ type: 'largest-contentful-paint', buffered: true });

      const clsObserver = new PerformanceObserver((list) => {
        let clsValue = 0;
        for (const entry of list.getEntries()) {
          if (!entry.hadRecentInput) {
            clsValue += (entry as any).value || 0;
          }
        }
        vitals.cls = clsValue;
        tryResolve();
      });
      clsObserver.observe({ type: 'layout-shift', buffered: true });

      const eventObserver = new PerformanceObserver((list) => {
        let maxInp = 0;
        for (const entry of list.getEntries()) {
          const et = entry as any;
          if (et.processingEnd && et.startTime) {
            const inp = et.processingEnd - et.startTime;
            if (inp > maxInp) maxInp = inp;
          }
        }
        if (maxInp > 0) vitals.inp = maxInp;
      });
      eventObserver.observe({ type: 'event', durationThreshold: 16, buffered: true });

      const navEntry = performance.getEntriesByType('navigation')[0] as any;
      if (navEntry && navEntry.responseStart) {
        vitals.ttfb = navEntry.responseStart;
      }

      setTimeout(() => {
        if (!resolved) resolve(vitals);
      }, 10000);
    });
  });
}

test.describe('Web Vitals', () => {
  test('homepage LCP and CLS within thresholds', async ({ page }) => {
    await page.goto(FRONTEND_URL, { waitUntil: 'networkidle' });
    const vitals = await collectWebVitals(page);

    if (vitals.lcp !== undefined) {
      expect(vitals.lcp).toBeLessThan(4000);
    }
    if (vitals.cls !== undefined) {
      expect(vitals.cls).toBeLessThan(0.25);
    }
    if (vitals.ttfb !== undefined) {
      expect(vitals.ttfb).toBeLessThan(800);
    }
  });

  test('tournaments page loads and renders', async ({ page }) => {
    await page.goto(`${FRONTEND_URL}/tournaments`, { waitUntil: 'networkidle' });
    const vitals = await collectWebVitals(page);

    if (vitals.lcp !== undefined) {
      expect(vitals.lcp).toBeLessThan(4000);
    }
    if (vitals.cls !== undefined) {
      expect(vitals.cls).toBeLessThan(0.25);
    }
  });

  test('lists page loads and renders', async ({ page }) => {
    await page.goto(`${FRONTEND_URL}/lists`, { waitUntil: 'networkidle' });
    const vitals = await collectWebVitals(page);

    if (vitals.lcp !== undefined) {
      expect(vitals.lcp).toBeLessThan(4000);
    }
    if (vitals.cls !== undefined) {
      expect(vitals.cls).toBeLessThan(0.25);
    }
  });

  test('cards page loads with search interaction', async ({ page }) => {
    await page.goto(`${FRONTEND_URL}/cards`, { waitUntil: 'networkidle' });
    const vitals = await collectWebVitals(page);

    if (vitals.lcp !== undefined) {
      expect(vitals.lcp).toBeLessThan(4000);
    }
    if (vitals.cls !== undefined) {
      expect(vitals.cls).toBeLessThan(0.25);
    }

    const searchInput = page.locator('input[type="text"], input[name="search"], input[placeholder*="search" i], input[placeholder*="filter" i]').first();
    if (await searchInput.isVisible().catch(() => false)) {
      await searchInput.click();
      await searchInput.fill('a');
      await page.waitForTimeout(500);
    }
  });

  test('ships page loads and renders', async ({ page }) => {
    await page.goto(`${FRONTEND_URL}/ships`, { waitUntil: 'networkidle' });
    const vitals = await collectWebVitals(page);

    if (vitals.lcp !== undefined) {
      expect(vitals.lcp).toBeLessThan(4000);
    }
    if (vitals.cls !== undefined) {
      expect(vitals.cls).toBeLessThan(0.25);
    }
  });
});
