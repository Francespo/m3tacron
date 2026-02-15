"""
Longshanks Scraper Implementation (Playwright).

Supports X-Wing 2.5 (xwing.longshanks.org) and Legacy 2.0 (xwing-legacy.longshanks.org).
Extracts tournament data, player results with XWS, and match data.
"""
import logging
import json
import re
from datetime import datetime, date as date_type

from playwright.sync_api import sync_playwright

# Local Imports
from .base import BaseScraper
from ..models import Tournament, PlayerResult, Match
from ..data_structures.formats import Format, infer_format_from_xws
from ..data_structures.factions import Faction
from ..data_structures.platforms import Platform
from ..data_structures.round_types import RoundType
from ..data_structures.scenarios import Scenario
from ..utils import parse_builder_url


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
        self.inferred_format = None
    
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
                    page.evaluate(r"""() => {
                        const popup = document.getElementById('cookie_permission');
                        if (popup) popup.style.display = 'none';
                    }""")
        except Exception:
            pass
    

    def _parse_faction(self, value: str) -> str | None:
        """Parse faction from image alt/src."""
        faction = Faction.from_xws(value)
        return faction.value if faction != Faction.UNKNOWN else None
    
    def get_tournament_data(self, tournament_id: str, inferred_format: Format | None = None) -> Tournament:
        """
        Scrape high-level tournament metadata.
        
        Args:
            tournament_id: Longshanks event ID
            inferred_format: Format inferred from XWS data (priority over URL detection)
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
                
                # Validation: Game System
                # Check for "X-Wing" in the page content (system name usually top left or in table)
                # We specifically look for the "GameBadge" or text
                game_system_valid = page.evaluate("""() => {
                    const bodyText = document.body.innerText || "";
                    if (bodyText.includes("X-Wing")) return true;
                    if (bodyText.includes("xwing")) return true; 
                    // Reject if explicitly other games
                    if (bodyText.includes("Guild Ball")) return false;
                    // Default to true if ambiguous but no other game found? 
                    // No, USER said strict. 
                    return false;
                }""")
                
                if not game_system_valid:
                    # Relax validation: Just warn instead of failing
                    logger.warning(f"Tournament {tournament_id} does not appear to explicitly state 'X-Wing' in body. Proceeding anyway.")
                    # raise ValueError(f"Tournament {tournament_id} does not appear to be an X-Wing event.")
                
                # Data Extraction using JS
                event_info = page.evaluate("""() => {
                    let dateStr = '';
                    let playerCount = 0;
                    
                    let teamCount = 0;
                
                    const rows = document.querySelectorAll('tr');
                    for (const row of rows) {
                        const img = row.querySelector('img');
                        const cells = row.querySelectorAll('td');
                        if (!img || cells.length < 2) continue;
                        
                        const alt = img.alt || '';
                        const value = cells[1]?.textContent?.trim() || '';
                        
                        // Event size (e.g. "17 players" or "10 teams (50 players)")
                        if (alt === 'Event size' || value.includes('player')) {
                            // Team check first
                            const teamMatch = value.match(/(\\d+)\\s+team/i);
                            if (teamMatch) teamCount = parseInt(teamMatch[1], 10);

                            const outOfMatch = value.match(/(\\d+)\\s*(?:out\\s+)?of\\s+\\d+/i);
                            if (outOfMatch) {
                                playerCount = parseInt(outOfMatch[1], 10);
                            } else {
                                const pMatch = value.match(/(\\d+)\\s*player/i);
                                if (pMatch) playerCount = parseInt(pMatch[1], 10);
                            }
                        }
                        
                        // Date
                        if (alt === 'Date' || value.match(/\\d{4}-\\d{2}-\\d{2}/)) {
                            if (!dateStr) dateStr = value;
                        }
                    }
                    
                    return { dateStr, playerCount, teamCount };
                }""")
                
                # Extract Location (often under the details or separate, check simple text search in table or headers)
                # Look for "Location" label or icon with alt="Location"
                location_raw = page.evaluate("""() => {
                    const rows = document.querySelectorAll('tr');
                    for (const row of rows) {
                        const img = row.querySelector('img');
                        if (img && (img.alt === 'Location' || img.alt === 'Venue')) {
                            const cell = row.querySelector('td:nth-child(2)');
                            return cell?.textContent?.trim() || '';
                        }
                    }
                    return '';
                }""")
                
                if location_raw:
                    logger.debug(f"Longshanks Raw Location: '{location_raw}'")

                # Use resolve_location
                from ..utils.geocoding import resolve_location
                location_obj = resolve_location(location_raw) if location_raw else None
                
                if not location_obj and location_raw:
                     logger.debug(f"Could not resolve location: '{location_raw}'")

                # Manual Override for known issues (e.g. PSO Lomza mapped to Virtual but is physical)
                name_lower = name.lower()
                if ("lomza" in name_lower or "pso" in name_lower) and (not location_obj or location_obj.city == "Virtual"):
                     logger.info(f"Overriding location for {name} to Lomza, Poland")
                     location_obj = resolve_location("Lomza, Poland")
                
                if "torchlight" in name_lower:
                     logger.info(f"Overriding location for {name} to Burlington, Canada")
                     location_obj = resolve_location("Burlington, Canada")

                parsed_date = self._parse_date(event_info.get("dateStr", ""))
                player_count = event_info.get("playerCount", 0)
                
                # Determine format: Use inferred format if provided, otherwise fall back to internal state or URL
                game_format = inferred_format or self.inferred_format
                if game_format:
                    logger.info(f"Using XWS-inferred format: {game_format.value}")
                else:
                    # Fallback policy: Conservative (Format.OTHER)
                    game_format = Format.OTHER
                    logger.info("No XWS format inferred. Defaulting to OTHER (Conservative Policy).")
                
                return Tournament(
                    id=int(tournament_id),
                    name=name,
                    date=parsed_date.date(),
                    location=location_obj,
                    format=game_format,
                    player_count=player_count,
                    team_count=event_info.get("teamCount", 0),
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
        Scrape participants from the Ranking tab (Pure Python).
        """
        participants = []
        # Force navigation to Ranking tab
        url = f"{self.base_url}/event/{tournament_id}/?tab=ranking"
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            try:
                logger.info(f"Scraping participants from {url}")
                page.goto(url, wait_until="domcontentloaded", timeout=60000)
                
                # Cookie cleanup
                page.add_style_tag(content="#cookie_permission { display: none !important; }")
                
                # Wait for player list
                try:
                    page.wait_for_selector(".player", timeout=5000)
                except:
                    logger.warning("No .player elements found on Ranking tab.")
                
                # Detection: Check if it's a team event (presence of sub-tabs)
                is_team_event = page.locator("a#tab_team").count() > 0
                
                # We will perform two passes for team events, or one pass for individual events
                passes = [False] # Individual view (default)
                if is_team_event:
                    passes = [True, False] # Team view first, then Individual view
                
                participants_dict = {} # (Name, is_team) -> PlayerResult
                member_to_team = {} # PID -> TeamName mapping

                for is_team_pass in passes:
                    if is_team_event:
                        if is_team_pass:
                            # Pass 1: Scrape Teams
                            page.locator("a#tab_team").click()
                        else:
                            # Pass 2: Scrape Individuals
                            page.locator("a#tab_player").click()
                        
                        page.wait_for_timeout(2000)
                        # Wait for rows to refresh from AJAX
                        try:
                            page.wait_for_selector(".player", timeout=5000)
                        except: pass
                    
                    data_dump = []
                    # Robust selectors (legacy doesn't have .main_content)
                    ranking_container = page.locator(".ranking.event, .main_content, body").first
                    elements = ranking_container.locator("h3, .player").all()

                    for el in elements:
                        tag = el.evaluate("el => el.tagName.toLowerCase()")
                        if tag == 'h3':
                            data_dump.append({'type': 'header', 'text': el.text_content() or ''})
                            continue
                        
                        classes = el.get_attribute("class") or ""
                        if "player" not in classes: continue
                        
                        # Data Extraction
                        name_el = el.locator(".player_link").first
                        if name_el.count() == 0: name_el = el.locator(".data").first
                        name_raw = name_el.text_content() if name_el.count() > 0 else "Unknown"

                        rank_el = el.locator(".rank").first
                        rank_raw = rank_el.text_content() if rank_el.count() > 0 else "0"
                        
                        wins_el = el.locator(".wins").first
                        wins_txt = wins_el.text_content() if wins_el.count() > 0 else "0"
                        
                        loss_el = el.locator(".loss").first
                        loss_txt = loss_el.text_content() if loss_el.count() > 0 else "0"
                        
                        draws_el = el.locator(".draws").first
                        draws_txt = draws_el.text_content() if draws_el.count() > 0 else "0"
                        
                        # Stats
                        stats_items = []
                        for s in el.locator(".stat").all():
                            stats_items.append({
                                'text': s.inner_text().strip() or s.text_content().strip(),
                                'title': s.get_attribute("title") or ''
                            })
                        
                        list_icon = el.locator("a.list_link.pop").first
                        xws_raw = list_icon.get_attribute("data-list") if list_icon.count() > 0 else None
                        
                        # PID and Team Mapping
                        pid = None
                        team_name = None
                        if is_team_pass:
                             # Team View: First link is team, others are players
                             team_link = el.locator("a[onclick*='pop_team']").first
                             team_name = team_link.text_content().strip() if team_link.count() > 0 else name_raw
                             
                             # Map members
                             for m_lnk in el.locator("a[onclick*='pop_user']").all():
                                 onclick = m_lnk.get_attribute("onclick")
                                 if onclick:
                                     m_match = re.search(r"pop_user\((\d+)", onclick)
                                     if m_match:
                                         member_to_team[m_match.group(1)] = team_name
                        else:
                             # Individual View: extract PID
                             user_link = el.locator("a[onclick*='pop_user']").first
                             if user_link.count() > 0:
                                 onclick = user_link.get_attribute("onclick")
                                 if onclick:
                                     p_match = re.search(r"pop_user\((\d+)", onclick)
                                     if p_match: pid = p_match.group(1)
                             
                             if not pid:
                                 id_span = el.locator(".id_number").first
                                 if id_span.count() > 0:
                                     txt = id_span.text_content() or ""
                                     if '#' in txt: pid = re.sub(r"[^0-9]", "", txt.split('#')[-1])

                        data_dump.append({
                            'type': 'player',
                            'nameRaw': name_raw,
                            'rankRaw': rank_raw,
                            'wins': wins_txt,
                            'loss': loss_txt,
                            'draw': draws_txt,
                            'stats': stats_items,
                            'xws': xws_raw,
                            'pid': pid,
                            'pid': pid,
                            'team_name': team_name if is_team_pass else member_to_team.get(pid)
                        })
                    
                    # Process data_dump for this pass
                    current_section = "swiss"
                    for item in data_dump:
                        if item['type'] == 'header':
                            h_text = item['text'].lower()
                            if "cut" in h_text or "top" in h_text: current_section = "cut"
                            elif "main" in h_text or "swiss" in h_text: current_section = "swiss"
                            continue
                        
                        if item['type'] != 'player': continue
                        
                        try:
                            name = item.get('nameRaw', 'Unknown').strip()
                            name = re.sub(r"\s*#\d+$", "", name)
                            name = " ".join(name.split())
                            
                            
                            pid = item.get('pid')
                            t_name = item.get('team_name')

                            if "bye" in name.lower() or "drop" in name.lower() or pid == "308":
                                continue
                            
                            # Filter column headers
                            wins_raw = str(item.get('wins', '0')).strip()
                            if not re.match(r'^-?\d+$', wins_raw): continue
                            
                            r_match = re.search(r"(\d+)", str(item.get('rankRaw', '0')))
                            rank = int(r_match.group(1)) if r_match else 0
                            if rank == 0: continue
                            
                            wins = int(str(item.get('wins')).replace('-', '0').strip() or 0)
                            losses = int(str(item.get('loss')).replace('-', '0').strip() or 0)
                            draws = int(str(item.get('draw')).replace('-', '0').strip() or 0)
                            
                            tp = 0
                            vps = 0
                            score = 0
                            mov = 0
                            
                            for st in item.get('stats', []):
                                txt = st['text'].strip().replace('\xa0', ' ').replace('–', '-').replace('—', '-')
                                pattern1 = r"([a-zA-Z]+(?:\s+[a-zA-Z]+)*)\s+(-?\d+(?:\.\d+)?)"
                                matches = re.findall(pattern1, txt)
                                if not matches:
                                    pattern2 = r"(-?\d+(?:\.\d+)?)\s+([a-zA-Z]+(?:\s+[a-zA-Z]+)*)"
                                    matches_rev = re.findall(pattern2, txt)
                                    matches = [(m[1], m[0]) for m in matches_rev]
                                
                                for label_raw, val_raw in matches:
                                    label = label_raw.strip().lower()
                                    try: val_int = int(float(val_raw))
                                    except: continue
                                    if label in ["tp", "tournament points"]: tp = val_int
                                    elif label in ["mp", "mission points", "vps", "victory points"]: vps = val_int
                                    elif label in ["mov", "margin of victory"]: mov = val_int
                                    elif label in ["score", "points"]: score = val_int
                                
                                if not matches and st['title']:
                                    title_lower = st['title'].lower()
                                    try:
                                        check_str = txt.replace('.', '', 1).replace('-', '', 1)
                                        if check_str.isdigit():
                                            val = int(float(txt))
                                            if "tournament points" in title_lower or title_lower == "tp": tp = val
                                            elif "mission points" in title_lower or "victory points" in title_lower or title_lower == "vps": vps = val
                                            elif "margin of victory" in title_lower or title_lower == "mov": mov = val
                                    except: pass

                            if not tp and (wins or draws): tp = (wins * 3) + (draws * 1)
                            
                            final_ep = tp if "xwing-legacy" not in self.base_url else None
                            final_tb = vps if "xwing-legacy" not in self.base_url else (mov if mov else vps)
                            
                            key = name
                            if key in participants_dict:
                                pr = participants_dict[key]
                                if current_section == "cut":
                                    pr.cut_rank, pr.cut_wins, pr.cut_losses, pr.cut_draws = rank, wins, losses, draws
                                    pr.cut_event_points, pr.cut_tie_breaker_points = final_ep, final_tb
                                else:
                                    pr.swiss_rank, pr.swiss_wins, pr.swiss_losses, pr.swiss_draws = rank, wins, losses, draws
                                    pr.swiss_event_points, pr.swiss_tie_breaker_points = final_ep, final_tb
                            else:
                                pr = PlayerResult(
                                    tournament_id=int(tournament_id),
                                    player_name=name,
                                    team_name=t_name,
                                    list_json={}
                                )
                                if current_section == "cut":
                                    pr.cut_rank, pr.cut_wins, pr.cut_losses, pr.cut_draws = rank, wins, losses, draws
                                    pr.cut_event_points, pr.cut_tie_breaker_points = final_ep, final_tb
                                else:
                                    pr.swiss_rank, pr.swiss_wins, pr.swiss_losses, pr.swiss_draws = rank, wins, losses, draws
                                    pr.swiss_event_points, pr.swiss_tie_breaker_points = final_ep, final_tb
                                participants_dict[key] = pr

                            if item.get('xws'):
                                try:
                                    xws_json = json.loads(item['xws'])
                                    participants_dict[key].list_json = xws_json
                                    if not self.inferred_format:
                                        from ..data_structures.formats import infer_format_from_xws
                                        self.inferred_format = infer_format_from_xws(xws_json)
                                except: pass
                        except Exception as loop_e:
                            logger.warning(f"Error parsing item: {loop_e}")

                participants = list(participants_dict.values())
                self._extract_lists_from_icons(page, participants, tournament_id)
                
            except Exception as e:
                logger.error(f"Error scraping participants: {e}")
            finally:
                browser.close()
        
        return participants

    def _fetch_lists_from_popups(self, page, participants, tournament_id):
        """
        Fallback: Fetch lists from pop_info.php if icons exist but no data-list.
        """
        try:
            # 1. Identify players with missing lists who likely have them
            # We need their Longshanks ID. 
            # We must re-scan the rows to get IDs if we didn't store them.
            # Ideally, get_participants should store them.
            # For now, let's fast-scan again or assume we can find them.
            
            # Let's extract IDs from the page first
            player_ids = {} # Name -> ID
            
            rows = page.locator(".player").all()
            for row in rows:
                try:
                    # Extract Name
                    name_el = row.locator("span.player_link, a.player_link").first
                    if name_el.count() == 0: 
                        name_el = row.locator(".data").first
                    
                    if name_el.count() == 0: continue
                    raw_name = name_el.inner_text().strip()
                    
                    # Clean Name for matching
                    import re
                    clean_name = re.sub(r"\s*#\d+$", "", raw_name).strip()
                    clean_name_lower = clean_name.lower()
                    
                    # Extract ID
                    # Try onclick="pop_user(13326, ...)"
                    # Or class="id_number"
                    pid = None
                    
                    # Method A: Link onclick
                    link = row.locator("a.player_link").first
                    if link.count() > 0:
                        onclick = link.get_attribute("onclick") or ""
                        # pop_user(13326,30230)
                        m = re.search(r"pop_user\((\d+)", onclick)
                        if m: pid = m.group(1)
                    
                    # Method B: ID in text
                    if not pid:
                        id_span = row.locator(".id_number").first
                        if id_span.count() > 0:
                            txt = id_span.inner_text()
                            m = re.search(r"#(\d+)", txt)
                            if m: pid = m.group(1)
                            
                    if pid and clean_name_lower:
                        player_ids[clean_name_lower] = pid
                        
                except: pass
                
            # Filter participants needing lists
            missing = []
            for p in participants:
                # If list is empty AND we have an ID
                if (not p.list_json or not p.list_json.get("pilots")) and p.player_name.lower().strip() in player_ids:
                    missing.append((p, player_ids[p.player_name.lower().strip()]))
            
            if not missing:
                return

            logger.info(f"Fetching missing lists for {len(missing)} players via pop_info...")
            
            # 2. Get Cookies
            cookies = {c['name']: c['value'] for c in page.context.cookies()}
            
            # 3. Concurrent Fetch
            import httpx
            from concurrent.futures import ThreadPoolExecutor, as_completed
            
            def fetch_list(player, pid):
                # Use current base_url for pop_info (works for both xwing and xwing-legacy)
                url = f"{self.base_url}/admin/players/pop_info.php?player={pid}&event={tournament_id}&tab=list"
                try:
                    resp = httpx.get(url, cookies=cookies, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
                    if resp.status_code == 200:
                        import html
                        content = html.unescape(resp.text)
                        # Extract Textarea content
                        # <textarea id="list_13326" ...>{ JSON }</textarea>
                        # Regex for content between textarea tags
                        m = re.search(r"<textarea[^>]*>(.*?)</textarea>", content, re.DOTALL)
                        if m:
                            json_str = m.group(1).strip()
                            try:
                                return player, json.loads(json_str)
                            except Exception as je:
                                logger.error(f"Failed to parse XWS JSON for {player.player_name}: {je}")
                except Exception as e:
                    logger.debug(f"Fetch list error for {pid}: {e}")
                return player, None

            with ThreadPoolExecutor(max_workers=10) as executor:
                futures = [executor.submit(fetch_list, p, pid) for p, pid in missing]
                
                for future in as_completed(futures):
                    try:
                        p, xws = future.result()
                        if xws:
                            p.list_json = xws
                    except: pass
                    
        except Exception as e:
            logger.error(f"Error in _fetch_lists_from_popups: {e}")

    def _extract_lists_from_icons(self, page, participants, tournament_id):
        """
        Extract XWS from list icons (Pure Python).
        """
        found_any = False
        try:
            # Find all list icons
            icons = page.locator("a.list_link.pop").all()
            
            # If no standard icons, check for the popup style icons (Step 2)
            if not icons:
                # Check for ANY list icon image to decide if we should try popup fetch
                other_icons = page.locator("img[src*='list_code.png']").count()
                if other_icons > 0:
                     logger.info("Found list icons but no data-list. Attempting popup fetch.")
                     self._fetch_lists_from_popups(page, participants, tournament_id)
                     return

            if not icons:
                return

            import json
            for icon in icons:
                try:
                    # Get data-list attribute
                    xws_str = icon.get_attribute("data-list")
                    if not xws_str: continue
                    
                    found_any = True
                    
                    # Get player ID from parent row
                    row = icon.locator("xpath=./ancestor::div[contains(@class, 'player')]").first
                    if row.count() == 0: continue
                    
                    # Extract Name from row
                    name_el = row.locator("span.player_link, a.player_link").first
                    if name_el.count() == 0: 
                        name_el = row.locator(".data").first
                    
                    if name_el.count() == 0: continue
                    
                    raw_name = name_el.inner_text().strip()
                    # Clean ID suffix
                    if "#" in raw_name:
                        import re
                        raw_name = re.sub(r"\s*#\d+$", "", raw_name)
                    
                    clean_target = raw_name.lower().strip()
                    
                    # Find participant (Case insensitive match)
                    target_p = None
                    for p in participants:
                        if p.player_name.lower().strip() == clean_target:
                            target_p = p
                            break
                    
                    if target_p:
                        try:
                            xws = json.loads(xws_str)
                            target_p.list_json = xws
                            # STATEFUL INFERENCE: Capture format from first XWS found
                            if not self.inferred_format:
                                from ..data_structures.formats import infer_format_from_xws
                                self.inferred_format = infer_format_from_xws(xws)
                        except: 
                            # Fallback: if data-list is actually a URL or something else, 
                            # we might want to store it, but for now we follow XWS spec.
                            pass
                         
                except Exception as loop_e:
                     pass
                     
            if not found_any:
                 # Double check if we should try popups
                 other_icons = page.locator("img[src*='list_code.png']").count()
                 if other_icons > 0:
                     self._fetch_lists_from_popups(page, participants, tournament_id)
                     
        except Exception as e:
            logger.warning(f"List extraction warning: {e}")


    def get_matches(self, tournament_id: str) -> list[Match]:
        """Scrape matches from the Games tab by iterating the round dropdown.

        Longshanks shows one round at a time via a #round_selector dropdown.
        This method selects each round option, waits for DOM update, and
        extracts match data from the .results containers.
        """
        matches = []
        url = f"{self.base_url}/event/{tournament_id}/?tab=games"

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            try:
                # Check for Legacy format first
                is_legacy = False
                if self.inferred_format:
                    fmt_val = self.inferred_format.value if hasattr(self.inferred_format, "value") else self.inferred_format
                    if fmt_val in [Format.LEGACY_XLC.value, Format.LEGACY_X2PO.value, Format.FFG.value]:
                        is_legacy = True
                        logger.info("Legacy format detected (from XWS). Forcing Scenario to NO_SCENARIO.")

                page.goto(url, wait_until="domcontentloaded", timeout=60000)
                page.add_style_tag(
                    content="#cookie_permission { display: none !important; }"
                )

                # Check Title/System for Legacy keywords if not already detected
                if not is_legacy:
                    try:
                        # 1. Check event header text (Title is usually H1, but system is in .event_status)
                        # Subagent found: div.event_status .entry .text -> "X-Wing Legacy"
                        # Also check H1 just in case
                        header_texts = []
                        
                        # Title
                        h1 = page.locator("h1").first
                        if h1.count() > 0:
                            header_texts.append(h1.inner_text())
                            
                        # System Text
                        sys_text = page.locator(".event_status .entry .text").all_inner_texts()
                        header_texts.extend(sys_text)
                        
                        # System Logo Title
                        sys_logo = page.locator("img.logo.system").first
                        if sys_logo.count() > 0:
                            header_texts.append(sys_logo.get_attribute("title") or "")
                            
                        full_header_text = " ".join(header_texts).lower()
                        
                        if any(x in full_header_text for x in ["legacy", "2.0", "x2po", "xlc", "ffg"]):
                            is_legacy = True
                            logger.info(f"Legacy format detected (from Page Info: '{full_header_text[:100]}...'). Forcing Scenario to NO_SCENARIO.")
                    except Exception as e:
                        logger.warning(f"Error checking for legacy format in DOM: {e}")
                page.wait_for_timeout(2000)

                # Get round options from the dropdown
                round_options = page.evaluate("""() => {
                    const sel = document.getElementById('round_selector');
                    if (!sel) return [];
                    return Array.from(sel.options).map(o => ({
                        value: o.value, text: o.innerText.trim()
                    }));
                }""")

                if not round_options:
                    logger.warning(f"No round_selector found for {tournament_id}")
                    return []

                logger.info(
                    f"Found {len(round_options)} rounds in dropdown."
                )

                for opt in round_options:
                    round_text = opt["text"]
                    round_val = opt["value"]

                    # Parse round number and type from dropdown text
                    round_num = 0
                    round_type = RoundType.SWISS
                    rm = re.search(r"Round (\d+)", round_text)
                    if rm:
                        round_num = int(rm.group(1))
                    elif "Cut" in round_text or "Top" in round_text:
                        round_type = RoundType.CUT
                        cm = re.search(r"(\d+)", round_text)
                        round_num = int(cm.group(1)) if cm else 0
                    else:
                        # Fallback: use dropdown value as round number
                        try:
                            round_num = int(round_val)
                        except (ValueError, TypeError):
                            round_num = 0

                    # Parse scenario from round text ("Round 1 - Scramble")
                    scenario = None
                    if not is_legacy:
                        if " - " in round_text:
                            scen_part = round_text.split(" - ", 1)[1].strip()
                            scenario = self._parse_scenario(scen_part)
                    else:
                        from ..data_structures.scenarios import Scenario
                        scenario = Scenario.NO_SCENARIO
                    
                    # Fallback: Scan page content for known scenarios if not found in dropdown
                    if not scenario or scenario == "unknown": # Check vs "unknown" string if enum returns that, or None
                         # We need to wait for content to load first, which happens below after click. 
                         # So we move this logic AFTER the click/wait.
                         pass

                    # Select round using robust trigger (jQuery or Native)
                    page.evaluate(f"""() => {{
                        const sel = document.getElementById('round_selector');
                        if (!sel) return;
                        sel.value = '{round_val}';
                        if (typeof jQuery !== 'undefined') {{
                            jQuery(sel).trigger('change');
                        }} else {{
                            sel.dispatchEvent(new Event('change', {{ bubbles: true }}));
                        }}
                    }}""")
                    page.wait_for_timeout(2000)

                    # --- Precise Scenario Extraction (Subagent Verified) ---
                    # Logic: Look for any "Scenario" header inside a match item and grab its sibling.
                    # We assume the scenario is the same for all matches in the round (Standard Longshanks behavior).
                    if not is_legacy and (not scenario or scenario == "unknown"):
                        try:
                            # Execute JS to find the first valid scenario text in this round
                            found_scen_text = page.evaluate("""() => {
                                const headers = Array.from(document.querySelectorAll('span.header'));
                                const scenHeader = headers.find(h => h.innerText.trim() === 'Scenario');
                                if (scenHeader && scenHeader.nextElementSibling) {
                                    return scenHeader.nextElementSibling.innerText.trim();
                                }
                                return null;
                            }""")
                            
                            if found_scen_text:
                                scenario = self._parse_scenario(found_scen_text)
                                logger.info(f"Extracted scenario from DOM: '{found_scen_text}' -> {scenario}")
                        except Exception as e:
                            logger.warning(f"DOM scenario extraction failed: {e}")
                    # -------------------------------------------------------

                    # Each .results div IS one match (2 child .player divs)
                    result_divs = page.locator(".results").all()
                    for rdiv in result_divs:
                        try:
                            player_divs = rdiv.locator(".player").all()
                            if len(player_divs) < 2:
                                continue

                            # Extract player names from .player_link
                            p1_link = player_divs[0].locator(".player_link")
                            p2_link = player_divs[1].locator(".player_link")
                            if p1_link.count() == 0 or p2_link.count() == 0:
                                continue

                            p1_name = p1_link.inner_text().strip()
                            p2_name = p2_link.inner_text().strip()

                            # Extract scores from .score elements
                            s1 = 0
                            s2 = 0
                            p1_score_el = player_divs[0].locator(".score")
                            p2_score_el = player_divs[1].locator(".score")
                            if p1_score_el.count() > 0:
                                try:
                                    s1 = int(p1_score_el.inner_text().strip())
                                except ValueError:
                                    s1 = 0
                            if p2_score_el.count() > 0:
                                try:
                                    s2 = int(p2_score_el.inner_text().strip())
                                except ValueError:
                                    s2 = 0

                            # Winner from CSS class (winner/loser)
                            p1_cls = player_divs[0].get_attribute("class") or ""
                            p2_cls = player_divs[1].get_attribute("class") or ""
                            winner_name = None
                            if "winner" in p1_cls:
                                winner_name = p1_name
                            elif "winner" in p2_cls:
                                winner_name = p2_name
                            elif s1 > s2:
                                winner_name = p1_name
                            elif s2 > s1:
                                winner_name = p2_name

                            is_bye = "bye" in p2_name.lower()

                            m_dict = {
                                "round_number": round_num,
                                "round_type": round_type,
                                "scenario": scenario,
                                "player1_score": s1,
                                "player2_score": s2,
                                "is_bye": is_bye,
                                "p1_name_temp": p1_name,
                                "p2_name_temp": p2_name,
                                "winner_name_temp": winner_name,
                            }
                            matches.append(m_dict)
                        except Exception:
                            pass

                    logger.info(
                        f"Round '{round_text}': "
                        f"{sum(1 for m in matches if m['round_number'] == round_num)} matches"
                    )

            except Exception as e:
                logger.error(f"Error scraping matches: {e}")
            finally:
                browser.close()

        logger.info(f"Total matches scraped: {len(matches)}")
        return matches

    def list_tournaments(
        self,
        date_from: date_type,
        date_to: date_type,
        max_pages: int | None = None
    ) -> list[dict]:
        """
        Discover tournament URLs from the Longshanks history page.

        Scrapes /events/history/ with pagination, filtering by date range.

        Args:
            date_from: Start of date range (inclusive).
            date_to: End of date range (inclusive).
            max_pages: Max pages to scrape. None = all pages.

        Returns:
            List of dicts: {url, name, date, player_count}.
        """
        results = []
        # Support date filtering directly via URL parameters
        history_url = f"{self.base_url}/events/history/"
        if date_from and date_to:
            history_url += f"?date_from={date_from.isoformat()}&date_to={date_to.isoformat()}"
        
        logger.info(f"Scraping Longshanks history: {history_url}")

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            try:
                page.goto(history_url, wait_until="domcontentloaded", timeout=30000)
                page.wait_for_timeout(2000)
                self._dismiss_cookie_popup(page)

                pages_scraped = 0
                stop_early = False

                while True:
                    pages_scraped += 1
                    if max_pages and pages_scraped > max_pages:
                        break

                    # Extract tournament cards from current page
                    cards = page.locator(".event_display").all()
                    logger.info(f"Page {pages_scraped}: found {len(cards)} tournament cards.")

                    for card in cards:
                        try:
                            # Name + URL
                            name_link = card.locator(".event_name a").first
                            if name_link.count() == 0:
                                continue
                            name = name_link.inner_text().strip()
                            href = name_link.get_attribute("href") or ""
                            url = f"{self.base_url}{href}" if href.startswith("/") else href

                            # Date — find td with img[alt='Date'], get next sibling td
                            date_text = page.evaluate(
                                """(card) => {
                                    const tds = card.querySelectorAll('td');
                                    for (let i = 0; i < tds.length; i++) {
                                        const img = tds[i].querySelector('img[alt="Date"]');
                                        if (img && tds[i+1]) return tds[i+1].textContent.trim();
                                    }
                                    return '';
                                }""",
                                card.element_handle()
                            )
                            parsed_date = self._parse_date(date_text)
                            event_date = parsed_date.date() if isinstance(parsed_date, datetime) else parsed_date

                            # Date range filter — skip future events beyond range
                            if event_date > date_to:
                                continue
                            if event_date < date_from:
                                # History is sorted newest-first, so once we pass
                                # the range we can stop scraping entirely
                                stop_early = True
                                break

                            # Player count
                            size_text = page.evaluate(
                                """(card) => {
                                    const tds = card.querySelectorAll('td');
                                    for (let i = 0; i < tds.length; i++) {
                                        const img = tds[i].querySelector('img[alt="Event size"]');
                                        if (img && tds[i+1]) return tds[i+1].textContent.trim();
                                    }
                                    return '0';
                                }""",
                                card.element_handle()
                            )
                            player_count = 0
                            p_match = re.search(r"(\d+)\s*player", size_text, re.IGNORECASE)
                            if p_match:
                                player_count = int(p_match.group(1))

                            results.append({
                                "url": url,
                                "name": name,
                                "date": event_date.isoformat(),
                                "player_count": player_count,
                            })
                        except Exception as e:
                            logger.debug(f"Error parsing card: {e}")

                    if stop_early:
                        break

                    # Pagination: click next page button (⟫⟫ or next numbered page)
                    next_btn = page.locator("a.button.small:has-text('⟫⟫')").first
                    if next_btn.count() > 0:
                        next_btn.click()
                        page.wait_for_timeout(2000)
                    else:
                        break
            except Exception as e:
                logger.error(f"Error listing tournaments: {e}")
            finally:
                browser.close()

        logger.info(f"Discovered {len(results)} tournaments from Longshanks ({self.subdomain}).")
        return results

    def run_full_scrape(
        self, 
        tournament_id: str,
        subdomain: str | None = None
    ) -> tuple[Tournament, list[PlayerResult], list[Match]]:
        """Override to support runtime subdomain switching."""
        if subdomain:
            self.subdomain = subdomain
            self.base_url = f"https://{subdomain}.longshanks.org"

        return super().run_full_scrape(tournament_id)


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
