"""
Longshanks Playwright Scraper for M3taCron.

Supports X-Wing 2.5 (xwing.longshanks.org) and Legacy 2.0 (xwing-legacy.longshanks.org).
Extracts player lists from modals containing YASB/LaunchBayNext links.
"""

from datetime import datetime
import re

XWING_25_HISTORY = "https://xwing.longshanks.org/events/history/"
XWING_20_HISTORY = "https://xwing-legacy.longshanks.org/events/history/"


async def scrape_tournament(event_id: int, subdomain: str = "xwing", browser=None) -> dict[str, any] | None:
    """
    Scrape a Longshanks tournament page using Playwright.
    
    Args:
        event_id: The Longshanks event ID.
        subdomain: Either "xwing" (2.5) or "xwing-legacy" (2.0).
        browser: Optional Playwright browser instance.

    Returns:
        Dict with tournament info, players with XWS links, and matches.
    """
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        raise ImportError("Playwright required: pip install playwright && playwright install")
    
    # Build correct URL with subdomain
    url = f"https://{subdomain}.longshanks.org/event/{event_id}/"
    
    if browser:
        return await _scrape_with_browser(event_id, browser, url, subdomain)
    else:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            try:
                return await _scrape_with_browser(event_id, browser, url, subdomain)
            finally:
                await browser.close()


async def _scrape_with_browser(event_id: int, browser, url: str, subdomain: str) -> dict[str, any] | None:
    """Internal worker using an existing browser."""
    page = await browser.new_page()
    try:
        await page.goto(url, wait_until="networkidle", timeout=30000)
        await page.wait_for_timeout(2000)
        
        # Dismiss cookie consent popup if present
        await _dismiss_cookie_popup(page)
        
        # Extract tournament info
        tournament = await _extract_tournament_info(page, event_id, url, subdomain)
        if not tournament:
            return None
        
        # Extract players with list links
        players = await _extract_players_with_lists(page)
        
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


async def _dismiss_cookie_popup(page) -> None:
    """Dismiss the cookie consent popup if present."""
    try:
        # Look for the cookie permission popup
        cookie_popup = await page.query_selector("#cookie_permission")
        if cookie_popup:
            # Try to accept/dismiss by clicking the accept button
            accept_btn = await page.query_selector("#cookie_permission button, #cookie_permission a.accept, #cookie_permission .button")
            if accept_btn:
                await accept_btn.click()
                await page.wait_for_timeout(500)
            else:
                # Hide the popup via JavaScript
                await page.evaluate("""() => {
                    const popup = document.getElementById('cookie_permission');
                    if (popup) popup.style.display = 'none';
                }""")
    except Exception:
        # Silently ignore - popup may not exist
        pass


async def _extract_tournament_info(page, event_id: int, url: str, subdomain: str) -> dict[str, any] | None:
    """Extract tournament metadata from the page."""
    try:
        # Title is in h1
        name_el = await page.query_selector("h1")
        name = await name_el.inner_text() if name_el else f"Longshanks Event {event_id}"
        
        # Extract date and player count from event info table
        event_info = await page.evaluate("""() => {
            let dateStr = '';
            let playerCount = 0;
            
            const rows = document.querySelectorAll('tr');
            for (const row of rows) {
                const img = row.querySelector('img');
                const cells = row.querySelectorAll('td');
                if (!img || cells.length < 2) continue;
                
                const alt = img.alt || '';
                const value = cells[1]?.textContent?.trim() || '';
                
                // Event size (e.g. "17 players")
                if (alt === 'Event size' || value.includes('player')) {
                    // Check for "X out of Y players" pattern first
                    const outOfMatch = value.match(/(\d+)\s*out\s*of\s*\d+/i);
                    if (outOfMatch) {
                        playerCount = parseInt(outOfMatch[1], 10);
                    } else {
                        // Fallback to standard "X players"
                        const match = value.match(/(\d+)\s*player/i);
                        if (match) playerCount = parseInt(match[1], 10);
                    }
                }
                
                // Date
                if (alt === 'Date' || value.match(/\d{4}-\d{2}-\d{2}/) || value.match(/\d{1,2}\s+\w+\s+\d{4}/)) {
                    if (!dateStr) dateStr = value;
                }
            }
            
            return { dateStr, playerCount };
        }""")
        
        parsed_date = _parse_date(event_info.get("dateStr", ""))
        player_count = event_info.get("playerCount", 0)
        
        # Determine format based on subdomain
        fmt = "2.5" if subdomain == "xwing" else "2.0"
        
        return {
            "id": event_id,
            "name": name.strip(),
            "date": parsed_date,
            "format": fmt,
            "url": url,
            "platform": "Longshanks",
            "player_count": player_count,  # From Event size header
        }
    except Exception as e:
        print(f"Error extracting tournament info: {e}")
        return None


