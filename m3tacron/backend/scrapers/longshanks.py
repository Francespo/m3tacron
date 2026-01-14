"""
Longshanks Playwright Scraper for M3taCron (Updated with correct selectors).

URL format: https://longshanks.org/event/{id}/
"""
from typing import Optional, Dict, Any, List
from datetime import datetime


async def scrape_tournament(event_id: int) -> Optional[Dict[str, Any]]:
    """
    Scrape a Longshanks tournament page using Playwright.
    
    Args:
        event_id: Longshanks event ID.
    
    Returns:
        Dict with tournament info, players, and matches, or None if failed.
    """
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        raise ImportError("Playwright required: pip install playwright && playwright install")
    
    # Use the correct URL format
    url = f"https://longshanks.org/event/{event_id}/"
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
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
                "matches": [],  # Could add Games tab scraping
            }
        except Exception as e:
            print(f"Error scraping Longshanks {event_id}: {e}")
            return None
        finally:
            await browser.close()


async def _extract_tournament_info(page, event_id: int, url: str) -> Optional[Dict[str, Any]]:
    """Extract tournament metadata from the page."""
    try:
        # Title is in h1
        name_el = await page.query_selector("h1")
        name = await name_el.inner_text() if name_el else f"Longshanks Event {event_id}"
        
        # Try to find date (format varies)
        date_el = await page.query_selector(".event_date, .date, [class*='date']")
        date_str = await date_el.inner_text() if date_el else None
        
        return {
            "id": event_id,
            "name": name.strip(),
            "date": _parse_date(date_str) if date_str else datetime.now(),
            "format": "Standard",  # Longshanks doesn't always specify
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
        
        for i, link in enumerate(player_links):
            try:
                name = await link.inner_text()
                name = name.strip()
                
                # Get rank if available
                rank = i + 1
                if i < len(rank_elements):
                    rank_text = await rank_elements[i].inner_text()
                    try:
                        rank = int(rank_text.strip())
                    except ValueError:
                        pass
                
                # Get faction if available
                faction = None
                if i < len(faction_elements):
                    faction = await faction_elements[i].get_attribute("title")
                
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
    """Parse date string to datetime."""
    if not date_str:
        return datetime.now()
    
    formats = [
        "%d/%m/%Y", "%Y-%m-%d", "%d %B %Y", "%B %d, %Y",
        "%d-%m-%Y", "%d %b %Y", "%b %d, %Y",
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(date_str.strip(), fmt)
        except ValueError:
            continue
    
    return datetime.now()


async def search_xwing_tournaments() -> List[Dict[str, Any]]:
    """Search for X-Wing tournaments on Longshanks."""
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        return []
    
    tournaments = []
    url = "https://longshanks.org/events/"
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        try:
            await page.goto(url, wait_until="networkidle", timeout=30000)
            await page.wait_for_timeout(2000)
            
            # Find event links
            links = await page.query_selector_all("a[href*='/event/']")
            
            for link in links[:20]:
                try:
                    href = await link.get_attribute("href")
                    name = await link.inner_text()
                    
                    # Extract event ID from URL
                    if "/event/" in href:
                        parts = href.split("/event/")[1].split("/")
                        event_id = int(parts[0])
                        tournaments.append({
                            "id": event_id,
                            "name": name.strip(),
                            "url": f"https://longshanks.org{href}" if href.startswith("/") else href,
                        })
                except Exception:
                    continue
        except Exception:
            pass
        finally:
            await browser.close()
    
    return tournaments
