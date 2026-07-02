import { defineConfig } from '@playwright/test';

const baseURL = process.env.PLAYWRIGHT_BASE_URL
  || process.env.LIGHTHOUSE_URL
  || 'http://localhost:3333';

export default defineConfig({
  testDir: './tests/performance/playwright',
  timeout: 60000,
  retries: 0,
  use: {
    baseURL,
    headless: true,
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
    trace: 'retain-on-failure',
  },
  reporter: [
    ['json', { outputFile: 'reports/playwright-results.json' }],
    ['list'],
  ],
  projects: [
    {
      name: 'chromium',
      use: {
        browserName: 'chromium',
        launchOptions: {
          args: ['--no-sandbox'],
        },
      },
    },
  ],
});