async def _extract_players_with_lists(page) -> list[dict[str, any]]:
    """
    Extract player rankings and their list links.
    
    Longshanks shows lists in modals. The </> icon indicates an encoded list
    with a link to YASB or LaunchBayNext.
    
    Note: The results table has repeated header rows (after every ~8 players).
    We only extract rows containing actual player links (a.player_link).
    """
    players = []
    
    try:
        # Use JavaScript to extract only actual player data, skipping header rows
        player_data = await page.evaluate("""() => {
            const results = [];
            // Only select actual player links - these are unique per player
            const playerLinks = document.querySelectorAll('a.player_link');
            
            playerLinks.forEach((link, idx) => {
                const row = link.closest('tr') || link.closest('div');
                if (!row) return;
                
                // Get faction from image
                let faction = null;
                const factionImg = row.querySelector('img.faction, img.logo');
                if (factionImg) {
                    faction = factionImg.alt || factionImg.src || null;
                }
                
                results.push({
                    name: link.textContent.trim(),
                    faction: faction,
                    index: idx
                });
            });
            
            return results;
        }""")
        
        for i, p in enumerate(player_data):
            players.append({
                "rank": i + 1,
                "name": p.get("name", f"Player {i+1}"),
                "faction": _parse_faction(p.get("faction") or ""),
                "xws_link": None,
                "xws": None,
            })
        
        # Extract list links from modals
        await _extract_list_links_from_icons(page, players)
        
    except Exception as e:
        print(f"Error extracting players: {e}")
    
    return players


async def _extract_list_links_from_icons(page, players: list[dict[str, any]]) -> None:
    """
    Extract XWS links by clicking on encoded list icons with force option.
    
    Uses Playwright's force=True to bypass overlay interception.
    """
    try:
        # Get icon-to-player mappings
        icon_data = await page.evaluate("""() => {
            const icons = document.querySelectorAll("img.logo[title='Encoded list']");
            const results = [];
            
            icons.forEach((icon, idx) => {
                let parent = icon.parentElement;
                let name = null;
                
                for (let i = 0; i < 10 && parent; i++) {
                    const playerLink = parent.querySelector('a.player_link');
                    if (playerLink) {
                        name = playerLink.textContent.trim();
                        break;
                    }
                    parent = parent.parentElement;
                }
                
                if (name) {
                    results.push({index: idx, name: name});
                }
            });
            
            return results;
        }""")
        
        if not icon_data:
            print(f"   No encoded list icons found")
            return
        
        print(f"   Found {len(icon_data)} encoded list icons")
        
        # Create a name-to-player lookup
        player_by_name = {p["name"].strip(): p for p in players}
        
        # Get all icons
        list_icons = await page.query_selector_all("img.logo[title='Encoded list']")
        
        for item in icon_data:
            icon_idx = item["index"]
            player_name = item["name"]
            
            if icon_idx >= len(list_icons):
                continue
            
            try:
                icon = list_icons[icon_idx]
                
                # Force click to bypass any overlays
                await icon.click(force=True)
                await page.wait_for_timeout(1000)
                
                # Extract XWS from the hidden textarea in #edit_player_list
                # This contains the full XWS JSON already formatted!
                xws_data = await page.evaluate("""() => {
                    // Get the XWS link first
                    let xws_link = null;
                    const linkSelectors = [
                        "a[href*='yasb.app']",
                        "a[href*='launchbaynext']"
                    ];
                    for (const sel of linkSelectors) {
                        const el = document.querySelector(sel);
                        if (el) {
                            xws_link = el.getAttribute('href');
                            break;
                        }
                    }
                    
                    // Try to get XWS from hidden textarea in #edit_player_list
                    const textarea = document.querySelector('#edit_player_list textarea');
                    let xwsJson = null;
                    if (textarea) {
                        try {
                            xwsJson = JSON.parse(textarea.value);
                        } catch (e) {
                            // Not valid JSON, continue with fallback
                        }
                    }
                    
                    // Parse faction from the link as fallback
                    let faction = null;
                    if (xws_link) {
                        const fMatch = xws_link.match(/[?&]f=([^&]+)/);
                        if (fMatch) faction = decodeURIComponent(fMatch[1]);
                    }
                    
                    // Extract squad name if present
                    let squadName = null;
                    if (xws_link) {
                        const snMatch = xws_link.match(/[?&]sn=([^&]+)/);
                        if (snMatch) squadName = decodeURIComponent(snMatch[1]);
                    }
                    
                    return {
                        link: xws_link,
                        faction: faction,
                        name: squadName,
                        xws: xwsJson  // Full XWS JSON from textarea
                    };
                }""")
                
                if xws_data and player_name in player_by_name:
                    player_by_name[player_name]["xws_link"] = xws_data.get("link")
                    
                    # If we got full XWS from textarea, use it directly
                    xws_json = xws_data.get("xws")
                    if xws_json:
                        # Add link to vendor section
                        if "vendor" not in xws_json:
                            xws_json["vendor"] = {}
                        xws_json["vendor"]["longshanks"] = {"link": xws_data.get("link")}
                        player_by_name[player_name]["xws"] = xws_json
                        pilot_count = len(xws_json.get("pilots", []))
                        print(f"   [OK] Got XWS for {player_name} ({pilot_count} pilots)")
                    else:
                        # Fallback: store basic info from URL
                        player_by_name[player_name]["xws"] = {
                            "faction": xws_data.get("faction"),
                            "name": xws_data.get("name"),
                            "vendor": {
                                "longshanks": {"link": xws_data.get("link")}
                            }
                        }
                        print(f"   [OK] Got XWS link for {player_name} (no full XWS)")
                
                # Close modal
                await page.keyboard.press("Escape")
                await page.wait_for_timeout(400)
                
            except Exception as e:
                # Try to recover
                try:
                    await page.keyboard.press("Escape")
                    await page.wait_for_timeout(200)
                except:
                    pass
                continue
                
    except Exception as e:
        print(f"Error extracting list links: {e}")



