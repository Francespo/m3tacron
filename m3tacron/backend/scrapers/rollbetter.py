"""
RollBetter Scraper Implementation (Playwright).

This module implements the scraping logic for rollbetter.gg using Playwright,
as the public API is unreliable or non-existent for many tournaments.
"""
import json
import logging
import re
from datetime import datetime

from urllib.parse import unquote

from playwright.sync_api import sync_playwright

# Local Imports
from .base import BaseScraper
from ..models import Tournament, PlayerResult, Match
from ..enums.formats import Format, infer_format_from_xws
from ..enums.factions import Faction
from ..enums.factions import Faction
from ..enums.platforms import Platform
from ..enums.round_types import RoundType
from ..enums.scenarios import Scenario

logger = logging.getLogger(__name__)

class RollbetterScraper(BaseScraper):
    """
    Scraper for RollBetter.gg tournaments using Playwright.
    """
    
    BASE_URL = "https://rollbetter.gg"

    def get_tournament_data(self, tournament_id: str) -> Tournament:
        """
        Scrape high-level tournament metadata from the main page.
        """
        url = f"{self.BASE_URL}/tournaments/{tournament_id}"
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            try:
                page.goto(url, wait_until="domcontentloaded")
                # Wait for title to appear
                page.wait_for_selector("h1", timeout=10000)
                
                # Scrape Title
                name = page.locator("h1").first.inner_text().strip()
                
                # Scrape Date
                date_obj = datetime.now()
                try:
                    # Look for calendar icon
                    # The date is usually in the parent or next sibling of .fa-calendar
                    if page.locator(".bi-calendar, .fa-calendar").count() > 0:
                        icon = page.locator(".bi-calendar, .fa-calendar").first
                        # Try parent text
                        parent_text = icon.locator("..").inner_text()
                        # Regex for date
                        match = re.search(r"([A-Za-z]{3})\s+(\d{1,2}),\s+(\d{4})", parent_text)
                        if match:
                             date_str = match.group(0)
                             date_obj = datetime.strptime(date_str, "%b %d, %Y")
                    # Fallback: Body regex
                    else:
                        body_text = page.locator("body").inner_text()
                        match = re.search(r"([A-Za-z]{3})\s+(\d{1,2}),\s+(\d{4})", body_text)
                        if match:
                             date_str = match.group(0)
                             date_obj = datetime.strptime(date_str, "%b %d, %Y")
                except Exception as e:
                    logger.warning(f"Date extraction failed: {e}")

                # Player Count
                # Look for badge "X/Y" e.g. "6/16"
                player_count = 0
                try:
                    badges = page.locator(".badge").all_inner_texts()
                    for b in badges:
                        if "/" in b:
                             parts = b.split("/")
                             if parts[0].strip().isdigit():
                                 player_count = int(parts[0].strip())
                                 break
                except Exception as e:
                    logger.warning(f"Count extraction failed: {e}")

                return Tournament(
                    id=int(tournament_id),
                    name=name,
                    date=date_obj.date(),
                    format=None, # Inferred later
                    player_count=player_count,
                    platform=Platform.ROLLBETTER,
                    url=url
                )
            except Exception as e:
                logger.error(f"Failed to scrape tournament {tournament_id}: {e}")
                raise e
            finally:
                browser.close()

    def get_participants(self, tournament_id: str) -> list[PlayerResult]:
        """
        Scrape players and lists.
        """
        ladder_url = f"{self.BASE_URL}/tournaments/{tournament_id}"
        lists_url = f"{self.BASE_URL}/tournaments/{tournament_id}/lists"
        
        participants_map: dict[str, PlayerResult] = {}
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            try:
                # 1. LADDER
                page.goto(ladder_url, wait_until="domcontentloaded")
                try: page.wait_for_selector("table tr", timeout=5000)
                except: pass
                
                ladder_data = page.evaluate("""() => {
                    const rows = Array.from(document.querySelectorAll("table tr"));
                    const headers = Array.from(document.querySelectorAll("table th"));
                    let wdlIndex = headers.findIndex(h => h.innerText.includes("W/D/L"));
                    if (wdlIndex === -1) wdlIndex = 5; 
                    
                    const players = [];
                    for (const row of rows) {
                        const nameEl = row.querySelector(".fancy-link") || row.querySelector("a[href*='/player/']");
                        if (!nameEl) continue;
                        const name = nameEl.innerText.trim();
                        const cells = row.querySelectorAll("td");
                        let rank = 0, points = 0;
                        if (cells.length > 0) rank = parseInt(cells[0].innerText) || 0;
                        if (cells.length > 4) points = parseInt(cells[4].innerText) || 0;
                        
                        let wins = 0, losses = 0, draws = 0;
                        if (cells.length > wdlIndex) {
                             const parts = cells[wdlIndex].innerText.trim().split("/");
                             if (parts.length === 3) {
                                  wins = parseInt(parts[0])||0; draws = parseInt(parts[1])||0; losses = parseInt(parts[2])||0;
                             }
                        }
                        players.push({name, rank, points, wins, losses, draws});
                    }
                    return players;
                }""")
                
                for d in ladder_data:
                    participants_map[d["name"]] = PlayerResult(
                        tournament_id=int(tournament_id),
                        player_name=d["name"],
                        list_json={},
                        rank=d["rank"],
                        swiss_rank=d["rank"],
                        points_at_event=d["points"],
                        swiss_wins=d["wins"],
                        swiss_losses=d["losses"],
                        swiss_draws=d["draws"]
                    )
                logger.info(f"Ladder: Found {len(participants_map)} players.")

                # 2. LISTS
                page.goto(lists_url, wait_until="domcontentloaded")
                
                # Check if hidden
                if page.get_by_text("Lists are hidden").count() > 0:
                    logger.warning(f"Lists are explicitly hidden for tournament {tournament_id}.")
                else:
                    page_num = 1
                    matched_total = 0
                    
                    while True:
                        logger.info(f"Scraping Lists Page {page_num}...")
                        try:
                            # Wait for ANY content that might have lists
                            page.wait_for_selector("button", timeout=4000)
                        except:
                             pass

                        page_lists = page.evaluate("""async (names) => {
                            const results = [];
                            // Target specific XWS buttons or generic fallback
                            const buttons = Array.from(document.querySelectorAll("button"))
                                            .filter(b => b.innerText.includes("Copy XWS") || b.innerText.includes("Export XWS"));
                            
                            let lastCopied = null;
                            const originalWrite = navigator.clipboard.writeText;
                            navigator.clipboard.writeText = async (t) => { lastCopied = t; };

                            const players = names; // Injected variable? No, need to pass it.
                            
                            for (const btn of buttons) {
                                let current = btn;
                                let bestXws = null;
                                let matchedName = null;
                                
                                btn.click();
                                await new Promise(r => setTimeout(r, 10));
                                if (lastCopied) {
                                    try { bestXws = JSON.parse(lastCopied); } catch(e){}
                                    lastCopied = null;
                                }
                                if (!bestXws) continue;

                                // Traverse up to find name
                                let temp = btn;
                                for(let i=0; i<6; i++) {
                                     if(!temp) break;
                                     
                                     // 1. Check Previous Sibling (Header)
                                     if (temp.previousElementSibling) {
                                          const sibText = temp.previousElementSibling.innerText;
                                          for (const p of players) {
                                               if (sibText.includes(p)) {
                                                    matchedName = p;
                                                    break;
                                               }
                                          }
                                     }
                                     if (matchedName) break;

                                     // 2. Check Container Text (Wrapper)
                                     // Be careful not to match "Search" or huge grids
                                     // Only check if length is reasonable? Or just check inclusion.
                                     // If we are at a high level (Grid), it might contain ALL names.
                                     // But usually "Search | IRIS | ..." means IRIS is first.
                                     // We verify strict containment. 
                                     
                                     // NOTE: Checking container text is risky if it contains multiple players.
                                     // But if we are deeper than the Grid, it is safe.
                                     // We can trust Sibling Check more.
                                     
                                     // Let's rely on Sibling Check primarily?
                                     // What if Name is inside the wrapper?
                                     
                                     // Check Inner Text
                                     const txt = temp.innerText;
                                     // Optimization: Only check if txt length is not huge
                                     if (txt.length < 500) {
                                         for (const p of players) {
                                             if (txt.includes(p)) {
                                                  matchedName = p;
                                                  break;
                                             }
                                         }
                                     }
                                     if (matchedName) break;
                                     
                                     temp = temp.parentElement;
                                }
                                
                                if (matchedName) {
                                     results.push({name: matchedName, xws: bestXws});
                                }
                            }
                            navigator.clipboard.writeText = originalWrite;
                            return results;
                        }""", sorted(participants_map.keys(), key=len, reverse=True))
                        
                        logger.info(f"Raw lists found on page {page_num}: {len(page_lists)}")
                        
                        names_desc = sorted(participants_map.keys(), key=len, reverse=True)
                        
                        for item in page_lists:
                            if not item.get("name"): continue
                            
                            p_name = item["name"]
                            if p_name in participants_map:
                                participants_map[p_name].list_json = item["xws"]
                                matched_total += 1
                        
                        # Pagination
                        next_loc = page.locator("ul.pagination li.page-item:not(.disabled) a[aria-label='Next'], ul.pagination li.page-item:not(.disabled) a:has-text('›')")
                        if next_loc.count() > 0 and next_loc.first.is_visible():
                            next_loc.first.click()
                            page.wait_for_timeout(2000)
                            page_num += 1
                        else:
                            break
                    
                    logger.info(f"Lists: Matched {matched_total} XWS lists.")

            except Exception as e:
                logger.error(f"Error scraping participants: {e}")
            finally:
                browser.close()
        return list(participants_map.values())

    def get_matches(self, tournament_id: str) -> list[Match]:
        """
        Scrape matches.
        """
        url = f"{self.BASE_URL}/tournaments/{tournament_id}"
        matches = []
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            try:
                page.goto(url, wait_until="domcontentloaded")
                
                # Navigate to Rounds
                try:
                    page.locator("a.nav-link:has-text('Rounds'), button.nav-link:has-text('Rounds')").first.click()
                    page.wait_for_timeout(2000) # Wait for component load
                except:
                    logger.warning("No Rounds tab.")
                    return []

                # Filter TABS by Allowlist (Safer)
                possible_tabs = page.locator("button.nav-link.no-wrap-tab").all()
                valid_tabs = []
                
                # We only want tabs that look like tournament rounds
                allowed_prefixes = ["Round", "Top", "Cut", "Final", "Bracket", "Swiss", "Group"]
                
                logger.info(f"Total potential tabs found: {len(possible_tabs)}")
                
                for t in possible_tabs:
                    txt = t.inner_text().strip()
                    if txt == "Rounds": continue
                    
                    # Check prefix
                    is_valid = False
                    for prefix in allowed_prefixes:
                        if txt.startswith(prefix) or txt == prefix: # Exact or prefix
                            is_valid = True
                            break
                    
                    if is_valid:
                        valid_tabs.append(t)
                        logger.info(f"  [Use] {txt}")
                    else:
                        logger.info(f"  [Skip] {txt}")
                
                logger.info(f"Valid Rounds found: {len(valid_tabs)}")
                
                # If no tabs found, maybe it's just a single page? Check if there's a table.
                if not valid_tabs and page.locator("table").count() > 0:
                     logger.info("No tabs found, checking for existing table as single round.")
                     valid_tabs = [None] # Mock a 'Round 1' tab for loop

                for i, tab in enumerate(valid_tabs):
                    if tab:
                        round_name = tab.inner_text().strip()
                        logger.info(f"Scraping Round {i+1}: {round_name}")
                        tab.click()
                        page.wait_for_timeout(1000)
                    else:
                        round_name = "Round 1"
                        logger.info("Scraping default view as Round 1")
                    
                    # Extract Scenario
                    # Scope to the active tab pane to avoid grabbing hidden text from other rounds
                    current_scenario = None
                    try:
                        # Find the active tab pane. 
                        # Usually .tab-content > .tab-pane.active
                        active_pane = page.locator(".tab-pane.active")
                        if active_pane.count() > 0:
                            scenario_el = active_pane.locator("div:has-text('Scenario:')").first
                            if scenario_el.count() > 0 and scenario_el.is_visible():
                                txt = scenario_el.inner_text()
                                if "Scenario:" in txt:
                                    val = txt.split("Scenario:")[1].strip()
                                    val = val.split("\n")[0].strip()
                                    
                                    from m3tacron.backend.enums.scenarios import Scenario
                                    for s in Scenario:
                                        if s.label.lower() == val.lower():
                                            current_scenario = s
                                            logger.info(f"Found Scenario: {s.label}")
                                            break
                    except Exception as e:
                        logger.warning(f"Could not extract scenario: {e}")

                    # Scrape Table
                    try:
                        rows = page.locator("table tr").all()
                    except:
                        rows = []
                        
                    # Use generic scraping
                    rr_data = page.evaluate("""() => {
                        const rows = Array.from(document.querySelectorAll("table tr"));
                        const matches = [];
                        for (let i=0; i<rows.length; i++) {
                            const r = rows[i];
                            const next = r.nextElementSibling;
                            
                            // Check if this looks like a match row 
                            // Rollbetter matches are typically pairs of rows (one per player)
                            if (!next) continue;
                            
                            // Extract Names
                            const get_name = (el) => {
                                 let n = el.querySelector(".fancy-link") || el.querySelector("a[href*='/player/']");
                                 return n ? n.innerText.trim() : null;
                            };
                            
                            const p1 = get_name(r);
                            const p2 = get_name(next);
                            
                            if (p1 && p2) {
                                // Scores
                                const getScore = (el) => {
                                    const cells = el.querySelectorAll("td");
                                    if (cells.length > 4) return parseInt(cells[4].innerText)||0;
                                    return 0;
                                };
                                const s1 = getScore(r);
                                const s2 = getScore(next);
                                
                                // Winner
                                const isWin = (el) => el.innerText.includes("Win") || !!el.querySelector(".bi-check-circle-fill");
                                const p1Win = isWin(r);
                                const p2Win = isWin(next);
                                
                                matches.push({p1, p2, p1Win, p2Win, s1, s2});
                            }
                        }
                        return matches;
                    }""")
                    
                    seen_matches = set()
                    
                    for m_dat in rr_data:
                        # Composite key
                        key = tuple(sorted([m_dat['p1'], m_dat['p2']]))
                        if key in seen_matches: continue
                        seen_matches.add(key)
                        
                        is_bye = (m_dat['p2'] == "Bye")
                        
                        # Match Round Type
                        # from m3tacron.backend.enums.matches import RoundType # Already imported at top
                        current_round_type = RoundType.SWISS
                        lower_name = round_name.lower()
                        if "cut" in lower_name or "top" in lower_name or "final" in lower_name or "bracket" in lower_name:
                             current_round_type = RoundType.CUT

                        m = Match(
                            tournament_id=int(tournament_id),
                            round_number=i+1, 
                            round_type=current_round_type,
                            scenario=current_scenario, # New Field
                            player1_id=0, player2_id=0, winner_id=0,
                            player1_score=m_dat['s1'],
                            player2_score=m_dat['s2'],
                            is_bye=is_bye
                        )
                        m.p1_name_temp = m_dat['p1']
                        m.p2_name_temp = m_dat['p2']
                        if m_dat['p1Win']: m.winner_name_temp = m_dat['p1']
                        elif m_dat['p2Win']: m.winner_name_temp = m_dat['p2']
                        
                        matches.append(m)

            except Exception as e:
                logger.error(f"Error scraping matches: {e}")
            finally:
                browser.close()
        return matches

    def run_full_scrape(
        self, 
        tournament_id: str
    ) -> tuple[Tournament, list[PlayerResult], list[Match]]:
        """
        Execute a complete scrape, inferring format from XWS.
        """
        # 1. Metadata
        tournament = self.get_tournament_data(tournament_id)
        
        # 2. Players
        players = self.get_participants(tournament_id)
        
        # 3. Infer Format from Players' XWS
        if not tournament.format:
            # Check up to first 20 players to find a valid format
            # Prioritize players who actually have lists
            for p in players[:20]:
                if p.list_json:
                    format_enum = infer_format_from_xws(p.list_json)
                    if format_enum != Format.OTHER:
                        tournament.format = format_enum
                        logger.info(f"Inferred format {format_enum.value} from player {p.player_name}")
                        break
            
            # If still None
            if not tournament.format:
                logger.warning(f"Could not infer format for {tournament_id}, defaulting to Other")

                tournament.format = Format.OTHER

        # 4. Matches
        matches = self.get_matches(tournament_id)
        
        return tournament, players, matches
