"""
RollBetter Scraper for M3taCron.

RollBetter has an undocumented JSON API:
- GET /tournaments/{id} - Tournament metadata + rounds list
- GET /tournaments/{id}/players - Rankings with full squad lists
- GET /tournaments/{id}/rounds/{n} - Match pairings for round N

Also supports Playwright-based scraping for full XWS extraction (which the API lacks).
"""
import httpx
import json

from datetime import datetime

BASE_URL = "https://api.rollbetter.gg"


async def scrape_tournament(tournament_id: int, browser=None) -> dict[str, any] | None:
    """
    Scrape a Rollbetter tournament using Playwright.
    
    Extracts full XWS from the Lists tab where each player has
    a "Copy XWS to Clipboard" button.
    
    Args:
        tournament_id: Rollbetter tournament ID
        browser: Optional Playwright browser instance
        
    Returns:
        Dict with tournament info and players with XWS
    """
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        raise ImportError("Playwright required: pip install playwright && playwright install")
    
    url = f"https://rollbetter.gg/tournaments/{tournament_id}/lists"
    
    async def _scrape(browser_instance):
        context = await browser_instance.new_context()
        page = await context.new_page()
        
        try:
            await page.goto(url, wait_until="networkidle", timeout=30000)
            await page.wait_for_timeout(2000)
            
            # Get tournament name
            tournament_name = await page.evaluate("""() => {
                const h1 = document.querySelector('h1');
                return h1 ? h1.textContent.trim() : 'Unknown Tournament';
            }""")
            
            # Extract all XWS data using JavaScript
            # Each player card has a hidden XWS that gets copied to clipboard
            players_data = await page.evaluate("""() => {
                const results = [];
                
                // Find all player cards/rows in the lists view
                const cards = document.querySelectorAll('[class*="PlayerListCard"], [class*="player"], .list-card');
                
                // Also try to find buttons that copy XWS
                const copyButtons = document.querySelectorAll('button');
                
                // Method 1: Look for data in React state or component props
                // Rollbetter uses React, so data might be in __reactProps
                const findXWSInElement = (el) => {
                    const text = el.innerText || '';
                    const props = el.__reactProps || {};
                    return { text, hasProps: Object.keys(props).length > 0 };
                };
                
                // Method 2: Parse visible content for each player
                // Look for elements containing faction/pilot info
                const factionDivs = document.querySelectorAll('[class*="faction"], [class*="list-header"]');
                
                // For now, return info about what we found
                return {
                    cardsFound: cards.length,
                    buttonsFound: copyButtons.length,
                    factionDivsFound: factionDivs.length,
                    pageText: document.body.innerText.substring(0, 2000)
                };
            }""")
            
            # Try to intercept the XWS by triggering copy buttons
            xws_list = await page.evaluate("""async () => {
                const results = [];
                
                // Find all "Copy XWS to Clipboard" buttons
                const buttons = Array.from(document.querySelectorAll('button'))
                    .filter(b => b.textContent.includes('Copy XWS'));
                
                // For each button, we need to intercept what it copies
                const originalWriteText = navigator.clipboard.writeText;
                let lastCopied = null;
                
                navigator.clipboard.writeText = async (text) => {
                    lastCopied = text;
                    return Promise.resolve();
                };
                
                for (let i = 0; i < buttons.length; i++) {
                    const btn = buttons[i];
                    lastCopied = null;
                    
                    // Find player name near this button
                    let playerName = 'Unknown';
                    let parent = btn.parentElement;
                    for (let j = 0; j < 10 && parent; j++) {
                        const nameEl = parent.querySelector('h3, h4, [class*="name"], [class*="Name"]');
                        if (nameEl) {
                            playerName = nameEl.textContent.trim();
                            break;
                        }
                        parent = parent.parentElement;
                    }
                    
                    try {
                        btn.click();
                        await new Promise(r => setTimeout(r, 100));
                        
                        if (lastCopied) {
                            try {
                                const xws = JSON.parse(lastCopied);
                                results.push({
                                    name: playerName,
                                    xws: xws
                                });
                            } catch (e) {
                                // Not valid JSON
                            }
                        }
                    } catch (e) {
                        // Button click failed
                    }
                }
                
                navigator.clipboard.writeText = originalWriteText;
                return results;
            }""")
            
            # Build player results
            players = []
            for i, item in enumerate(xws_list):
                players.append({
                    "rank": i + 1,
                    "name": item.get("name", f"Player {i+1}"),
                    "xws": item.get("xws")
                })
            
            return {
                "tournament": {
                    "name": tournament_name,
                    "platform": "Rollbetter",
                    "url": url,
                },
                "players": players,
                "debug": players_data
            }
        finally:
            await page.close()
            await context.close()

    if browser:
        return await _scrape(browser)
    else:
        async with async_playwright() as p:
            browser_instance = await p.chromium.launch(headless=True)
            try:
                return await _scrape(browser_instance)
            finally:
                await browser_instance.close()


