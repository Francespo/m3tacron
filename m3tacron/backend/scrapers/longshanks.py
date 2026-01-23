"""
Longshanks Scraper Implementation (Playwright).

Supports X-Wing 2.5 (xwing.longshanks.org) and Legacy 2.0 (xwing-legacy.longshanks.org).
Extracts tournament data, player results with XWS, and match data.
"""
import logging
import re
from datetime import datetime

from playwright.sync_api import sync_playwright

# Local Imports
from .base import BaseScraper
from ..models import Tournament, PlayerResult, Match
from ..data_structures.formats import Format, infer_format_from_xws
from ..data_structures.factions import Faction
from ..data_structures.platforms import Platform
from ..data_structures.round_types import RoundType
from ..data_structures.scenarios import Scenario

logger = logging.getLogger(__name__)

# History URLs for reference
XWING_25_HISTORY = "https://xwing.longshanks.org/events/history/"
XWING_20_HISTORY = "https://xwing-legacy.longshanks.org/events/history/"


class LongshanksScraper(BaseScraper):
    """
    Scraper for Longshanks tournaments using sync Playwright.
    
    Supports both X-Wing 2.5 and Legacy 2.0 via the subdomain parameter.
    """
    
    def __init__(self, subdomain: str = "xwing"):
        """
        Initialize scraper with subdomain.
        
        Args:
            subdomain: "xwing" for 2.5, "xwing-legacy" for 2.0
        """
        self.subdomain = subdomain
        self.base_url = f"https://{subdomain}.longshanks.org"
    
    def _dismiss_cookie_popup(self, page) -> None:
        """Dismiss cookie consent popup if present."""
        try:
            cookie_popup = page.query_selector("#cookie_permission")
            if cookie_popup:
                accept_btn = page.query_selector(
                    "#cookie_permission button, #cookie_permission a.accept"
                )
                if accept_btn:
                    accept_btn.click()
                    page.wait_for_timeout(500)
                else:
                    # Hide via JavaScript
                    page.evaluate("""() => {
                        const popup = document.getElementById('cookie_permission');
                        if (popup) popup.style.display = 'none';
                    }""")
        except Exception:
            pass
    
    def _parse_date(self, date_str: str) -> datetime:
        """Parse date string with multiple formats."""
        if not date_str:
            return datetime.now()
        
        # Remove ordinal suffixes (1st, 2nd, 3rd, 4th)
        clean_str = re.sub(r"(\d+)(st|nd|rd|th)", r"\1", date_str.strip())
        
        # Handle date ranges (e.g. "2026-01-10 – 2026-01-11")
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
    
    def _parse_faction(self, value: str) -> str | None:
        """Parse faction from image alt/src."""
        faction = Faction.from_xws(value)
        return faction.value if faction != Faction.UNKNOWN else None
    
    def get_tournament_data(self, tournament_id: str) -> Tournament:
        """
        Scrape high-level tournament metadata.
        """
        url = f"{self.base_url}/event/{tournament_id}/"
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            try:
                page.goto(url, wait_until="networkidle", timeout=30000)
                page.wait_for_timeout(2000)
                
                self._dismiss_cookie_popup(page)
                
                # Scrape Title from h1
                name_el = page.query_selector("h1")
                name = name_el.inner_text().strip() if name_el else f"Longshanks Event {tournament_id}"
                
                # Extract date and player count from event info table
                event_info = page.evaluate("""() => {
                    let dateStr = '';
                    let playerCount = 0;
                    
                    const rows = document.querySelectorAll('tr');
                    for (const row of rows) {
                        const img = row.querySelector('img');
                        const cells = row.querySelectorAll('td');
                        if (!img || cells.length < 2) continue;
                        
                        const alt = img.alt || '';
                        const value = cells[1]?.textContent?.trim() || '';
                        
                        // Event size (e.g. "17 players" or "28 of 36 players")
                        if (alt === 'Event size' || value.includes('player')) {
                            const outOfMatch = value.match(/(\d+)\s*(?:out\s+)?of\s+\d+/i);
                            if (outOfMatch) {
                                playerCount = parseInt(outOfMatch[1], 10);
                            } else {
                                const match = value.match(/(\d+)\s*player/i);
                                if (match) playerCount = parseInt(match[1], 10);
                            }
                        }
                        
                        // Date
                        if (alt === 'Date' || value.match(/\\d{4}-\\d{2}-\\d{2}/)) {
                            if (!dateStr) dateStr = value;
                        }
                    }
                    
                    return { dateStr, playerCount };
                }""")
                
                parsed_date = self._parse_date(event_info.get("dateStr", ""))
                player_count = event_info.get("playerCount", 0)
                
                # Determine format based on subdomain
                game_format = Format.XWA if self.subdomain == "xwing" else Format.LEGACY_X2PO
                
                return Tournament(
                    id=int(tournament_id),
                    name=name,
                    date=parsed_date.date(),
                    format=game_format,
                    player_count=player_count,
                    platform=Platform.LONGSHANKS,
                    url=url
                )
            except Exception as e:
                logger.error(f"Failed to scrape tournament {tournament_id}: {e}")
                raise
            finally:
                browser.close()
    
    def get_participants(self, tournament_id: str) -> list[PlayerResult]:
        """
        Scrape players and their lists.
        """
        url = f"{self.base_url}/event/{tournament_id}/"
        participants: list[PlayerResult] = []
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            try:
                page.goto(url, wait_until="networkidle", timeout=30000)
                page.wait_for_timeout(2000)
                
                self._dismiss_cookie_popup(page)
                
                # Check for Squad Tournament and switch to individual players tab
                try:
                    # Look for "Team results" tab or "Load standings" with player arg
                    squad_tab = page.locator("a[onclick*=\"load_standings('player')\"]").first
                    if squad_tab.count() > 0 and squad_tab.is_visible():
                         logger.info("Squad Tournament detected: Switching to Individual Players tab")
                         squad_tab.click()
                         page.wait_for_load_state("networkidle")
                         page.wait_for_timeout(2000) # Wait for AJAX load
                         page.wait_for_selector(".player:not(.accordion), .ranking_row", timeout=5000)
                except Exception as e:
                    logger.warning(f"Failed to check/switch squad tabs: {e}")

                # Extract player data from div.player elements (Longshanks uses divs, not tables)
                player_data = page.evaluate("""() => {
                    const results = [];
                    const seenNames = new Set();
                    // Longshanks uses div.player for each player row (or ranking_row for AJAX loaded)
                    const players = document.querySelectorAll('.player:not(.accordion), .ranking_row');
                    
                    players.forEach((playerEl) => {
                        // Rank is in div.rank
                        const rankEl = playerEl.querySelector('.rank');
                        const rank = rankEl ? parseInt(rankEl.textContent.trim()) : 0;
                        if (isNaN(rank) || rank === 0) return;
                        
                        // Data is in div.data with child divs for each field
                        const dataEl = playerEl.querySelector('.data');
                        if (!dataEl) return;
                        
                        const children = dataEl.children;
                        
                        // Name is in first child (div.name), inside .player_link or direct text
                        let name = '';
                        const nameDiv = children[0];
                        // Extract External ID and Name
                        let external_id = null;
                        if (nameDiv) {
                            const link = nameDiv.querySelector('.player_link, a');
                            if (link) {
                                const clone = link.cloneNode(true);
                                clone.querySelectorAll('span').forEach(s => s.remove());
                                name = clone.textContent.trim();
                                
                                // ID
                                if (link.href) {
                                    const parts = link.href.split('/');
                                    const numeric = parts.filter(p => !isNaN(parseInt(p)) && p.length > 0);
                                    if (numeric.length > 0) external_id = numeric[numeric.length - 1];
                                }
                            } else {
                                name = nameDiv.textContent.trim();
                            }
                            // Clean player ID suffix like "#13326"
                            name = name.replace(/\\s*#\\d+$/, '').trim();
                        }
                        
                        if (!name || seenNames.has(name)) return;
                        seenNames.add(name);
                        
                        // W/L/D is in a child with class 'stat mono' (usually index 5)
                        // Format: "3 / 0" or "3 / 0 / 0"
                        let wins = 0, losses = 0, draws = 0;
                        for (let i = 4; i < children.length; i++) {
                            const text = children[i].textContent.trim();
                            // Match "3 / 0 / 0" or "3 / 0"
                            const wldMatch = text.match(/(\\d+)\\s*\\/\\s*(\\d+)(?:\\s*\\/\\s*(\\d+))?/);
                            if (wldMatch) {
                                wins = parseInt(wldMatch[1]) || 0;
                                losses = parseInt(wldMatch[2]) || 0;
                                draws = wldMatch[3] ? parseInt(wldMatch[3]) : 0;
                                break;
                            }
                        }
                        
                        // TP (Tournament Points) is in a child with class containing 'skinny' (index 4)
                        let points = 0;
                        for (let i = 3; i < children.length; i++) {
                            if (children[i].classList.contains('skinny')) {
                                const pMatch = children[i].textContent.match(/\\d+/);
                                if (pMatch) points = parseInt(pMatch[0]) || 0;
                                break;
                            }
                        }
                        
                        // Check for encoded list icon in factions div
                        const hasListIcon = !!playerEl.querySelector("img[title='Encoded list']");
                        
                        // Faction from image
                        const factionImg = playerEl.querySelector('.factions img.faction, .factions img');
                        let faction = null;
                        if (factionImg) {
                            faction = factionImg.alt || factionImg.src || null;
                        }
                        
                        results.push({
                            name: name,
                            external_id: external_id,
                            rank: rank,
                            faction: faction,
                            wins: wins,
                            losses: losses,
                            draws: draws,
                            points: points,
                            hasListIcon: hasListIcon
                        });
                    });
                    
                    return results;
                }""")
                
                logger.info(f"Found {len(player_data)} players in results table")
                
                # Build participants list
                for p_data in player_data:
                    pr = PlayerResult(
                        tournament_id=int(tournament_id),
                        player_name=p_data["name"],
                        rank=p_data["rank"],
                        swiss_rank=p_data["rank"],
                        swiss_wins=p_data["wins"],
                        swiss_losses=p_data["losses"],
                        swiss_draws=p_data["draws"],
                        points_at_event=p_data["points"],
                        list_json={}
                    )
                    # Attach external_id dynamically (not in model)
                    if p_data.get("external_id"):
                        pr.external_id = str(p_data["external_id"])
                    
                    participants.append(pr)
                
                # Extract XWS from encoded list icons
                self._extract_lists_from_icons(page, participants, tournament_id)
                
            except Exception as e:
                logger.error(f"Error scraping participants: {e}")
            finally:
                browser.close()
        
        return participants
    
    def _extract_lists_from_icons(self, page, participants: list[PlayerResult], tournament_id: str) -> None:
        """
        Extract XWS data by calling Longshanks's pop_user() JS function.
        
        Longshanks loads XWS into textarea#list_<player_id> when pop_user() is called.
        """
        try:
            # Get player IDs and names from encoded list icons
            player_ids = page.evaluate("""() => {
                const results = [];
                const icons = document.querySelectorAll("img[title='Encoded list']");
                
                icons.forEach(icon => {
                    // The icon's onclick has the player_id: pop_user(13326, 30230, 'list')
                    const onclick = icon.getAttribute('onclick') || '';
                    const match = onclick.match(/pop_user\\((\\d+),/);
                    if (!match) return;
                    
                    const playerId = match[1];
                    
                    // Get player name from parent .player div
                    let name = null;
                    const playerDiv = icon.closest('.player');
                    if (playerDiv) {
                        const dataEl = playerDiv.querySelector('.data');
                        if (dataEl && dataEl.children[0]) {
                            const link = dataEl.children[0].querySelector('.player_link, a');
                            name = link ? link.textContent.trim() : dataEl.children[0].textContent.trim();
                            name = name.replace(/\\s*#\\d+$/, '').trim();
                        }
                    }
                    
                    if (name && playerId) {
                        results.push({id: playerId, name: name});
                    }
                });
                
                return results;
            }""")
            
            if not player_ids:
                logger.info("No players with encoded list icons found")
                return
            
            logger.info(f"Found {len(player_ids)} players with encoded lists")
            
            # Name-to-participant lookup
            participant_by_name = {p.player_name: p for p in participants}
            
            extracted_count = 0
            for player in player_ids:
                player_id = player["id"]
                player_name = player["name"]
                
                if player_name not in participant_by_name:
                    logger.debug(f"Player '{player_name}' not found in participants")
                    continue
                
                try:
                    # Call pop_user to load the XWS data
                    xws_data = page.evaluate(f"""async () => {{
                        // Trigger the popup/data load
                        pop_user({player_id}, {tournament_id}, 'list');
                        
                        // Wait for textarea to be populated (up to 2 seconds)
                        for (let i = 0; i < 50; i++) {{
                            await new Promise(r => setTimeout(r, 100));
                            const textarea = document.querySelector('textarea#list_{player_id}');
                            if (textarea && textarea.value) {{
                                try {{
                                    const xws = JSON.parse(textarea.value);
                                    
                                    // Also get YASB/LBN link if present
                                    let link = null;
                                    const yasb = document.querySelector("a[href*='yasb.app']");
                                    const lbn = document.querySelector("a[href*='launchbaynext']");
                                    if (yasb) link = yasb.getAttribute('href');
                                    else if (lbn) link = lbn.getAttribute('href');
                                    
                                    return {{ xws: xws, link: link }};
                                }} catch (e) {{
                                    return {{ error: 'parse', value: textarea.value.substring(0, 100) }};
                                }}
                            }}
                        }}
                        return {{ error: 'timeout' }};
                    }}""")
                    
                    if xws_data and "xws" in xws_data:
                        xws_json = xws_data["xws"]
                        # Add vendor info
                        if "vendor" not in xws_json:
                            xws_json["vendor"] = {}
                        xws_json["vendor"]["longshanks"] = {"link": xws_data.get("link")}
                        participant_by_name[player_name].list_json = xws_json
                        extracted_count += 1
                        logger.debug(f"Got XWS for {player_name} ({len(xws_json.get('pilots', []))} pilots)")
                    elif xws_data and xws_data.get("link"):
                        # Store link reference only
                        participant_by_name[player_name].list_json = {
                            "vendor": {"longshanks": {"link": xws_data.get("link")}}
                        }
                    else:
                        logger.debug(f"No XWS data for {player_name}: {xws_data}")
                    
                    # Close modal (press Escape)
                    page.keyboard.press("Escape")
                    page.wait_for_timeout(100)
                    
                except Exception as e:
                    logger.debug(f"Error extracting list for {player_name}: {e}")
                    try:
                        page.keyboard.press("Escape")
                    except:
                        pass
            
            logger.info(f"Extracted {extracted_count} XWS lists")
            
        except Exception as e:
            logger.error(f"Error extracting list links: {e}")
    
    def get_matches(self, tournament_id: str) -> list[Match]:
        """
        Scrape matches from the Games tab, handling pagination via round selector.
        """
        url = f"{self.base_url}/event/{tournament_id}/"
        matches: list[Match] = []
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            try:
                page.goto(url, wait_until="networkidle", timeout=30000)
                
                # Kill cookie popup aggressively
                page.add_style_tag(content="#cookie_permission { display: none !important; }")
                page.wait_for_timeout(1000)
                
                # Click Games tab
                games_tab = page.query_selector("#tab_games, a[href='#tab_games'], button:has-text('Games')")
                if not games_tab:
                    logger.warning("No Games tab found")
                    return []
                
                games_tab.click()
                page.wait_for_timeout(2000)
                
                # Get all round values from selector logic
                # Longshanks loads matches via AJAX when selector changes
                round_values = page.evaluate("""() => {
                    const sel = document.querySelector('#round_selector');
                    if (!sel) return [];
                    return Array.from(sel.options).map(o => o.value);
                }""")
                
                if not round_values:
                    # Fallback if no selector (single round or loaded straight)
                    round_values = ["current"]
                
                logger.info(f"Found {len(round_values)} rounds to scrape: {round_values}")
                
                processed_rounds = set()

                for r_val in round_values:
                    if r_val != "current":
                        # Select the round
                        page.select_option("#round_selector", r_val)
                        
                        # Dispatch change event explicitly for some browsers/JS frameworks
                        page.evaluate("document.querySelector('#round_selector').dispatchEvent(new Event('change'))")
                        
                        # Remove Cookie Banner aggresively
                        page.evaluate("const c=document.getElementById('cookie_permission'); if(c) c.remove();")
                        
                        # Wait for the table/divs to update
                        # Ideally wait for a specific element that confirms the round loaded
                        # We wait for the 'details' header to likely match our round if possible, or just a hard wait + network idle
                        page.wait_for_timeout(500)
                        try:
                            page.wait_for_load_state("networkidle", timeout=3000)
                            # Wait for at least one match item to appear to ensure we aren't scraping empty states
                            page.wait_for_selector(".item", timeout=3000)
                        except:
                            pass
                            
                        # Double check we have content
                        page.wait_for_timeout(1000)
                    
                    # Scrape the currently visible matches
                    # Squad Extraction Logic
                    # Squad Extraction Logic
                    # Squad Extraction Logic
                    # Ensure content is loaded
                    try:
                        page.wait_for_selector(".game, .match, .details", timeout=2000)
                    except:
                        pass
                    
                    squad_locators = page.locator("a.game_tab")
                    count = squad_locators.count()
                    round_matches_data = []
                    
                    if count > 0:
                        logger.info(f"Squad Mode: Found {count} team matches in round {r_val}")
                        # Inject CSS to hide cookie banner permanently
                        page.add_style_tag(content="#cookie_permission { display: none !important; visibility: hidden !important; }")
                        
                        for i in range(count):
                            try:
                                btn = squad_locators.nth(i)
                                
                                # Get onclick attribute to bypass click issues
                                onclick_attr = btn.get_attribute("onclick")
                                match_id = None
                                if onclick_attr:
                                    import re
                                    m = re.search(r"pop_open\('([^']+)'\)", onclick_attr)
                                    if m:
                                        match_id = m.group(1)
                                
                                if match_id:
                                    logger.info(f"Invoking squad match via JS: {match_id}")
                                    page.evaluate(f"pop_open('{match_id}')")
                                    page.wait_for_timeout(500)
                                else:
                                    # Fallback to click if no ID found
                                    logger.warning("No pop_open ID found, falling back to click")
                                    btn.click(force=True)
                                
                                # Wait for modal with retry
                                try:
                                    page.wait_for_selector(".popframe", timeout=3000)
                                except:
                                    logger.warning("Modal timeout, retrying via click")
                                    btn.click(force=True)
                                    page.wait_for_selector(".popframe", timeout=3000)
                                    
                                page.wait_for_timeout(200)
                                
                                # Extract from modal (using previously fixed logic)
                                sub_matches = page.evaluate("""() => {
                                    const modal = document.querySelector('.popframe');
                                    if (!modal) return [];
                                    const matches = [];
                                    const items = modal.querySelectorAll('.game, .item'); 
                                    items.forEach(item => {
                                        const pLinks = item.querySelectorAll('.player_link');
                                        const scores = item.querySelectorAll('.score.vp');
                                        if (pLinks.length >= 2) {
                                            const p1 = pLinks[0].textContent.trim().replace(/\\s*#\\d+$/, '');
                                            const p2 = pLinks[1].textContent.trim().replace(/\\s*#\\d+$/, '');
                                            const s1 = scores[0] ? parseInt(scores[0].textContent) || 0 : 0;
                                            const s2 = scores[1] ? parseInt(scores[1].textContent) || 0 : 0;
                                            
                                            let p1Id = null, p2Id = null;
                                            
                                            const getId = (link) => {
                                                const onclick = link.getAttribute('onclick');
                                                if (onclick) {
                                                    const m = onclick.match(/pop_user\\((\\d+)/);
                                                    if (m) return m[1];
                                                }
                                                if (link.parentElement) {
                                                    const span = link.parentElement.querySelector('.id_number');
                                                    if (span) return span.innerText.replace('#','').trim();
                                                }
                                                if (link.href && link.href.includes('/player/')) {
                                                    const parts = link.href.split('/');
                                                    const nums = parts.filter(p => !isNaN(parseInt(p)) && p.length > 0);
                                                    if (nums.length) return nums[nums.length-1];
                                                }
                                                return null;
                                            };
                                            
                                            p1Id = getId(pLinks[0]);
                                            p2Id = getId(pLinks[1]);
                                            matches.push({p1, p2, p1_id: p1Id, p2_id: p2Id, s1, s2});
                                        }
                                    });
                                    return matches;
                                }""")
                                
                                current_round_num = int(r_val) if r_val.lstrip('-').isdigit() else 1
                                
                                for sm in sub_matches:
                                    logger.debug(f"Squad Sub-Match: {sm['p1']} ({sm['p1_id']}) vs {sm['p2']} ({sm['p2_id']})")
                                    round_matches_data.append({
                                        'round': current_round_num,
                                        'type': 'swiss',
                                        'p1': sm['p1'], 'p2': sm['p2'],
                                        'p1_id': sm['p1_id'], 'p2_id': sm['p2_id'],
                                        's1': sm['s1'], 's2': sm['s2'],
                                        'bye': False, 'first_player_index': None, 'scenario': None
                                    })
                                
                                # Close modal - Explicitly click Close button if possible
                                close_btn = page.locator(".button_close")
                                if close_btn.is_visible():
                                    close_btn.click(force=True)
                                else:
                                    page.keyboard.press("Escape")
                                
                                # Wait for modal to disappear
                                page.wait_for_timeout(500)
                                
                            except Exception as e:
                                logger.warning(f"Error scraping squad match {i}: {e}")
                                try: page.keyboard.press("Escape")
                                except: pass
                    
                    if not round_matches_data:

                        round_matches_data = page.evaluate("""() => {
                        const extracted = [];
                        const headers = document.querySelectorAll('.details');
                        
                        headers.forEach(header => {
                            if (!/(Round|Top|Cut|Final)/i.test(header.innerText)) return;
                            
                            // Parse Round Header (Round X, Round C2, Top 8, Final)
                            const headerText = header.innerText;
                            const rMatch = headerText.match(/(Round|Top|Cut|Final)\\s+([A-Za-z0-9]+)/i);
                            let roundNum = 1;
                            let roundType = "swiss";
                            
                            if (rMatch) {
                                        const d = val.match(/\\d+/);
                                        roundNum = d ? parseInt(d[0]) : 1;
                                    }
                                }
                            }
                            
                            // The players are in the SIBLING .results div (or next-next)
                            // Structure: .details -> .results
                            let next = header.nextElementSibling;
                            while (next && !next.classList.contains('details') && !next.classList.contains('footer')) {
                                if (next.classList.contains('results')) {
                                    // In div layout, players are children of .results
                                    const pLinks = next.querySelectorAll('.player_link');
                                    const scores = next.querySelectorAll('.score.vp');
                                    
                                    if (pLinks.length >= 2) {
                                        const p1 = pLinks[0].textContent.trim().replace(/\s*#\d+$/, '');
                                        const p2 = pLinks[1].textContent.trim().replace(/\s*#\d+$/, '');
                                        const s1 = scores[0] ? parseInt(scores[0].textContent) || 0 : 0;
                                        const s2 = scores[1] ? parseInt(scores[1].textContent) || 0 : 0;
                                        
                                        // IDs
                                        let p1Id = null;
                                        let p2Id = null;
                                        
                                        if (pLinks[0].href) {
                                            const parts = pLinks[0].href.split('/');
                                            const nums = parts.filter(p => !isNaN(parseInt(p)) && p.length > 0);
                                            if (nums.length) p1Id = nums[nums.length-1];
                                        }
                                        if (pLinks[1].href) {
                                            const parts = pLinks[1].href.split('/');
                                            const nums = parts.filter(p => !isNaN(parseInt(p)) && p.length > 0);
                                            if (nums.length) p2Id = nums[nums.length-1];
                                        }
                                        
                                        // First Player (Legacy/2.0)
                                        // Look for img with title='First player'
                                        // It is usually a sibling of the player link or score.
                                        // We assume DOM order: P1, Score, P2.
                                        // If icon is before the middle (scores), it's P1.
                                        let firstPlayerIndex = null; // 0 or 1
                                        const fpIcon = next.querySelector("img[title='First player']");
                                        if (fpIcon) {
                                            // Check position relative to P2 Link
                                            // compareDocumentPosition: 2 (preceding), 4 (following)
                                            // If fpIcon follows P1 Link and precedes P2 Link -> P1?
                                            // Or if fpIcon is inside P1 block.
                                            
                                        // Robust check: Is it before P2 Link?
                                            // The compareDocumentPosition check in JS returns a bitmask.
                                            // 4 means "followed by" (Node A follows Node B? No, Node.DOCUMENT_POSITION_FOLLOWING means other node follows reference node)
                                            // Actually, simplest is: Is the icon logically closer to P1 block?
                                            // If fpIcon is document-preceding P2, it is P1.
                                            // The bitmask for "node A (fpIcon) precedes node B (pLinks[1])" is 4 (DOCUMENT_POSITION_FOLLOWING... wait, definitions are tricky).
                                            // Let's use containment if possible, or Order.
                                            if (fpIcon.compareDocumentPosition(pLinks[1]) & Node.DOCUMENT_POSITION_PRECEDING) {
                                                // fpIcon COMES AFTER P2 (Preceding means P2 precedes fpIcon? No.)
                                                // 2 (PRECEDING): The other node precedes the reference node. 
                                                // So pLinks[1] precedes fpIcon -> Icon is AFTER P2 -> P2 is First
                                                 firstPlayerIndex = 1;
                                            } else {
                                                // Icon is BEFORE P2 -> P1 is First
                                                firstPlayerIndex = 0;
                                            }
                                        } else {
                                           // Fallback: Check for "star" text (*) in scores or player blocks
                                           // User report: "First player has one star, second has two" (or similar notation)
                                           // Check if scores text contains '*'
                                           const scores = next.querySelectorAll('.score');
                                           if (scores.length >= 2) {
                                               const t1 = scores[0].innerText;
                                               const t2 = scores[1].innerText;
                                               if (t1.includes('*') && !t2.includes('*')) firstPlayerIndex = 0;
                                               else if (!t1.includes('*') && t2.includes('*')) firstPlayerIndex = 1;
                                               // Check player names too
                                               else {
                                                   const n1 = pLinks[0].parentElement.innerText;
                                                   const n2 = pLinks[1].parentElement.innerText;
                                                   if (n1.includes('*') && !n2.includes('*')) firstPlayerIndex = 0;
                                                   else if (!n1.includes('*') && n2.includes('*')) firstPlayerIndex = 1;
                                               }
                                           }
                                        }
                                        
                                        // Scenario (XWA/2.5)
                                        // Look for "Scenario" in the NEXT sibling (.details)
                                        let scenarioName = null;
                                        const scenarioContainer = next.nextElementSibling;
                                        if (scenarioContainer && scenarioContainer.classList.contains('details')) {
                                            // Check text content of items in this details div
                                            const items = scenarioContainer.querySelectorAll('.item');
                                            for (const item of items) {
                                                if (item.textContent.trim().startsWith("Scenario")) {
                                                    const sSpan = item.querySelector('span[title]');
                                                    if (sSpan) scenarioName = sSpan.textContent.trim();
                                                    break;
                                                }
                                            }
                                        }

                                        extracted.push({
                                            round: roundNum,
                                            type: roundType,
                                            p1: p1,
                                            p2: p2,
                                            p1_id: p1Id,
                                            p2_id: p2Id,
                                            s1: s1,
                                            s2: s2,
                                            bye: false,
                                            first_player_index: firstPlayerIndex,
                                            scenario: scenarioName
                                        });
                                        
                                    } else if (pLinks.length === 1) {
                                        // BYE
                                        const p1 = pLinks[0].textContent.trim().replace(/\s*#\d+$/, '');
                                        const s1 = scores[0] ? parseInt(scores[0].textContent) || 0 : 0;
                                        
                                        let p1Id = null;
                                        if (pLinks[0].href) {
                                            const parts = pLinks[0].href.split('/');
                                            const nums = parts.filter(p => !isNaN(parseInt(p)) && p.length > 0);
                                            if (nums.length) p1Id = nums[nums.length-1];
                                        }
                                        
                                        extracted.push({
                                            round: roundNum,
                                            type: roundType,
                                            p1: p1,
                                            p2: 'BYE',
                                            p1_id: p1Id,
                                            p2_id: null,
                                            s1: s1,
                                            s2: 0,
                                            bye: true
                                        });
                                    }
                                }
                                next = next.nextElementSibling;
                            }
                        });
                        return extracted;
                    }""")
                    
                    # Scenario Propagation: Backfill scenario for rounds
                    # Find consistent scenario per round
                    round_scenarios = {}
                    for rm in round_matches_data:
                        r_key = rm['round']
                        if rm.get('scenario') and r_key not in round_scenarios:
                            round_scenarios[r_key] = rm['scenario']
                            
                    # Backfill
                    for rm in round_matches_data:
                        r_key = rm['round']
                        if not rm.get('scenario') and r_key in round_scenarios:
                            rm['scenario'] = round_scenarios[r_key]

                    for rm in round_matches_data:
                        # Unique check (round + p1)
                        unique_key = (rm['round'], rm['type'], rm['p1'])
                        if unique_key in processed_rounds:
                            continue
                        processed_rounds.add(unique_key)
                        
                        # Map string to Enum (safety)
                        r_type_enum = RoundType.SWISS
                        if rm['type'] == 'cut': r_type_enum = RoundType.CUT
                        
                        m = Match(
                            tournament_id=int(tournament_id),
                            round_number=rm['round'],
                            round_type=r_type_enum,
                            player1_id=0, player2_id=0, winner_id=0,
                            player1_score=rm['s1'],
                            player2_score=rm['s2'],
                            is_bye=rm['bye']
                        )
                        m.p1_name_temp = rm['p1']
                        m.p1_name_temp = rm['p1']
                        m.p2_name_temp = rm['p2']
                        m.winner_name_temp = None
                        
                        # Attach IDs dynamically
                        if rm.get('p1_id'): m.p1_external_id = str(rm['p1_id'])
                        if rm.get('p2_id'): m.p2_external_id = str(rm['p2_id'])
                        
                        # Scenario
                        scen_str = rm.get('scenario')
                        if scen_str:
                            try:
                                key = scen_str.lower().replace(' ', '_')
                                m.scenario = Scenario(key)
                            except ValueError:
                                logger.warning(f"Unknown scenario: {scen_str}")
                        
                        # First Player Index (Temp)
                        if rm.get('first_player_index') is not None:
                            m.first_player_temp_index = rm['first_player_index']

                        # Winner logic
                        if m.is_bye:
                            m.winner_name_temp = m.p1_name_temp
                        elif m.player1_score > m.player2_score:
                            m.winner_name_temp = m.p1_name_temp
                        elif m.player2_score > m.player1_score:
                            m.winner_name_temp = m.p2_name_temp
                            
                        matches.append(m)
                        
            except Exception as e:
                logger.error(f"Error scraping matches: {e}")
            finally:
                browser.close()
        
        # Deduplicate if needed, though processed_rounds helps
        return matches
    
    def run_full_scrape(
        self, 
        tournament_id: str,
        subdomain: str | None = None
    ) -> tuple[Tournament, list[PlayerResult], list[Match]]:
        """
        Execute a complete scrape, optionally overriding subdomain.
        
        Args:
            tournament_id: The Longshanks event ID
            subdomain: Optional override for subdomain ("xwing" or "xwing-legacy")
        """
        # Allow runtime subdomain override
        if subdomain:
            self.subdomain = subdomain
            self.base_url = f"https://{subdomain}.longshanks.org"
        
        # 1. Metadata
        tournament = self.get_tournament_data(tournament_id)
        
        # 2. Players
        players = self.get_participants(tournament_id)
        
        if len(players) < 2:
            raise ValueError(f"Tournament {tournament_id} has fewer than 2 players ({len(players)})")
        
        # Update player count from actual results
        if players and tournament.player_count == 0:
            tournament.player_count = len(players)
        
        # 3. Infer specific format from XWS if available
        for pl in players[:20]:
            if pl.list_json and pl.list_json.get("pilots"):
                inferred = infer_format_from_xws(pl.list_json)
                if inferred != Format.OTHER:
                    tournament.format = inferred
                    logger.info(f"Inferred format {inferred.value} from player {pl.player_name}")
                    break
        
        # 4. Matches
        matches = self.get_matches(tournament_id)
        
        return tournament, players, matches


# Convenience functions for standalone use
def scrape_longshanks_event(
    event_id: int | str, 
    subdomain: str = "xwing"
) -> tuple[Tournament, list[PlayerResult], list[Match]]:
    """
    Convenience function to scrape a single Longshanks event.
    
    Args:
        event_id: The Longshanks event ID
        subdomain: "xwing" for 2.5, "xwing-legacy" for 2.0
    
    Returns:
        Tuple of (Tournament, list[PlayerResult], list[Match])
    """
    scraper = LongshanksScraper(subdomain=subdomain)
    return scraper.run_full_scrape(str(event_id))
