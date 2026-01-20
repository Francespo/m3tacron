from playwright.sync_api import sync_playwright
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("DebugScenario")

def run():
    # Tournament 2546 matches were scraped successfully. Let's look at its Rounds.
    # We need to see if scenario is mentioned.
    url = "https://rollbetter.gg/tournaments/2546/rounds"
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url, wait_until="domcontentloaded")
        page.wait_for_timeout(3000)
        
        # Click Round 1 if available
        try:
             page.locator("button.nav-link:has-text('Round 1')").click()
             page.wait_for_timeout(1000)
        except:
             pass

        # Dump text of the page content, especially headers
        logger.info("Page Text Dump (First 2000 chars):")
        text = page.locator("body").inner_text()
        logger.info(text[:2000])
        
        # Specific search for scenario keywords
        keywords = ["Salvage", "Scramble", "Chance", "Assault", "Scenario"]
        for k in keywords:
            count = page.get_by_text(k).count()
            logger.info(f"Keyword '{k}': found {count} times.")
            if count > 0:
                 # Print context
                 loc = page.get_by_text(k).first
                 logger.info(f"Context for '{k}': {loc.locator('..').inner_text()[:100]}")

        browser.close()

if __name__ == "__main__":
    run()