def _parse_faction(value: str) -> str | None:
    """Parse faction from image alt text or src."""
    value = value.lower()
    
    faction_map = {
        "rebel": "rebelalliance",
        "empire": "galacticempire",
        "scum": "scumandvillainy",
        "resistance": "resistance",
        "first order": "firstorder",
        "republic": "galacticrepublic",
        "separatist": "separatistalliance",
    }
    
    for key, faction in faction_map.items():
        if key in value:
            return faction
    
    return None


def _parse_date(date_str: str) -> datetime:
    """Parse date string with multiple formats."""
    if not date_str:
        return datetime.now()
    
    # Remove ordinal suffixes (1st, 2nd, 3rd, 4th)
    clean_str = re.sub(r"(\d+)(st|nd|rd|th)", r"\1", date_str.strip())
    
    # Handle ranges (e.g. "2026-01-10 – 2026-01-11")
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
            
    return datetime.now()


async def scrape_longshanks_history(subdomain: str = "xwing", max_pages: int = 1) -> list[dict[str, any]]:
    """
    Scrape tournament history from X-Wing Longshanks subdomains.
    
    Args:
        subdomain: "xwing" for 2.5, "xwing-legacy" for 2.0
        max_pages: Number of history pages to scrape
    
    Returns:
        List of tournament metadata dicts
    """
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        return []
    
    url = f"https://{subdomain}.longshanks.org/events/history/"
    tournaments = []
    game_format = "2.5" if subdomain == "xwing" else "2.0"
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        try:
            print(f"Scraping History: {url}")
            await page.goto(url, wait_until="networkidle", timeout=30000)
            await page.wait_for_timeout(2000)
            
            for page_num in range(max_pages):
                # Find all event cards
                cards = await page.query_selector_all(".event_display")
                
                for card in cards:
                    try:
                        # Name and ID from link
                        name_el = await card.query_selector(".event_name a")
                        if not name_el:
                            continue
                        
                        name = await name_el.inner_text()
                        href = await name_el.get_attribute("href")
                        
                        # Extract ID: /event/1234/
                        if "/event/" not in href:
                            continue
                        event_id = int(href.split("/event/")[1].split("/")[0])
                        
                        # Date
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
                        
                        # Player count
                        player_count = 0
                        p_text = await card.evaluate("""(card) => {
                            const img = card.querySelector('img[alt="Event size"]');
                            if (!img) return "";
                            const tr = img.closest('tr');
                            if (tr && tr.cells.length > 1) {
                                return tr.cells[1].textContent.trim();
                            }
                            return "";
                        }""")
                        
                        if p_text:
                            try:
                                # Handle "4 out of 30 players"
                                if "out of" in p_text.lower():
                                    player_count = int(p_text.split(" ")[0])
                                else:
                                    # Standard "30 players"
                                    # Use regex to find first number to be safe
                                    import re
                                    m = re.search(r'\d+', p_text)
                                    if m:
                                        player_count = int(m.group(0))
                            except:
                                pass
                        
                        tournaments.append({
                            "id": event_id,
                            "name": name.strip(),
                            "date": parsed_date,
                            "platform": "Longshanks",
                            "format": game_format,
                            "player_count": player_count,
                            "url": f"https://{subdomain}.longshanks.org{href}"
                        })
                        
                    except Exception:
                        continue
                
                # Try to go to next page if needed
                if page_num < max_pages - 1:
                    next_btn = await page.query_selector("a.next, .pagination a:has-text('Next')")
                    if next_btn:
                        await next_btn.click()
                        await page.wait_for_timeout(2000)
                    else:
                        break
                        
        except Exception as e:
            print(f"Error scraping history: {e}")
        finally:
            await page.close()
            await browser.close()
    
    return tournaments


async def fetch_xws_from_builder_link(link: str) -> dict[str, any] | None:
    """
    Parse a YASB or LaunchBayNext link to extract XWS data.
    
    YASB links encode the squad in the 'd' parameter.
    This requires a separate decoder or calling the builder API.
    """
    if not link:
        return None
    
    # For now, return the link as a reference
    # Full XWS parsing would require decoding YASB's format
    # or calling an API endpoint
    
    if "yasb" in link.lower():
        return {"builder": "yasb", "link": link}
    elif "launchbay" in link.lower():
        return {"builder": "launchbaynext", "link": link}
    
    return None