async def fetch_tournament(tournament_id: int) -> dict[str, any] | None:
    """
    Fetch tournament metadata from RollBetter API.
    """
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(f"{BASE_URL}/tournaments/{tournament_id}")
        if response.status_code == 404 or response.status_code == 500:
            return None
        response.raise_for_status()
        data = response.json()
        
        if "name" not in data and "title" in data:
            data["name"] = data["title"]
            
        return data


async def fetch_players(tournament_id: int) -> list[dict[str, any]]:
    """
    Fetch player rankings and squad lists from API.
    Note: These lists might be simplified (missing pilots/upgrades).
    """
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(f"{BASE_URL}/tournaments/{tournament_id}/players")
        if response.status_code != 200:
            return []
        data = response.json()
        if isinstance(data, list):
            return data
        return data.get("players", data.get("ladder", []))


async def fetch_round_matches(tournament_id: int, round_number: int) -> list[dict[str, any]]:
    """
    Fetch match pairings for a specific round from API.
    """
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(
            f"{BASE_URL}/tournaments/{tournament_id}/rounds/{round_number}"
        )
        if response.status_code != 200:
            return []
        data = response.json()
        
        # 2026 Update: API returns a list of round objects for some endpoints
        # [ { "roundNumber": 1, "pairings": [...] } ]
        if isinstance(data, list) and len(data) > 0 and "pairings" in data[0]:
            return data[0].get("pairings", [])
            
        if isinstance(data, list):
            return data
        return data.get("matches", data.get("pairings", data.get("games", [])))


def extract_xws_from_player(player: dict[str, any]) -> dict[str, any] | None:
    """
    Extract XWS data from a RollBetter player record (API response).
    """
    # Try different possible field names
    squad = player.get("squad") or player.get("xws")
    
    # Check 'list' field first - this is the ListFortress export format
    list_data = player.get("list")
    if list_data and isinstance(list_data, str) and list_data.strip():
        try:
            parsed = json.loads(list_data)
            if isinstance(parsed, dict) and ("faction" in parsed or "pilots" in parsed):
                return parsed
        except json.JSONDecodeError:
            pass
    
    # 2026 Update: simplify API format
    if not squad and "lists" in player and isinstance(player["lists"], list) and len(player["lists"]) > 0:
        squad_entry = player["lists"][0]
        squad = squad_entry.get("raw") or squad_entry.get("json") or squad_entry
        
    if not squad:
        return None
    
    if isinstance(squad, dict):
        if "faction" in squad or "pilots" in squad:
            return squad
    
    if isinstance(squad, str):
        try:
            parsed = json.loads(squad)
            if isinstance(parsed, dict) and ("faction" in parsed or "pilots" in parsed):
                return parsed
        except json.JSONDecodeError:
            pass
    
    return None



def parse_listfortress_export(export_data: dict[str, any]) -> list[dict[str, any]]:
    """
    Parse data from Rollbetter's "Export to ListFortress" format.
    
    This is the preferred method when you have the export JSON.
    Contains full XWS in the 'list' field of each player.
    
    Args:
        export_data: The parsed JSON from the ListFortress export
        
    Returns:
        List of player dicts with extracted XWS
    """
    results = []
    players = export_data.get("players", [])
    
    for p in players:
        player_data = {
            "name": p.get("name"),
            "rank": p.get("rank", {}).get("swiss") if isinstance(p.get("rank"), dict) else p.get("rank"),
            "score": p.get("score"),
            "sos": p.get("sos"),
            "mov": p.get("mov"),
            "dropped": p.get("dropped", False),
        }
        
        # Parse the 'list' field which contains full XWS as JSON string
        list_str = p.get("list", "")
        if list_str and isinstance(list_str, str):
            try:
                xws = json.loads(list_str)
                player_data["xws"] = xws
            except json.JSONDecodeError:
                player_data["xws"] = None
        else:
            player_data["xws"] = None
            
        results.append(player_data)
    
    return results

