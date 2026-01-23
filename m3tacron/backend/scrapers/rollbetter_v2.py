
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

class RollbetterScraperV2(BaseScraper):
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

    def _ensure_data(self, tournament_id: str):
        """Load data if not in cache."""
        if tournament_id in self.cache:
            return
        
        # Scrape
        url = f"{self.BASE_URL}/tournaments/{tournament_id}"
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            try:
                page.goto(url, wait_until="networkidle", timeout=60000)
                
                # Check validation (throws error if fails)
                if not self._validate_page(page, tournament_id):
                    raise ValueError("Tournament failed validation")

                # Try ListFortress Export
                lf_data = self._try_listfortress_export(page)
                
                # Capture Location from Page (since LF JSON might not have it)
                location_data = None
                try:
                    # Strategy 1: Icons (wait for them)
                    try:
                        page.wait_for_selector(".bi-geo-alt, .fa-map-marker-alt, .fa-map-marker", timeout=3000)
                    except:
                        pass
                        
                    loc_icon = page.locator(".bi-geo-alt, .fa-map-marker-alt, .fa-map-marker").first
                    if loc_icon.count() > 0:
                        full_text = loc_icon.locator("..").inner_text().strip()
                        if full_text:
                            parts = [p.strip() for p in full_text.split(',')]
                            location_data = Location.create(
                                city=parts[0],
                                country=parts[2] if len(parts) > 2 else "US"
                            )
                    
                    # Strategy 2: Fallback to text blocks
                    if not location_data:
                        try:
                            page.wait_for_selector("div.overflow-protected", timeout=3000)
                        except: pass
                        
                        blocks = page.locator("div.overflow-protected").all()
                        for block in blocks:
                            text = block.inner_text().strip()
                            if text in ["Started", "Open", "More", "Show More", "List Fortress", "In Person", "Online"]: continue
                            if "X-Wing" in text or "Standard" in text or "Legacy" in text or "Round" in text: continue
                            if ":" in text and ("AM" in text or "PM" in text): continue
                            
                            if "," in text and len(text) < 100:
                                parts = [p.strip() for p in text.split(',')]
                                location_data = Location.create(
                                    city=parts[0],
                                    country=parts[2] if len(parts) > 2 else "US"
                                )
                                break
                except: pass

                if lf_data:
                    logger.info(f"Using LF JSON for {tournament_id}")
                    self.cache[tournament_id] = self._parse_from_json(lf_data, tournament_id, url, location_data)
                else:
                     logger.info(f"Fallback HTML for {tournament_id}")
                     self.cache[tournament_id] = self._scrape_html_fallback(page, tournament_id, url, location_data)
                     
            finally:
                browser.close()

    def get_tournament_data(self, tournament_id: str) -> Tournament:
        self._ensure_data(tournament_id)
        return self.cache[tournament_id]['tournament']

    def get_participants(self, tournament_id: str) -> list[PlayerResult]:
        self._ensure_data(tournament_id)
        return self.cache[tournament_id]['players']

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

    def _try_listfortress_export(self, page) -> dict | None:
        try:
            # The button text is "List Fortress" (with space) or has the LF icon
            export_btn = page.locator("button:has-text('List Fortress')").first
            
            if export_btn.count() > 0:
                logger.info("Found List Fortress export button. Opening modal...")
                export_btn.click()
                
                # Wait for the modal and the "Calculate" button
                calc_btn = page.locator("button:has-text('Calculate List Fortress JSON')")
                try:
                    calc_btn.wait_for(timeout=5000)
                    calc_btn.click()
                    logger.info("Triggered JSON calculation...")
                    
                    # Wait for the textarea to be populated
                    textarea = page.locator("textarea")
                    # textarea might take a few seconds
                    for _ in range(10):
                        val = textarea.input_value()
                        if val and val.strip().startswith("{"):
                            return json.loads(val)
                        page.wait_for_timeout(1000)
                except Exception as e:
                    logger.warning(f"Could not calculate LF JSON: {e}")
            
            return None
        except Exception as e:
            logger.warning(f"List Fortress export failed or not found: {e}")
            return None

    def _parse_from_json(self, data: dict, tid: str, url: str, location_data: dict | None = None):
        # ... JSON parsing logic from previous step ...
        # (I will reimplement cleanly here to match cache structure)
        
        # Tournament
        name = data.get("title", f"Rollbetter Event {tid}")
        date_str = data.get("date", "")
        try: date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
        except: date_obj = datetime.now().date()
        
        # Players
        players_json = data.get("players", [])
        t = Tournament(
            id=int(tid), name=name, date=date_obj,
            location=location_data,
            player_count=len(players_json), platform=Platform.ROLLBETTER, url=url, format=Format.OTHER
        )

        participants = []
        for p in players_json:
            # LF JSON from RollBetter often has NO list or a STRINGIFIED list
            raw_list = p.get("list", {})
            list_json = {}
            if isinstance(raw_list, str) and raw_list.strip():
                try:
                    list_json = json.loads(raw_list)
                except:
                    logger.warning(f"Failed to parse stringified list for {p.get('name')}")
            elif isinstance(raw_list, dict):
                list_json = raw_list
            
            pr = PlayerResult(
                tournament_id=int(tid),
                player_name=p.get("name", "Unknown"),
                rank=p.get("rank", {}).get("swiss", 0) if isinstance(p.get("rank"), dict) else p.get("rank", 0),
                swiss_rank=p.get("swiss_rank", 0), # Fallback
                points_at_event=p.get("score", 0),
                list_json=list_json
            )
            pr.temp_lf_id = p.get("id")
            participants.append(pr)
            
        # Matches
        matches = []
        rounds_json = data.get("rounds", [])
        for r_idx, r in enumerate(rounds_json):
            round_type = RoundType.SWISS
            if r.get("round-type") == "elimination": round_type = RoundType.CUT
            
            for m_data in r.get("matches", []):
                p1_lf_id = m_data.get("player1-id") or m_data.get("player1_id")
                p2_lf_id = m_data.get("player2-id") or m_data.get("player2_id")
                w_lf_id = m_data.get("winner-id") or m_data.get("winner_id")
                
                m = Match(
                    tournament_id=int(tid),
                    round_number=r_idx + 1,
                    round_type=round_type,
                    player1_score=m_data.get("player1_points", 0),
                    player2_score=m_data.get("player2_points", 0),
                    winner_id=0, # Placeholder
                    is_bye=(p2_lf_id is None)
                )
                
                # Map names
                p1 = next((x for x in participants if getattr(x, 'temp_lf_id') == p1_lf_id), None)
                p2 = next((x for x in participants if getattr(x, 'temp_lf_id') == p2_lf_id), None)
                
                if p1: m.p1_name_temp = p1.player_name
                if p2: m.p2_name_temp = p2.player_name
                if w_lf_id == p1_lf_id and p1: m.winner_name_temp = p1.player_name
                elif w_lf_id == p2_lf_id and p2: m.winner_name_temp = p2.player_name
                
                matches.append(m)
        
        # Format Inference
        f = Format.OTHER
        for p in participants[:10]:
            if p.list_json and p.list_json.get("pilots"):
                inferred = infer_format_from_xws(p.list_json)
                if inferred != Format.OTHER:
                    f = inferred; break
        t.format = f
        
        return {'tournament': t, 'players': participants, 'matches': matches}

    def _scrape_html_fallback(self, page, tid, url, location_data: dict | None = None):
        # Re-implementation of HTML scraping
        name = page.locator("h1").first.inner_text().strip()
        
        date_obj = datetime.now()
        try:
             calendar_icon = page.locator(".bi-calendar, .fa-calendar").first
             if calendar_icon.count() > 0:
                 parent = calendar_icon.locator("..").inner_text()
                 date_obj = self._parse_date(parent)
        except: pass
        
        player_count = 0
        try:
            badges = page.locator(".badge").all_inner_texts()
            for b in badges:
                if "/" in b:
                    parts = b.split("/")
                    if parts[0].strip().isdigit():
                        player_count = int(parts[0].strip())
                        break
        except: pass

        t = Tournament(
            id=int(tid), name=name, date=date_obj.date(), 
            location=location_data,
            player_count=player_count, platform=Platform.ROLLBETTER, url=url, format=Format.OTHER
        )
        
        # Ladder
        ladder_data = page.evaluate("""() => {
            const rows = Array.from(document.querySelectorAll("table tr"));
            const players = [];
            for (const row of rows) {
                const nameEl = row.querySelector(".fancy-link") || row.querySelector("a[href*='/player/']");
                if (!nameEl) continue;
                const name = nameEl.innerText.trim();
                const cells = row.querySelectorAll("td");
                let rank = 0, points = 0;
                if (cells.length > 0) rank = parseInt(cells[0].innerText) || 0;
                if (cells.length > 4) points = parseInt(cells[4].innerText) || 0;
                players.push({name, rank, points});
            }
            return players;
        }""")
        
        participants = []
        for d in ladder_data:
            participants.append(PlayerResult(
                tournament_id=int(tid), player_name=d["name"], rank=d["rank"],
                swiss_rank=d["rank"], points_at_event=d["points"], list_json={}
            ))
            
        # Matches (Simplified for V2 fallback)
        matches = []
        # (Assuming main value is JSON, fallback can be basic)
        
        return {'tournament': t, 'players': participants, 'matches': matches}
