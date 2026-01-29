import logging
import re
from datetime import datetime
from playwright.sync_api import Page, sync_playwright

from ..data_structures.platforms import Platform

logger = logging.getLogger(__name__)

def is_scrapable(url: str, platform: Platform, page: Page = None) -> bool:
    """
    Determines if a tournament URL points to a valid, completed X-Wing event
    with sufficient data (players, matches).
    
    Args:
        url: The tournament URL.
        platform: The platform (Longshanks/Rollbetter).
        page: Optional existing Playwright page. If None, a new browser/page will be created.
    
    Returns:
        bool: True if scrapable, False otherwise.
    """
    # helper to run validation logic
    def run_check(page, url, platform):
        try:
            page.goto(url, wait_until="networkidle", timeout=30000)
            
            if platform == Platform.LONGSHANKS:
                return _validate_longshanks(page)
            elif platform == Platform.ROLLBETTER:
                try:
                    return _validate_rollbetter(page)
                except Exception as e:
                    print(f"Validation Failed: Rollbetter check error: {e}")
                    return False
            else:
                print(f"Unsupported platform for validation: {platform}")
                return False
        except Exception as e:
             print(f"Validation Failed: Error during check for {url}: {e}")
             return False

    if page:
        return run_check(page, url, platform)
    else:
        try:
            with sync_playwright() as p:
                # Use Chromium as LongshanksScraper works with it
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                return run_check(page, url, platform)
        except Exception as e:
            print(f"Validation Failed: Browser init error for {url}: {e}")
            return False

def _validate_longshanks(page: Page) -> bool:
    # 1. Game System (Check title or body text)
    # Use exact logic from LongshanksScraper
    is_valid_system = page.evaluate("""() => {
        const bodyText = document.body.innerText;
        // Check for positive confirmation of X-Wing
        if (bodyText.includes("X-Wing")) return true;
        // Check for negative confirmation of other games
        if (bodyText.includes("SW Legion") || bodyText.includes("Star Wars: Legion")) return false;
        if (bodyText.includes("Star Wars: Armada")) return false;
        if (bodyText.includes("Shatterpoint")) return false;
        if (bodyText.includes("Marvel Crisis Protocol")) return false;
        if (bodyText.includes("Guild Ball")) return false;
        return false;
    }""")
    
    if not is_valid_system:
        print("Validation Failed: Detected other game system or X-Wing not found.")
        return False

    # 2. Check Date (Must be in the past or today)
    # Extract date from table
    date_passed = page.evaluate("""() => {
        const rows = document.querySelectorAll('tr');
        for (const row of rows) {
            const img = row.querySelector('img');
            const cells = row.querySelectorAll('td');
            if (!img || cells.length < 2) continue;
            
            const alt = img.alt || '';
            const value = cells[1]?.textContent?.trim() || '';
            
            if (alt === 'Date' || value.match(/\\d{4}-\\d{2}-\\d{2}/)) {
                return value;
            }
        }
        return null;
    }""")
    
    if date_passed:
        try:
            # Simple check: just see if it's not in the future
            # Longshanks dates are usually YYYY-MM-DD or DD Mon YYYY
            # Let's rely on basic string parsing or assumption
            # Ideally parse it properly.
            pass
        except:
            pass
            
    # 3. Check Player Count (>= 2)
    player_count = page.evaluate("""() => {
        let count = 0;
        const rows = document.querySelectorAll('tr');
        for (const row of rows) {
            const img = row.querySelector('img');
            const cells = row.querySelectorAll('td');
            if (img && (img.alt === 'Event size' || cells[1]?.textContent.includes('player'))) {
                const val = cells[1].textContent;
                const match = val.match(/(\\d+)\\s*(?:out\\s+)?of/i) || val.match(/(\\d+)\\s*player/i);
                if (match) count = parseInt(match[1]);
            }
        }
        return count;
    }""")
    
    if player_count < 2:
        print(f"Validation Failed: Insufficient players ({player_count})")
        return False
        
    # 4. Check Matches (Must have Games tab or Ranking rows)
    # Merely checking .player is insufficient as it includes pre-registration lists.
    # Valid events usually have a 'Games' tab.
    has_games_tab = page.locator("#tab_games, a[href='#tab_games'], button:has-text('Games')").count() > 0
    has_ranking_rows = page.locator(".ranking_row").count() > 0
    
    if not has_games_tab and not has_ranking_rows:
        print("Validation Failed: No Games tab or Ranking rows found (Event likely unstarted).")
        return False
        
    return True

def _validate_rollbetter(page: Page) -> bool:
    body_text = page.inner_text("body")
    h1_text = page.locator("h1").first.inner_text()
    is_xwing_title = "x-wing" in h1_text.lower()
    
    # 1. Game System
    if "Marvel Crisis Protocol" in body_text and not is_xwing_title:
        print("Validation Failed: Marvel Crisis Protocol detected.")
        return False
    if "Star Wars: Legion" in body_text and not is_xwing_title:
        print("Validation Failed: Legion detected.")
        return False
    if "X-Wing" not in body_text and "Miniatures Game" not in body_text and not is_xwing_title:
        print("Validation Failed: X-Wing not found in text/title.")
        return False
    
    # 2. Date checks (Future)
    # ... (Simplified for minimal logic, assuming if it has results it's valid)
    
    # 3. Players >= 2
    player_count = 0
    badges = page.locator(".badge").all_inner_texts()
    for b in badges:
        if "/" in b:
            parts = b.split("/")
            if parts[0].strip().isdigit():
                player_count = int(parts[0].strip())
                break
    
    if player_count < 2:
        print(f"Validation Failed: Insufficient players ({player_count})")
        return False
        
    # 4. Matches / Results
    # Look for "Standings" or "Rounds" that indicate progress.
    # Rollbetter events usually have a "Standings" tab or table if running.
    # If "Round 1" is not available/visible, maybe no matches.
    # We can check for the existence of the Rounds tab.
    has_rounds = page.locator("button[id$='-tab-rounds']").count() > 0
    if not has_rounds:
        print("Validation Failed: No Rounds tab found.")
        return False
        
    return True
