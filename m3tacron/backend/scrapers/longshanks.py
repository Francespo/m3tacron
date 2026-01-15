"""
Longshanks Playwright Scraper for M3taCron (Updated with correct selectors).

URL format: https://longshanks.org/event/{id}/
"""
from typing import Optional, Dict, Any, List
from datetime import datetime
import re

async def scrape_tournament(event_id: int, browser=None) -> Optional[Dict[str, Any]]:
    """
    Scrape a Longshanks tournament page using Playwright.
    Only proceeds if it's an X-Wing or X-Wing Legacy event.
    
    Args:
        event_id: The Longshanks event ID.
        browser: Optional Playwright browser instance. If None, a new one is created/closed.

    Returns:
        Dict with tournament info, players, and matches, or None if failed.
    """
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        raise ImportError("Playwright required: pip install playwright && playwright install")
    
    # Use the correct URL format
    url = f"https://longshanks.org/event/{event_id}/"
    
    # Internal context manager helper if we need to launch our own
    class LocalBrowser:
        async def __aenter__(self):
            self.p = await async_playwright().start()
            self.b = await self.p.chromium.launch(headless=True)
            return self.b
        async def __aexit__(self, exc_type, exc, tb):
            await self.b.close()
            await self.p.stop()

    # Determine if we own the browser
    own_browser = browser is None
    
    try:
        browser_ctx = LocalBrowser() if own_browser else None
        
        # If we didn't get a browser, launch one
        current_browser = browser
        if own_browser:
            # We must await the context manager manualy if not using 'async with' block easily with conditional
            # Simplified: just duplicate logic slightly or use contextlib
            # For simplicity in this function structure:
            pass 

    except Exception:
        pass

    # Easier pattern: Logic split
    if browser:
        return await _scrape_with_browser(event_id, browser, url)
    else:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            return await _scrape_with_browser(event_id, browser, url)

async def _scrape_with_browser(event_id, browser, url):
    """Internal worker using an existing browser."""
    page = await browser.new_page()
    try:
        await page.goto(url, wait_until="networkidle", timeout=30000)
        
        # Wait for content to load
        await page.wait_for_timeout(2000)
        
        # Extract tournament info
        tournament = await _extract_tournament_info(page, event_id, url)
        if not tournament:
            return None
        
        # Click on "Player results" tab if exists
        try:
            await page.click("#tab_player", timeout=2000)
            await page.wait_for_timeout(1000)
        except:
            pass
        
        # Extract players
        players = await _extract_players(page)
        
        return {
            "tournament": tournament,
            "players": players,
            "matches": [],
        }
    except Exception as e:
        print(f"Error scraping Longshanks {event_id}: {e}")
        return None
    finally:
        await page.close()


async def _extract_tournament_info(page, event_id: int, url: str) -> Optional[Dict[str, Any]]:
    """Extract tournament metadata from the page."""
    try:


        # Title is in h1
        name_el = await page.query_selector("h1")
        name = await name_el.inner_text() if name_el else f"Longshanks Event {event_id}"
        
        # STRICT VALIDATION
        # 1. Check title for bad keywords
        bad_keywords = ["shatterpoint", "legion", "armada", "marvel crisis", "mcp", "40k", "warhammer", "kill team", "blood bowl"]
        name_lower = name.lower()
        if any(kw in name_lower for kw in bad_keywords):
            print(f"Skipping non-X-Wing event (bad keyword in title): {name}")
            return None

        # 2. Check for game system link
        # Longshanks usually links to the system page
        game_link = await page.query_selector("a[href^='/systems/xwing'], a[href^='/systems/xwinglegacy']")
        
        # 3. Check page content for X-Wing mentions if link not found
        content = await page.content()
        is_xwing_content = "X-Wing" in content or "xwing" in url or "xwinglegacy" in url
        
        if not game_link and not is_xwing_content:
             print(f"Skipping non-X-Wing event {event_id}: {name}")
             return None
        
        # Try to find date - Longshanks often puts it in a specific div
        # Format: "14 Jan 2024" or similar
        date_el = await page.query_selector("div.date")
        date_str = await date_el.inner_text() if date_el else ""
        
        parsed_date = _parse_date(date_str)
        
        # Determine format (Legacy vs Standard)
        fmt = "Standard"
        if "legacy" in name.lower() or "2.0" in name.lower():
            fmt = "Legacy"
        if "2.5" in name.lower():
            fmt = "Standard"
        
        return {
            "id": event_id,
            "name": name.strip(),
            "date": parsed_date,
            "format": fmt,
            "url": url,
            "platform": "Longshanks",
        }
    except Exception as e:
        print(f"Error extracting tournament info: {e}")
        return None


