
import json
import logging
import re
from datetime import datetime
from playwright.sync_api import sync_playwright

from .base import BaseScraper
from ..models import Tournament, PlayerResult, Match
from ..data_structures.formats import Format, infer_format_from_xws
from ..data_structures.platforms import Platform
from ..data_structures.round_types import RoundType
from ..data_structures.round_types import RoundType
from ..data_structures.scenarios import Scenario
from ..data_structures.location import Location

logger = logging.getLogger(__name__)

# Game System URLs for reference
XWING_25AMG_URL = "https://rollbetter.gg/games/5"
XWING_25XWA_URL = "https://rollbetter.gg/games/17"
XWING_20_URL = "https://rollbetter.gg/games/4"

class RollbetterScraper(BaseScraper):
    """
    Improved RollBetter Scraper (V2).
    """
    
    BASE_URL = "https://rollbetter.gg"
    
    def __init__(self):
        super().__init__()
        self.cache = {} # Map ID -> dict (full data)

    def _parse_date(self, text: str) -> datetime:
        try:
            match = re.search(r"([A-Za-z]{3})\s+(\d{1,2}),\s+(\d{4})", text)
            if match:
                return datetime.strptime(match.group(0), "%b %d, %Y")
        except:
            pass
        return datetime.now()
    def _parse_int(self, val: str) -> int:
        try:
            return int(str(val).strip())
        except (ValueError, AttributeError):
            return 0

    def _ensure_data(self, tournament_id: str):
        """Load data if not in cache."""
        if tournament_id in self.cache:
            return

        error_trace = None
        for attempt in range(3):
            try:
                # Scrape ListFortress JSON from Rollbetter
                url = f"{self.BASE_URL}/tournaments/{tournament_id}"
                
                with sync_playwright() as p:
                    browser = p.chromium.launch(headless=True)
                    page = browser.new_page()
                    page.goto(url, wait_until="load", timeout=60000)
                    
                    # Wait for data load
                    page.wait_for_timeout(3000)
                    
                    # Check for validation (throws error if fails)
                    if not self._validate_page(page, tournament_id):
                        raise ValueError("Tournament failed validation")

                    # Try ListFortress Export Logic directly here
                    lf_data = None
                    triggered = False
                    
                    # 1. Look for Export Button (Dropdown)
                    try:
                        export_btn = page.locator("button:has-text('Export')")
                        if export_btn.count() > 0 and export_btn.first.is_visible():
                            export_btn.first.click()
                            page.wait_for_timeout(500)
                    except: pass
                    
                    # 2. Look for "List Fortress" link/button
                    lf_btn = page.locator("a:has-text('List Fortress'), button:has-text('List Fortress')")
                    if lf_btn.count() > 0:
                        logger.info(f"Found List Fortress export button for {tournament_id}")
                        lf_btn.first.click()
                        triggered = True
                    else:
                        # Fallback: maybe just "JSON" or "Export JSON"
                        json_btn = page.locator("a:has-text('JSON'), button:has-text('JSON')")
                        if json_btn.count() > 0:
                             json_btn.first.click()
                             triggered = True
                    
                    if triggered:
                        logger.info("Triggered JSON calculation...")
                        # Wait for the modal and the "Calculate" button if needed (sometimes auto triggers)
                        
                        # Sometimes we need to click "Calculate" inside modal
                        calc_btn = page.locator("button:has-text('Calculate List Fortress JSON')")
                        try:
                            if calc_btn.count() > 0:
                                calc_btn.first.click()
                                page.wait_for_timeout(1000)
                        except: pass

                        page.wait_for_timeout(2000) # Wait for modal population
                        
                        # Extract from Modal
                        if page.locator("div.modal-content textarea").count() > 0:
                             lf_data = page.locator("div.modal-content textarea").first.input_value()
                        elif page.locator("textarea.copy-target").count() > 0:
                             lf_data = page.locator("textarea.copy-target").first.input_value()
                        elif page.locator("textarea").count() > 0:
                             # Generic textarea if only one
                             lf_data = page.locator("textarea").first.input_value()
                        
                        # Close modal
                        page.keyboard.press("Escape")
                    
                    if lf_data:
                        logger.info(f"Using LF JSON for {tournament_id} (Length: {len(lf_data)})")
                        self.cache[tournament_id] = self._parse_from_json_v2(json.loads(lf_data) if isinstance(lf_data, str) else lf_data, tid=tournament_id, url=url)
                        
                        # Fix Name from H1 if JSON was generic
                        try:
                            h1_text = page.locator("h1").first.inner_text().strip()
                            if h1_text and "Rollbetter Event" in self.cache[tournament_id]['tournament'].name:
                                 self.cache[tournament_id]['tournament'].name = h1_text
                        except: pass
                        
                        # Now scrape UI for Location and Detailed Matches
                        try:
                            location_data = self._extract_location(page)
                            if location_data:
                                self.cache[tournament_id]['tournament'].location = location_data
                            
                            matches = self._scrape_detailed_matches(page, tournament_id)
                            if matches:
                                self.cache[tournament_id]['matches'] = matches
                        except Exception as e:
                            logger.warning(f"UI detail scrape failed for {tournament_id}: {e}")
                        
                        return # Success!
                    
                    # If we got here, we failed to get data
                    logger.warning(f"Attempt {attempt+1}: Failed to extract LF JSON.")
                    
            except Exception as e:
                logger.error(f"Attempt {attempt+1} Error for {tournament_id}: {e}")
                error_trace = e
                # Retry loop continues
        
        logger.error(f"Failed to scrape LF data for {tournament_id} after 3 attempts.")
        if error_trace:
             import traceback
             traceback.print_exc()
        # Raise so worker knows it failed
        raise ValueError("Failed to ensure data")

    def get_tournament_data(self, tournament_id: str) -> Tournament:
        self._ensure_data(tournament_id)
        return self.cache[tournament_id]['tournament']

    def get_participants(self, tournament_id: str) -> list[PlayerResult]:
        self._ensure_data(tournament_id)
        players = self.cache[tournament_id]['players']
        if not players:
            logger.warning(f"Rollbetter: No players found for {tournament_id} even after ensure_data.")
        return players

    def get_matches(self, tournament_id: str) -> list[Match]:
        self._ensure_data(tournament_id)
        return self.cache[tournament_id]['matches']

    # Validation (same as before)
    def _validate_page(self, page, tournament_id) -> bool:
        body_text = page.inner_text("body")
        
        # 1. Game System
        h1_text = page.locator("h1").first.inner_text()
        
        is_xwing_title = "x-wing" in h1_text.lower()
        
        if "Marvel Crisis Protocol" in body_text and not is_xwing_title:
             # Only reject if title is NOT X-Wing
             logger.warning(f"Tournament {tournament_id} seems to be Marvel Crisis Protocol. Skipping.")
             return False
             
        if "Star Wars: Legion" in body_text and not is_xwing_title:
             logger.warning(f"Tournament {tournament_id} seems to be Legion. Skipping.")
             return False
            
        if "X-Wing" not in body_text and "Miniatures Game" not in body_text and not is_xwing_title:
             logger.warning(f"Tournament {tournament_id} missing 'X-Wing' identifier in Body or Title. Skipping.")
             return False

        # Date
        date_obj = datetime.now()
        try:
            calendar_icon = page.locator(".bi-calendar, .fa-calendar").first
            if calendar_icon.count() > 0:
                 parent = calendar_icon.locator("..").inner_text()
                 date_obj = self._parse_date(parent)
            
            # Allow "Today" as valid (<=)
            if date_obj.date() > datetime.now().date():
                logger.warning(f"Tournament {tournament_id} is in the future ({date_obj.date()}). Skipping.")
                return False
        except: pass
            
        # Count
        player_count = 0
        try:
            badges = page.locator(".badge").all_inner_texts()
            for b in badges:
                if "/" in b:
                    parts = b.split("/")
                    if parts[0].strip().isdigit():
                        player_count = int(parts[0].strip())
                        break
            if player_count <= 1:
                logger.warning(f"Tournament {tournament_id} has insufficient players. Skipping.")
                return False
        except: pass
            
        return True

    def _extract_location(self, page) -> dict | None:
        from ..utils.geocoding import resolve_location
        from ..data_structures.location import Location
        location_data = None
        try:
            # Strategy 0: Check for "Online" badge/indicator first
            body_text = page.inner_text("body")
            # If "Online" badge exists and no physical address elements, use Virtual
            online_indicators = ["Event Type: Online", "Online Event", "Online Tournament"]
            if any(ind in body_text for ind in online_indicators):
                return Location.create(city="Virtual", country="Virtual", continent="Virtual")
            
            # Also check if there's a specific "Online" badge class near the header
            try:
                online_badge = page.locator("span.badge:has-text('Online'), div:has-text('Online')").first
                if online_badge.count() > 0:
                    badge_text = online_badge.inner_text().strip()
                    if badge_text == "Online":
                        return Location.create(city="Virtual", country="Virtual", continent="Virtual")
            except: pass

            # Strategy 1: Icons (wait for them)
            try:
                page.wait_for_selector(".bi-geo-alt, .fa-map-marker-alt, .fa-map-marker", timeout=3000)
            except:
                pass
                
            loc_icon = page.locator(".bi-geo-alt, .fa-map-marker-alt, .fa-map-marker").first
            if loc_icon.count() > 0:
                full_text = loc_icon.locator("..").inner_text().strip()
                if full_text:
                    # Use new geocoding logic
                    location_data = resolve_location(full_text)
            
            # Strategy 2: Fallback to text blocks
            if not location_data:
                try:
                    page.wait_for_selector("div.overflow-protected", timeout=3000)
                except: pass
                
                blocks = page.locator("div.overflow-protected").all()
                for block in blocks:
                    text = block.inner_text().strip()
                    if text in ["Started", "Open", "More", "Show More", "List Fortress", "In Person"]: continue
                    # Handle "Online" explicitly - aggressively
                    if "online" in text.lower():
                        return Location.create(city="Virtual", country="Virtual", continent="Virtual")
                    if "X-Wing" in text or "Standard" in text or "Legacy" in text or "Round" in text: continue
                    if ":" in text and ("AM" in text or "PM" in text): continue
                    
                    if len(text) < 100:
                        # Try to resolve any short text block that might be a location
                        loc = resolve_location(text)
                        if loc:
                            location_data = loc
                            break
        except Exception as e: 
            logger.warning(f"Location extraction failed: {e}")
            pass
        return location_data

    # _try_listfortress_export removed as logic moved into _ensure_data retry loop


    def _parse_from_json_v2(self, data: dict, tid: str, url: str):
        """
        New JSON parser that only handles Tournament metadata and Players.
        Matches are handled by _scrape_detailed_matches.
        """
        # Use title from JSON or fallback to page title (needs to be passed or stored)
        # Note: Rollbetter V2 often has empty title in LF JSON.
        name = data.get("title")
        if not name or "Rollbetter Event" in name:
            # Fallback to cached name if available or generic
            # We can't easily access cache here because we return the dict to put IN cache.
            # But the caller has the H1. Ideally we pass H1 to this function.
            # For now, let's trust the caller to update it or duplicate logic.
            # UPDATE: We will update the name in _ensure_data AFTER parsing if JSON name is bad.
            name = f"Rollbetter Event {tid}"

        date_str = data.get("date", "")
        formatted_date = datetime.now().date()
        if date_str:
            try: formatted_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            except: pass
        
        import os
        print(f"DEBUG: Scraper file: {os.path.abspath(__file__)}")
        print(f"DEBUG: JSON Keys: {list(data.keys())}")
        
        # Players
        players_json = data.get("players", []) or data.get("participants", []) or data.get("standings", [])
        print(f"DEBUG: Found {len(players_json)} players in JSON")
        t = Tournament(
            id=int(tid), name=name, date=formatted_date,
            player_count=len(players_json), platform=Platform.ROLLBETTER, url=url, format=Format.OTHER
        )

        participants = []
        for p in players_json:
            raw_list = p.get("list", {})
            list_json = {}
        results = []
        try:
            for player in players_json:
                raw_list = player.get("list", {})
                list_json = {}
                if isinstance(raw_list, str) and raw_list.strip():
                    try: list_json = json.loads(raw_list)
                    except: pass
                elif isinstance(raw_list, dict):
                    list_json = raw_list
                
                # Rollbetter JSON typically has: rank, wins, losses, draws, points
                # Use these as Swiss stats (and general stats if no cut)
                # Helper for safe int casting
                def safe_int(val, default=-1):
                    if val is None: return default
                    try: return int(val)
                    except: return default

                # Rollbetter JSON typically has: rank, wins, losses, draws, points
                # Use these as Swiss stats (and general stats if no cut)
                player_rank = safe_int(player.get("rank"), 0)
                if isinstance(player.get("rank"), dict):
                    # Handle nested rank object: {"swiss": 1, "elimination": 2}
                    pr_dict = player.get("rank")
                    player_rank = safe_int(pr_dict.get("swiss", pr_dict.get("elimination", 0)), 0)
                
                swiss_wins = safe_int(player.get("wins"), -1)
                swiss_losses = safe_int(player.get("losses"), -1)
                swiss_draws = safe_int(player.get("draws"), 0)
                # Points can be "points" or "tournament_points"
                swiss_points = safe_int(player.get("points"), safe_int(player.get("tournament_points"), -1))
                
                pr = PlayerResult(
                    tournament_id=int(tid),
                    player_name=player.get("name", "Unknown"),
                    swiss_rank=player_rank,
                    swiss_points=swiss_points,
                    swiss_wins=swiss_wins,
                    swiss_losses=swiss_losses,
                    swiss_draws=swiss_draws,
                    list_json=list_json
                )
                
                results.append(pr)
        except Exception as e:
            logger.error(f"Error checking LF data for {tid}: {e}")
            import traceback
            traceback.print_exc()
            # We still want to allow scraping other data, but players might be empty if we rely on JSON
        
        # Format Inference
        f = Format.OTHER
        for p in results[:10]:
            if p.list_json and p.list_json.get("pilots"):
                inferred = infer_format_from_xws(p.list_json)
                if inferred != Format.OTHER:
                    f = inferred; break
        t.format = f
        
        return {'tournament': t, 'players': results, 'matches': []}

    def _scrape_detailed_matches(self, page, tid: str) -> list[Match]:
        """
        Scrape matches from the 'Rounds' tab.
        """
        matches = []
        try:
            # 1. Go to Rounds tab
            rounds_tab = page.locator("button[id$='-tab-rounds']").first
            if rounds_tab.count() == 0:
                logger.warning("Rounds tab not found.")
                return []
            
            rounds_tab.click()
            logger.info("Clicked Rounds tab. Waiting for sub-tabs...")
            page.wait_for_timeout(2000) # Slightly longer wait
            
            # 2. Find all round sub-tabs
            import re
            round_btns = page.get_by_role("tab", name=re.compile(r"Round \d+", re.IGNORECASE)).all()
            
            if not round_btns:
                logger.info("Found no 'Round' role tabs, trying generic buttons...")
                all_btns = page.locator("button").all()
                round_btns = [b for b in all_btns if "Round" in (b.inner_text() or "")]
            
            if not round_btns:
                logger.warning("No round buttons found.")
                return []

            logger.info(f"Found {len(round_btns)} rounds to scrape.")
            
            for r_idx, btn in enumerate(round_btns):
                try:
                    btn_text = btn.inner_text()
                    logger.info(f"Scraping {btn_text}...")
                    
                    round_type = RoundType.SWISS
                    if "Top" in btn_text or "Elimination" in btn_text or "Cut" in btn_text:
                        round_type = RoundType.CUT
                        
                    btn.click()
                    page.wait_for_timeout(2000) 
                    
                    # Extract Scenario
                    scenario_text = ""
                    scenario_el = page.locator("div:has-text('Scenario:'), p:has-text('Scenario:'), b:has-text('Scenario:')").last
                    if scenario_el.count() > 0:
                        text = scenario_el.inner_text().strip()
                        if "Scenario:" in text:
                            scenario_text = text.split("Scenario:")[1].strip()
                    
                    # Map Scenario Enum
                    scenario_val = None
                    if scenario_text:
                        s_norm = scenario_text.lower().replace(" ", "_")
                        for s in Scenario:
                            if s.value == s_norm: scenario_val = s; break
                    
                    # Extract Matches
                    # Find the table that contains 'Player' or 'Result'
                    table = page.locator("table:has(th:has-text('Result')), table:has(td:has-text('Win'))").last
                    if table.count() == 0:
                        logger.warning(f"No match table found for round {r_idx+1}")
                        continue
                        
                    # New Logic: Iterate rows and look for pairs based on rowspan
                    # Rollbetter Structure: 
                    # Row 1 (Top): [Table# rowspan=2] [P1 Name] [Result] [EP] [Score/MP]
                    # Row 2 (Bot): [P2 Name] [Result] [EP] [Score/MP]
                    
                    # Convert to ElementHandle for query_selector_all support
                    table_el = table.element_handle()
                    if not table_el:
                         logger.warning(f"Could not get element handle for table round {r_idx+1}")
                         continue
                         
                    rows = table_el.query_selector_all("tbody tr")
                    if not rows:
                         rows = table_el.query_selector_all("tr")
                         
                    i = 0
                    while i < len(rows):
                        row1 = rows[i]
                        # Skip headers if encountered (usually index 0, handled by logic or data attributes)
                        if row1.query_selector("th"):
                            i += 1
                            continue

                        cells1 = row1.query_selector_all("td")
                        if not cells1: 
                            i += 1
                            continue
                            
                        # Check for rowspan on the first cell (Table #)
                        first_cell_attr = cells1[0].get_attribute("rowspan")
                        is_paired = first_cell_attr == "2"
                        
                        if is_paired and i + 1 < len(rows):
                            row2 = rows[i+1]
                            cells2 = row2.query_selector_all("td")
                            
                            # Extract P1 (Row 1)
                            # Offset: cell 0 is Table#, cell 1 is Name, 2 is Result, 3 is EP, 4 is Score
                            
                            if len(cells1) >= 5:
                                p1_name = cells1[1].inner_text().strip()
                                p1_res = cells1[2].inner_text().strip().lower() # "win" or "loss"
                                p1_score = self._parse_int(cells1[4].inner_text())
                            else:
                                p1_name = "Unknown"
                                p1_score = 0
                                p1_res = ""

                            # Extract P2 (Row 2) which has NO Table# cell
                            # Indices shifted: cell 0 is Name, 1 is Result, 2 is EP, 3 is Score
                            if len(cells2) >= 4:
                                p2_name = cells2[0].inner_text().strip()
                                p2_res = cells2[1].inner_text().strip().lower()
                                p2_score = self._parse_int(cells2[3].inner_text())
                            else:
                                p2_name = "Unknown"
                                p2_score = 0
                                p2_res = ""
                                
                            # Refine Winner
                            winner_name = None
                            if "win" in p1_res: winner_name = p1_name
                            elif "win" in p2_res: winner_name = p2_name
                            
                            # Detect Bye
                            is_bye = False
                            if "bye" in str(p2_name).lower() or not p2_name or p2_name == "Unknown":
                                 is_bye = True
                                 p2_name = None 
                            
                            m_dict = {
                                "round_number": r_idx + 1,
                                "round_type": round_type,
                                "scenario": scenario_val,
                                "player1_score": p1_score,
                                "player2_score": p2_score,
                                "is_bye": is_bye,
                                "p1_name_temp": p1_name,
                                "p2_name_temp": p2_name,
                                "winner_name_temp": winner_name
                            }
                            matches.append(m_dict)
                            
                            i += 2 # Skip the second row of the pair
                            
                        else:
                            # Single or Bye row
                            if len(cells1) >= 2:
                                p1_name = cells1[1].inner_text().strip()
                                m_dict = {
                                    "round_number": r_idx + 1,
                                    "round_type": round_type,
                                    "scenario": scenario_val,
                                    "player1_score": 0,
                                    "player2_score": 0,
                                    "is_bye": True,
                                    "p1_name_temp": p1_name,
                                    "p2_name_temp": None,
                                    "winner_name_temp": p1_name
                                }
                                matches.append(m_dict)
                            i += 1
                except Exception as round_err:
                    logger.warning(f"Error scraping round {r_idx+1}: {round_err}")
            
        except Exception as e:
            logger.warning(f"Detailed match scrape failed: {e}")
            
        return matches

