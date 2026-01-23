
import logging
import re
from playwright.sync_api import sync_playwright

from .base import BaseScraper
from .longshanks import LongshanksScraper
from ..models import PlayerResult
from ..utils import parse_builder_url

logger = logging.getLogger(__name__)

class LongshanksScraperV2(LongshanksScraper):
    """
    Optimized Longshanks scraper that extracts list data from the /lists/ endpoint
    instead of clicking individual player modals.
    """
    
    def get_participants(self, tournament_id: str) -> list[PlayerResult]:
        """
        Scrape players and their lists using the mass-list view.
        """
        base_url = f"{self.base_url}/event/{tournament_id}/"
        lists_url = f"{self.base_url}/event/{tournament_id}/lists/"
        
        participants: list[PlayerResult] = []
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context()
            page = context.new_page()
            try:
                # 1. First, go to main event page to get ranks/scores (metdata)
                # The /lists/ page often lacks rank/score info, or it's just a list dump.
                # Actually, /lists/ is just lists. We still need ranking from the main page.
                
                # We can reuse the logic from the parent class to get basic player stats
                # But we need to avoid the slow "extract_lists_from_icons" part.
                
                logger.info(f"V2: Scraping ranking data from {base_url}")
                page.goto(base_url, wait_until="networkidle", timeout=30000)
                self._dismiss_cookie_popup(page)
                
                # Check for squad tab switch if needed (reusing parent logic if accessible, 
                # but parent logic is monolithic in get_participants.
                # We will copy the ranking extraction logic for speed/customization)
                
                # Check for Squad Tournament and switch to individual players tab
                try:
                    squad_tab = page.locator("a[onclick*=\"load_standings('player')\"]").first
                    if squad_tab.count() > 0 and squad_tab.is_visible():
                         squad_tab.click()
                         page.wait_for_load_state("networkidle")
                         page.wait_for_timeout(2000)
                except Exception:
                    pass

                # Extract basic ranking data
                player_data = page.evaluate("""() => {
                    const results = [];
                    const seenNames = new Set();
                    const players = document.querySelectorAll('.player:not(.accordion), .ranking_row');
                    
                    players.forEach((playerEl) => {
                        const rankEl = playerEl.querySelector('.rank');
                        const rank = rankEl ? parseInt(rankEl.textContent.trim()) : 0;
                        if (isNaN(rank) || rank === 0) return;
                        
                        const dataEl = playerEl.querySelector('.data');
                        if (!dataEl) return;
                        
                        const children = dataEl.children;
                        let name = '';
                        const nameDiv = children[0];
                        let external_id = null;
                        
                        if (nameDiv) {
                            const link = nameDiv.querySelector('.player_link, a');
                            if (link) {
                                const clone = link.cloneNode(true);
                                clone.querySelectorAll('span').forEach(s => s.remove());
                                name = clone.textContent.trim();
                                if (link.href) {
                                    const parts = link.href.split('/');
                                    const numeric = parts.filter(p => !isNaN(parseInt(p)) && p.length > 0);
                                    if (numeric.length > 0) external_id = numeric[numeric.length - 1];
                                }
                            } else {
                                name = nameDiv.textContent.trim();
                            }
                            name = name.replace(/\\s*#\\d+$/, '').trim();
                        }
                        
                        if (!name || seenNames.has(name)) return;
                        seenNames.add(name);
                        
                        let wins = 0, losses = 0, draws = 0;
                        for (let i = 4; i < children.length; i++) {
                            const text = children[i].textContent.trim();
                            const wldMatch = text.match(/(\\d+)\\s*\\/\\s*(\\d+)(?:\\s*\\/\\s*(\\d+))?/);
                            if (wldMatch) {
                                wins = parseInt(wldMatch[1]) || 0;
                                losses = parseInt(wldMatch[2]) || 0;
                                draws = wldMatch[3] ? parseInt(wldMatch[3]) : 0;
                                break;
                            }
                        }
                        
                        let points = 0;
                        for (let i = 3; i < children.length; i++) {
                            if (children[i].classList.contains('skinny')) {
                                const pMatch = children[i].textContent.match(/\\d+/);
                                if (pMatch) points = parseInt(pMatch[0]) || 0;
                                break;
                            }
                        }
                        
                        results.push({
                            name: name,
                            external_id: external_id,
                            rank: rank,
                            wins: wins,
                            losses: losses,
                            draws: draws,
                            points: points
                        });
                    });
                    return results;
                }""")
                
                # Convert to PlayerResult objects
                name_to_player = {}
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
                        list_json={} # Will be populated next
                    )
                    if p_data.get("external_id"):
                        pr.external_id = str(p_data["external_id"])
                    
                    participants.append(pr)
                    name_to_player[pr.player_name] = pr
                    
                logger.info(f"V2: Can scrape lists for {len(participants)} players")
                
                # 2. Go to /lists/ page to bulk extract XWS
                logger.info(f"V2: Scraping lists from {lists_url}")
                page.goto(lists_url, wait_until="networkidle", timeout=60000)
                
                # Extract all XWS links mapped by player name
                # Structure: .player_link (Name) -> ... -> XWS List link
                # It's usually a card structure.
                
                lists_data = page.evaluate("""() => {
                    const mappings = [];
                    // Validated Strategy: Each player is in a 'div.column'
                    const columns = document.querySelectorAll('div.column');
                    
                    columns.forEach(col => {
                        // Find player name
                        const nameEl = col.querySelector('.player_link') || col.querySelector('.name');
                        if (!nameEl) return;
                        
                        let name = nameEl.innerText.trim();
                        name = name.replace(/\\s*#\\d+$/, '');
                        
                        // Find list link: Iterate all links to be safe
                        const allLinks = col.querySelectorAll('a');
                        let listLink = null;
                        for (const a of allLinks) {
                            const href = a.href.toLowerCase();
                            if ((href.includes('yasb.app') || href.includes('launchbaynext') || href.includes('xws')) && !href.includes('google')) {
                                listLink = a.href;
                                break;
                            }
                        }
                        
                        if (listLink) {
                            mappings.push({name: name, link: listLink});
                        }
                    });
                    
                    return mappings;
                }""")
                
                count_lists = 0
                for item in lists_data:
                    pname = item["name"]
                    link = item["link"]
                    
                    if pname in name_to_player:
                        # Parse the builder URL (Offline/Passive)
                        xws = parse_builder_url(link)
                        
                        # Check if offline parsing was sufficient (e.g. has pilots)
                        # Current parse_builder_url returns empty pilots for complex YASB links
                        # So we check if we have pilot data.
                        
                        has_pilots = xws.get("pilots") and len(xws["pilots"]) > 0
                        
                        # Strategy: If passive failed, go active (FETCH)
                        if not has_pilots and ("yasb.app" in link):
                            logger.info(f"V2: Passive parse incomplete for {pname}, fetching active export...")
                            fetched_xws = self._fetch_active_xws(page, link)
                            if fetched_xws:
                                xws = fetched_xws
                                # Merge vendor link if lost
                                if "vendor" not in xws: xws["vendor"] = {}
                                if "yasb" not in xws["vendor"]: xws["vendor"]["yasb"] = {"link": link}
                        
                        # Store the link in vendor data regardless
                        if "vendor" not in xws:
                            xws["vendor"] = {}
                        
                        # Determine vendor key
                        v_key = "yasb" if "yasb" in link else "lbn" if "launchbay" in link else "other"
                        if v_key not in xws["vendor"]:
                            xws["vendor"][v_key] = {"link": link}
                        
                        name_to_player[pname].list_json = xws
                        count_lists += 1
                    else:
                        logger.warning(f"V2 Match Fail: List for '{pname}' not in participants. Keys: {list(name_to_player.keys())[:3]}...")
                
                logger.info(f"V2: Extracted {count_lists} lists from bulk page. Found {len(lists_data)} raw mappings.")
                
            except Exception as e:
                logger.error(f"V2 Scraper failed: {e}")
                # Fallback? No, just raise or return what we have
            finally:
                browser.close()
                
        return participants

    def _fetch_active_xws(self, current_page, url) -> dict | None:
        """
        Active fetch using the existing browser context (new tab).
        Avoids nested sync_playwright calls.
        """
        new_page = current_page.context.new_page()
        try:
            new_page.goto(url, wait_until="networkidle", timeout=30000)
            
            # YASB Logic
            if "yasb.app" in url:
                try:
                   export_locator = new_page.locator("button.view-as-text")
                   export_locator.first.wait_for(state="attached", timeout=10000)
                   new_page.evaluate("document.querySelector('button.view-as-text').click()")
                   
                   xws_locator = new_page.locator("button.select-xws-view")
                   xws_locator.first.wait_for(state="attached", timeout=10000)
                   new_page.evaluate("document.querySelector('button.select-xws-view').click()")
                   
                   textarea = new_page.locator("textarea").first
                   for _ in range(10):
                       content = textarea.input_value()
                       if content and len(content) > 10:
                           return json.loads(content)
                       new_page.wait_for_timeout(500)
                except Exception as e:
                   logger.warning(f"Active fetch failed for {url}: {e}")
                   return None
            
            return None
        except Exception as e:
            logger.warning(f"Failed to open builder page {url}: {e}")
            return None
        finally:
            new_page.close()