async def _extract_players(page) -> List[Dict[str, Any]]:
    """Extract player rankings using correct selectors."""
    players = []
    
    try:
        # Get all player links
        player_links = await page.query_selector_all("a.player_link")
        rank_elements = await page.query_selector_all("div.rank")
        faction_elements = await page.query_selector_all("img.logo")
        
        seen_names = set()
        
        for i, link in enumerate(player_links):
            try:
                name = await link.inner_text()
                name = name.strip()
                
                if not name or name in seen_names:
                    continue
                
                # Filter out likely non-player links (organizers often match event title)
                # This is heuristic but helpful
                parent_class = await link.evaluate("el => el.parentElement.className")
                if "admin" in parent_class or "organizer" in parent_class:
                    continue

                seen_names.add(name)
                
                # Get rank if available
                rank = len(players) + 1 # Simple increments since scraping order usually matches rank
                
                # Check explicit rank if aligned (risky if filtering happened)
                # Instead, rely on list order for rank 
                
                # Get faction if available (heuristic mapping likely fails with filtering)
                # We'll try to get faction relative to the link row if possible
                # But for now, keeping simple structure
                faction = None
                
                players.append({
                    "rank": rank,
                    "name": name,
                    "faction": faction,
                    "xws": None,
                })
            except Exception:
                continue
                
    except Exception as e:
        print(f"Error extracting players: {e}")
    
    return players


def _parse_date(date_str: str) -> datetime:
    """Parse date string with multiple formats."""
    if not date_str:
        return datetime.now()
    
    # Remove ordinal suffixes (1st, 2nd, 3rd, 4th)
    clean_str = re.sub(r"(\d+)(st|nd|rd|th)", r"\1", date_str.strip())
    
    # Handle ranges (e.g. "2026-01-10 – 2026-01-11" or "10-11 Jan")
    # Take the first part
    if "–" in clean_str:
        clean_str = clean_str.split("–")[0].strip()
    if " - " in clean_str:
        clean_str = clean_str.split("-")[0].strip()
    
    formats = [
        "%d %b %Y",     # 14 Jan 2024
        "%d %B %Y",     # 14 January 2024
        "%Y-%m-%d",     # 2024-01-14
        "%d/%m/%Y",     # 14/01/2024
        "%B %d, %Y",    # January 14, 2024
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(clean_str, fmt)
        except ValueError:
            continue
            
    print(f"Warning: Could not parse date '{date_str}', using today.")
    return datetime.now()



async def scrape_longshanks_history(url_list: List[str]) -> List[Dict[str, Any]]:
    """
    Scrape tournament history from specific Longshanks subdomains.
    Returns metadata from the history page which is often more accurate.
    """
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        return []
    
    tournaments = []
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        
        for url in url_list:
            try:
                page = await browser.new_page()
                print(f"Scraping History: {url}")
                await page.goto(url, wait_until="networkidle", timeout=30000)
                await page.wait_for_timeout(2000)
                
                # Determine format based on URL
                fmt = "Standard"
                if "legacy" in url:
                    fmt = "Legacy"
                
                # Find all event cards
                cards = await page.query_selector_all(".event_display")
                
                for card in cards:
                    try:
                        # Name and ID
                        name_el = await card.query_selector(".event_name a")
                        if not name_el: continue
                        
                        name = await name_el.inner_text()
                        href = await name_el.get_attribute("href")
                        
                        # Extract ID: /event/1234/
                        if "/event/" not in href: continue
                        event_id = int(href.split("/event/")[1].split("/")[0])
                        
                        # Date
                        # Find icon with alt="Date", get parent row, read 2nd cell
                        date_str = await card.evaluate("""(card) => {
                            const img = card.querySelector('img[alt="Date"]');
                            if (!img) return "";
                            const tr = img.closest('tr');
                            if (tr && tr.cells.length > 1) {
                                return tr.cells[1].textContent.trim();
                            }
                            return "";
                        }""")
                        
                        parsed_date = _parse_date(date_str)
                        if not parsed_date or parsed_date.date() == datetime.now().date():
                             # Debug only if suspicious (today generally means fallback)
                             # (But events CAN be today, so this is just for dev)
                             print(f"DEBUG: Date '{date_str}' parsed as NOW for {name}")
                        
                        # Player Count
                        player_count = 0
                        p_text = await card.evaluate("""(card) => {
                            const img = card.querySelector('img[alt="Event size"]');
                            if (!img) return "";
                            const tr = img.closest('tr');
                            if (tr && tr.cells.length > 1) {
                                return tr.cells[1].textContent.trim();
                            }
                            return "";
                        }""")    # Format: "9 players" or "9 of 16 players"
                        
                        if p_text:
                            # Format: "9 players" or "9 of 16 players"
                            try:
                                player_count = int(p_text.split(" ")[0])
                            except:
                                pass
                        
                        tournaments.append({
                            "id": event_id,
                            "name": name.strip(),
                            "date": parsed_date,
                            "platform": "Longshanks",
                            "format": fmt,
                            "player_count": player_count,
                            "url": f"https://longshanks.org{href}"
                        })
                        
                    except Exception as e:
                        # print(f"Error parsing card: {e}")
                        continue
                        
                await page.close()
                
            except Exception as e:
                print(f"Error scraping {url}: {e}")
                
        await browser.close()
    
    return tournaments
