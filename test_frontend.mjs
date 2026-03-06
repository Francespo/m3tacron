import { chromium } from 'playwright';

(async () => {
    const browser = await chromium.launch();
    const page = await browser.newPage();
    await page.goto('http://localhost:5173/cards');
    await page.waitForLoadState('networkidle');

    console.log("Current URL:", page.url());

    // Click Date Range accordion
    await page.getByText('Date Range').click();
    
    // Fill Date Start
    // Find the first date input
    const startInput = page.locator('input[type="date"]').nth(0);
    await startInput.fill('2099-01-01');
    
    // Evaluate and dispatch event
    await startInput.evaluate(node => node.dispatchEvent(new Event('input', { bubbles: true })));
    await startInput.evaluate(node => node.dispatchEvent(new Event('change', { bubbles: true })));
    
    // Wait a bit for reactivity
    await page.waitForTimeout(1000);
    
    console.log("New URL:", page.url());
    
    await browser.close();
})();
