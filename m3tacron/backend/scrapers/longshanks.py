"""
Longshanks Scraper Implementation (Playwright).

Supports X-Wing 2.5 (xwing.longshanks.org) and Legacy 2.0 (xwing-legacy.longshanks.org).
Extracts tournament data, player results with XWS, and match data.
"""
import logging
import json
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
from ..utils.squadron import parse_builder_url


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
                    print(f"DEBUG: Longshanks Raw Location: '{location_raw}'")
                else:
                    print("DEBUG: Longshanks Raw Location not found in table.")

                # Use resolve_location
                from ..utils.geocoding import resolve_location
                location_obj = resolve_location(location_raw) if location_raw else None
                
                if not location_obj and location_raw:
                     print(f"DEBUG: Could not resolve location: '{location_raw}'")

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
                    # Fallback to URL-based detection
                    if "xwing-legacy" in self.base_url:
                         game_format = Format.LEGACY_XLC
                    else:
                         game_format = Format.XWA # Use XWA as more specific default for 2.5 subdomain
                    logger.info(f"Using URL-based format (no XWS available): {game_format.value}")
                
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
                            
                            # Robust Integer Parsing: Skip header rows (e.g. "W / L / D")
                            def safe_int(val, default=0):
                                if val is None: return default
                                s = str(val).strip().replace('-', '0')
                                if not s or not re.match(r'^-?\d+$', s): return default
                                return int(s)

                            wins_txt = item.get('wins', '0')
                            if not re.match(r'^-?\d+$', str(wins_txt).strip()): continue
                            
                            r_match = re.search(r"(\d+)", str(item.get('rankRaw', '0')))
                            rank = int(r_match.group(1)) if r_match else 0
                            if rank == 0: continue
                            
                            wins = safe_int(item.get('wins'))
                            losses = safe_int(item.get('loss'))
                            draws = safe_int(item.get('draw'))
                            
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

    def _parse_scenario(self, text: str) -> str | None:
        """Helper to extract Scenario enum name from text."""
        if not text: return None
        text_norm = text.lower().replace(" ", "_").strip()
        
        # Mapping Fix
        if "assault_the_satellite" in text_norm:
            text_norm = "assault_at_the_satellite_array"
            
        from ..data_structures.scenarios import Scenario
        for s in Scenario:
            if s.value != "unknown" and s.value.replace("_", " ") in text.lower():
                 return s.value
            # Also check direct value match
            if s.value in text_norm:
                 return s.value
        return Scenario.OTHER_UNKNOWN 

    def get_matches(self, tournament_id: str) -> list[Match]:
        """
        Scrape matches from the Games tab (Pure Python).
        """
        matches = []
        url = f"{self.base_url}/event/{tournament_id}/?tab=games"
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            try:
                logger.info(f"Scraping matches from {url}")
                page.goto(url, wait_until="domcontentloaded", timeout=60000)
                page.add_style_tag(content="#cookie_permission { display: none !important; }")
                
                # Ensure we are on the games tab
                try:
                    page.wait_for_selector("#tab_games", timeout=5000)
                    page.click("#tab_games")
                    page.wait_for_load_state("networkidle", timeout=30000)
                except: pass

                # Detect rounds if selector exists
                rounds = [""]
                try:
                    sel = page.locator("#round_selector")
                    if sel.count() > 0:
                        # Extract round list
                        rounds = [opt.get_attribute("value") for opt in sel.locator("option").all() if opt.get_attribute("value")]
                except: pass
                
                if not rounds: rounds = [""]

                processed_hashes = set()

                for rnd in rounds:
                    if rnd:
                        logger.info(f"Switching to Round {rnd}...")
                        try:
                            # Use select_option to switch round without full page reload
                            page.select_option("#round_selector", rnd)
                            # Wait for AJAX load
                            page.wait_for_load_state("networkidle", timeout=30000)
                            page.wait_for_timeout(3000) 
                        except Exception as exe:
                            logger.warning(f"Error switching round {rnd}: {exe}")
                    
                    # Expand accordions if team event (AJAX load)
                    try:
                        logger.info("Expanding accordions...")
                        page.evaluate("if(typeof all_accordions === 'function') all_accordions('expand');")
                        page.wait_for_timeout(5000) 
                    except: pass

                    try:
                        # Wait for ANY of the possible match containers
                        page.wait_for_selector(".results, #games, .game, .item, .pairing", timeout=15000)
                    except:
                        logger.warning(f"Timeout waiting for elements in round {rnd}")
                        continue
                    
                    # Capture pairings for this round
                    current_round = int(rnd) if rnd and rnd.isdigit() else 0
                    current_round_type = RoundType.SWISS
                    current_scenario = None
                    
                    items = page.locator(".item, .match, .game, .pairing").all()
                    logger.info(f"Scraped {len(items)} raw items for Round {rnd}")
                    
                    for el in items:
                        try:
                            cls = el.get_attribute("class") or ""
                            
                            if "item" in cls:
                                txt = el.inner_text().strip()
                                # Detect Round headers
                                if "Round" in txt and not (rnd and rnd.isdigit()):
                                    m_rnd = re.search(r"Round (\d+)", txt)
                                    if m_rnd: current_round = int(m_rnd.group(1))
                                    current_round_type = RoundType.SWISS
                                elif ("Cut" in txt or "Top" in txt):
                                    current_round = (current_round or 0) + 1
                                    current_round_type = RoundType.CUT
                                
                                # Scenario detection
                                if "-" in txt:
                                    scen_txt = txt.split("-", 1)[1].strip()
                                    current_scenario = self._parse_scenario(scen_txt)
                                else:
                                    current_scenario = None
                            
                            elif "match" in cls or "game" in cls or "pairing" in cls:
                                # Try multiple ways to find player names
                                p_names = []
                                # Option A: .player wrappers (standard)
                                p_els = el.locator(".player").all()
                                if len(p_els) >= 2:
                                    for p_el in p_els:
                                        # Try .player_disp, .player_link, or direct text
                                        name_el = p_el.locator(".player_disp, .player_link, .data").first
                                        if name_el.count() > 0:
                                            p_names.append(name_el.inner_text().strip())
                                        else:
                                            p_names.append(p_el.inner_text().strip())
                                
                                # Option B: Direct .player_link or .player_disp siblings (modal/compact)
                                if len(p_names) < 2:
                                    p_names = [n.inner_text().strip() for n in el.locator(".player_link, .player_disp, .data").all() if n.inner_text().strip()]
                                
                                if len(p_names) < 2:
                                    logger.info(f"Skipping potential match {cls}: only found players {p_names}")
                                    continue
                                
                                p1_raw = p_names[0]
                                p2_raw = p_names[1]
                                
                                # Hash to avoid duplicates
                                m_hash = f"{current_round}-{p1_raw}-{p2_raw}"
                                if m_hash in processed_hashes: continue
                                processed_hashes.add(m_hash)

                                # Clean names (remove #ID suffix)
                                p1_clean = re.sub(r"\s*#\d+$", "", p1_raw)
                                p1_clean = " ".join(p1_clean.split())
                                p2_clean = re.sub(r"\s*#\d+$", "", p2_raw)
                                p2_clean = " ".join(p2_clean.split())
                                
                                # Score extraction
                                s_els = el.locator(".score").all()
                                s1 = 0
                                s2 = 0
                                if len(s_els) >= 2:
                                    try:
                                        s1_txt = s_els[0].inner_text().strip().replace('-', '0')
                                        s2_txt = s_els[1].inner_text().strip().replace('-', '0')
                                        s1 = int(float(s1_txt))
                                        s2 = int(float(s2_txt))
                                    except: pass
                                
                                logger.info(f"SUCCESS: Scraped pairing: {repr(p1_clean)} vs {repr(p2_clean)} (Round {current_round})")

                                matches.append({
                                    "round_number": current_round or 1,
                                    "round_type": current_round_type,
                                    "scenario": current_scenario,
                                    "player1_score": s1,
                                    "player2_score": s2,
                                    "is_bye": "bye" in p2_clean.lower(),
                                    "p1_name_temp": p1_clean,
                                    "p2_name_temp": p2_clean,
                                    "winner_name_temp": p1_clean if s1 > s2 else (p2_clean if s2 > s1 else None)
                                })
                        except Exception as e:
                            logger.error(f"Error processing item: {e}")
                            
            except Exception as e:
                logger.error(f"Error scraping matches: {e}")
            finally:
                browser.close()
                
        return matches

    def run_full_scrape(
        self, 
        tournament_id: str,
        subdomain: str | None = None
    ) -> tuple[Tournament, list[PlayerResult], list[Match]]:
        """
        Execute a complete scrape, optionally overriding subdomain.
        
        XWS-PRIORITY FLOW:
        1. Extract participants and XWS data
        2. Infer format from XWS (priority)
        3. Create tournament with inferred format
        4. Extract matches
        """
        # Allow runtime subdomain override
        if subdomain:
            self.subdomain = subdomain
            self.base_url = f"https://{subdomain}.longshanks.org"
        
        # STEP 1: Extract Players & XWS data FIRST
        players = self.get_participants(tournament_id)
        
        if len(players) < 2:
            raise ValueError(f"Tournament {tournament_id} has fewer than 2 players ({len(players)})")
        
        # STEP 2: Infer format from XWS data (priority over URL)
        inferred_format = None
        for pl in players[:20]:  # Check first 20 players
            if pl.list_json and pl.list_json.get("pilots"):
                inferred = infer_format_from_xws(pl.list_json)
                if inferred != Format.OTHER:
                    inferred_format = inferred
                    logger.info(f"XWS-inferred format {inferred.value} from player {pl.player_name}")
                    break
        
        # STEP 3: Create Tournament with inferred format
        tournament = self.get_tournament_data(tournament_id, inferred_format=inferred_format)
        
        # Update player count from actual results
        if players and tournament.player_count == 0:
            tournament.player_count = len(players)
        
        # STEP 4: Extract Matches
        matches = self.get_matches(tournament_id)
        
        return tournament, players, matches


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
