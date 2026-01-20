import sys
import os
import logging
from playwright.sync_api import sync_playwright

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("DebugRollbetter")

BASE_URL = "https://rollbetter.gg"
TOURNAMENT_ID = "2519" # Known good (matches found in import)

def debug_participants():
    url = f"{BASE_URL}/tournaments/{TOURNAMENT_ID}"
    logger.info(f"Inspecting Ladder at {url}")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url, wait_until="domcontentloaded")
        page.wait_for_timeout(3000)
        
        # Check Ladder Table
        tables = page.locator("table").count()
        logger.info(f"Found {tables} tables.")
        
        if tables > 0:
            html = page.locator("table").first.inner_html()
            logger.info(f"First Table HTML (snippet): {html[:500]}...")
            
            # Check Rows
            rows = page.locator("table tr").count()
            logger.info(f"Found {rows} rows in table.")
            
            # Check Player Name selectors
            # Logic was: .fancy-link OR a[href*='/player/']
            fancy = page.locator(".fancy-link").count()
            links = page.locator("a[href*='/player/']").count()
            logger.info(f"Found {fancy} .fancy-link elements.")
            logger.info(f"Found {links} player links.")
            
        browser.close()

def debug_lists():
    url = f"{BASE_URL}/tournaments/{TOURNAMENT_ID}/lists"
    logger.info(f"Inspecting Lists at {url}")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url, wait_until="domcontentloaded")
        page.wait_for_timeout(3000)
        
        # Check Copy Buttons
        # "button:has-text('Copy XWS')"
        btns = page.locator("button:has-text('Copy XWS')").count()
        logger.info(f"Found {btns} Copy XWS buttons.")
        
        # Check generic buttons if 0
        if btns == 0:
            all_btns = page.locator("button").all()
            logger.info(f"Found {len(all_btns)} total buttons. Printing first 5 HTML:")
            for i, b in enumerate(all_btns[:5]):
                logger.info(f"Btn {i}: {b.inner_html()}")

        browser.close()

def debug_rounds():
    url = f"{BASE_URL}/tournaments/{TOURNAMENT_ID}"
    logger.info(f"Inspecting Rounds at {url}")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url, wait_until="domcontentloaded")
        page.wait_for_timeout(3000)
        
        try:
            # Click Rounds Tab
            round_nav = page.locator("a.nav-link:has-text('Rounds'), button.nav-link:has-text('Rounds')").first
            if round_nav.count() > 0:
                logger.info("Clicking 'Rounds' nav...")
                round_nav.click()
                page.wait_for_timeout(3000) # Wait longer for Vue/React
                
                # Print ALL buttons to find the tabs
                buttons = page.locator("button").all()
                logger.info(f"Found {len(buttons)} buttons on Rounds page.")
                for i, b in enumerate(buttons):
                    txt = b.inner_text().strip()
                    cls = b.get_attribute("class")
                    # Log buttons that might be tabs (e.g. Round 1)
                    if "Round" in txt or "Swiss" in txt or "Top" in txt:
                        logger.info(f"Potential Tab {i}: Text='{txt}', Class='{cls}'")
            
            # Deep DOM Search
            content = page.content()
            if "Round 1" in content:
                logger.info("Found 'Round 1' in page content!")
                # Find element
                r1 = page.get_by_text("Round 1").first
                if r1.count() > 0:
                    logger.info(f"Round 1 Element: {r1.inner_html()}")
                    logger.info(f"Round 1 Parent HTML: {r1.locator('..').inner_html()[:500]}")
                    logger.info(f"Round 1 Tag: {r1.evaluate('el => el.tagName')}")
                    logger.info(f"Round 1 Classes: {r1.get_attribute('class')}")
            else:
                logger.warning("'Round 1' text NOT found in page content.")
                
            # Check for dropdowns
            dropdowns = page.locator(".dropdown-toggle").count()
            logger.info(f"Found {dropdowns} dropdowns.")

            # Check Match Rows via generic selector
            generic_rows = page.locator("tr").count()
            logger.info(f"Total TR elements: {generic_rows}")
            
        except Exception as e:
            logger.error(f"Error navigating rounds: {e}")

        browser.close()

if __name__ == "__main__":
    debug_participants()
    debug_lists()
    debug_rounds()
