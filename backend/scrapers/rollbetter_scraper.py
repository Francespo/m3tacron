
import json
import logging
import re
import urllib.error
import urllib.request
from datetime import datetime, date as date_type
from playwright.sync_api import sync_playwright

from .base import BaseScraper
from ..models import Tournament, PlayerStanding, Match
from ..data_structures.formats import Format, infer_format_from_xws
from ..data_structures.source import Source
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

    def __init__(self, game_id: int | None = None):
        """Initialize scraper.

        Args:
            game_id: Rollbetter game system ID for listing.
                     5=AMG, 17=XWA, 4=2.0/Legacy. None=no listing.
        """
        super().__init__()
        self.game_id = game_id
        self.cache = {}  # Map ID -> dict (full data)

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
                    browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
                    page = browser.new_page()
                    page.goto(url, wait_until="load", timeout=60000)

                    # Wait for data load
                    page.wait_for_timeout(3000)

                    # Check for validation; if it fails, try API fallback before aborting.
                    if not self._validate_page(page, tournament_id):
                        api_data = self._try_fetch_api_data(tournament_id, url)
                        if api_data:
                            self.cache[tournament_id] = api_data
                            return
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
                    except:
                        pass

                    # 2. Look for "List Fortress" link/button
                    # The Rollbetter SPA loads its toolbar asynchronously, so
                    # wait for the button rather than relying on a fixed sleep.
                    lf_btn = page.locator(
                        "a:has-text('List Fortress'), button:has-text('List Fortress')")
                    try:
                        page.wait_for_selector(
                            "a:has-text('List Fortress'), button:has-text('List Fortress')",
                            timeout=20000,
                        )
                    except Exception:
                        pass
                    if lf_btn.count() > 0:
                        logger.info(
                            f"Found List Fortress export button for {tournament_id}")
                        lf_btn.first.click()
                        triggered = True
                    else:
                        # Fallback: maybe just "JSON" or "Export JSON"
                        json_btn = page.locator(
                            "a:has-text('JSON'), button:has-text('JSON')")
                        if json_btn.count() > 0:
                            json_btn.first.click()
                            triggered = True

                    if triggered:
                        logger.info("Triggered JSON calculation...")
                        try:
                            # The modal and its textarea render via the SPA;
                            # wait for the textarea to appear.
                            page.wait_for_selector(
                                "div.modal-content textarea, textarea",
                                timeout=10000,
                            )

                            # The "Calculate List Fortress JSON" button computes
                            # the export server-side; click it whenever present.
                            calc_btn = page.locator(
                                "button:has-text('Calculate List Fortress JSON')")
                            if calc_btn.count() > 0:
                                logger.info(
                                    "Clicked 'Calculate List Fortress JSON'.")
                                calc_btn.first.click()

                            # Poll the textarea until the JSON actually shows up
                            # (computation can take several seconds).
                            ta = page.locator(
                                "div.modal-content textarea, textarea").first
                            for _ in range(30):
                                lf_data = ta.input_value()
                                if lf_data.strip():
                                    break
                                page.wait_for_timeout(1000)
                        except Exception as exc:
                            logger.debug(
                                f"LF export modal interaction failed for {tournament_id}: {exc}")
                            lf_data = ""
                        finally:
                            # Always close the modal — an open modal blocks
                            # every later interaction with the page (fallback
                            # UI scraping would otherwise time out).
                            try:
                                page.keyboard.press("Escape")
                            except Exception:
                                pass

                    if lf_data:
                        logger.info(
                            f"Using LF JSON for {tournament_id} (Length: {len(lf_data)})")
                        self.cache[tournament_id] = self._parse_from_json_v2(json.loads(
                            lf_data) if isinstance(lf_data, str) else lf_data, tid=tournament_id, url=url)

                        # Fix Name from H1 if JSON was generic
                        try:
                            h1_text = page.locator(
                                "h1").first.inner_text().strip()
                            if h1_text and "Rollbetter Event" in self.cache[tournament_id]['tournament'].name:
                                self.cache[tournament_id]['tournament'].name = h1_text
                        except:
                            pass

                        # Now scrape UI for Location and Detailed Matches
                        try:
                            # Refine Date from UI (JSON date often fails or is today)
                            ui_date = self._scrape_date_from_ui(page)
                            if ui_date.date() != datetime.now().date():
                                self.cache[tournament_id]['tournament'].date = ui_date.date(
                                )
                                logger.info(
                                    f"Updated date from UI: {ui_date.date()}")

                            location_data = self._extract_location(page)
                            if location_data:
                                self.cache[tournament_id]['tournament'].location = location_data

                            # Determine Format from Body Text (FALLBACK if XWS inference failed)
                            # XWS inference has priority (already done in _parse_from_json_v2)
                            current_format = self.cache[tournament_id]['tournament'].format
                            if current_format == Format.UNKNOWN:
                                logger.info(
                                    "XWS inference failed or missing. Keeping format as OTHER (Conservative Policy).")
                            else:
                                logger.info(
                                    f"Using XWS-inferred format: {current_format.value}")

                            # Scrape UI Standings for missing stats
                            ui_stats = self._scrape_standings_ui(page)
                            if ui_stats:
                                for p in self.cache[tournament_id]['players']:
                                    key = p.player_name.lower().strip()
                                    if key in ui_stats:
                                        s = ui_stats[key]
                                        if s["wins"] != -1:
                                            p.swiss_wins = s["wins"]
                                        if s["losses"] != -1:
                                            p.swiss_losses = s["losses"]
                                        if s["draws"] != -1:
                                            p.swiss_draws = s["draws"]

                                        # Only update points if NOT Legacy and JSON was empty
                                        if self.cache[tournament_id]['tournament'].format != Format.LEGACY_X2PO:
                                            if (p.swiss_event_points is None or p.swiss_event_points <= 0) and s.get("points", 0) > 0:
                                                p.swiss_event_points = s["points"]

                            # The LF JSON export already carries full round
                            # data; only fall back to the UI tables when the
                            # JSON had no rounds.
                            matches = self.cache[tournament_id]['matches']
                            if not matches:
                                matches = self._scrape_detailed_matches(
                                    page, tournament_id)
                                if matches:
                                    self.cache[tournament_id]['matches'] = matches
                            if matches:
                                # Compute missing stats from matches
                                self._compute_stats_from_matches(
                                    self.cache[tournament_id]['players'], matches, self.cache[tournament_id]['tournament'].format)
                        except Exception as e:
                            logger.warning(
                                f"UI detail scrape failed for {tournament_id}: {e}")

                        return  # Success!

                    # If we got here, we failed to get data
                    logger.warning(
                        f"Attempt {attempt+1}: Failed to extract LF JSON.")

                    # Last attempt: build a UI-only fallback so we still scrape metadata and matches.
                    if attempt == 2:
                        ui_data = self._build_fallback_from_ui(
                            page, tournament_id, url)
                        if ui_data:
                            logger.info(
                                f"Using UI-only fallback for {tournament_id}.")
                            self.cache[tournament_id] = ui_data
                            return

            except Exception as e:
                logger.error(
                    f"Attempt {attempt+1} Error for {tournament_id}: {e}")
                error_trace = e
                # Retry loop continues

        # If LF export flow failed, fall back to the public API.
        api_data = self._try_fetch_api_data(
            tournament_id, f"{self.BASE_URL}/tournaments/{tournament_id}")
        if api_data:
            self.cache[tournament_id] = api_data
            return

        logger.error(
            f"Failed to scrape LF data for {tournament_id} after 3 attempts.")
        if error_trace:
            import traceback
            traceback.print_exc()
        # Raise so worker knows it failed
        raise ValueError("Failed to ensure data")

    def _build_fallback_from_ui(self, page, tournament_id: str, url: str) -> dict | None:
        """Build a minimal dataset from UI when LF JSON is unavailable."""
        try:
            name = f"Rollbetter Event {tournament_id}"
            h1 = page.locator("h1").first
            if h1.count() > 0:
                h1_text = h1.inner_text().strip()
                if h1_text:
                    name = h1_text

            ui_date = self._scrape_date_from_ui(page).date()
            tournament = Tournament(
                id=int(tournament_id),
                name=name,
                date=ui_date,
                player_count=0,
                source=Source.ROLLBETTER,
                url=url,
                format=Format.UNKNOWN,
            )

            location_data = self._extract_location(page)
            if location_data:
                tournament.location = location_data
            else:
                tournament.location = Location.create(
                    city="Unknown",
                    country="Unknown",
                    continent="Unknown",
                )

            # Augment with API timezone for continent if needed
            if not tournament.location.continent or tournament.location.continent == "Unknown":
                try:
                    import urllib.request
                    import json
                    req = urllib.request.Request(
                        f"https://api.rollbetter.gg/tournaments/{tournament_id}",
                        headers={"User-Agent": "Mozilla/5.0",
                                 "Accept": "application/json"}
                    )
                    with urllib.request.urlopen(req, timeout=10) as resp:
                        info = json.loads(resp.read().decode("utf-8"))
                        tz = info.get("timezone") or ""
                        if tz and ":" in tz:
                            cont = tz.split(":")[0].strip()
                            # Use Pydantic/Model assign correctly
                            if hasattr(tournament.location, 'continent'):
                                tournament.location.continent = cont
                except Exception as e:
                    logger.debug(
                        f"Failed to fetch timezone from API for continent fallback: {e}")

            players = self._scrape_players_ui(page)
            matches = self._scrape_detailed_matches(page, tournament_id)

            if not players and matches:
                players = self._build_players_from_matches(matches)

            if matches:
                self._compute_stats_from_matches(
                    players, matches, tournament.format)

            if players:
                tournament.player_count = len(players)

            logger.info(
                "UI fallback built for %s: %s player(s), %s match(es), location=%s",
                tournament_id,
                len(players),
                len(matches),
                tournament.location,
            )

            return {
                "tournament": tournament,
                "players": players,
                "matches": matches,
            }
        except Exception as exc:
            logger.warning(f"UI fallback failed for {tournament_id}: {exc}")
            return None

    def _build_players_from_matches(self, matches: list[dict]) -> list[PlayerStanding]:
        players = {}
        for m in matches:
            for name in [m.get("p1_name_temp"), m.get("p2_name_temp")]:
                if not name:
                    continue
                key = name.strip().lower()
                if key not in players:
                    players[key] = PlayerStanding(
                        player_name=name.strip(),
                        swiss_rank=-1,
                        swiss_wins=-1,
                        swiss_losses=-1,
                        swiss_draws=0,
                        swiss_event_points=None,
                        swiss_tie_breaker_points=-1,
                    )
        return list(players.values())

    def _scrape_players_ui(self, page) -> list[PlayerStanding]:
        """Scrape the Ladder (standings) table into PlayerStanding list.

        Rollbetter's standings tab is called "Ladder"; its columns are
        ``# | Player | List | EP | SOS | MP | W/D/L | Affiliation`` where the
        W/D/L cell uses a slash format (e.g. "3/0/0" = wins/draws/losses).
        """
        players = []
        try:
            ladder_tab = page.locator(
                "button[id$='-tab-ladder'], button[id$='-tab-standings'], "
                "button:has-text('Ladder'), button:has-text('Standings')").first
            if ladder_tab.count() > 0:
                ladder_tab.click()
                page.wait_for_timeout(1500)

            table = page.locator(
                "div.tab-pane.active table:has(th:has-text('W/D/L')), "
                "table:has(th:has-text('W/D/L'))").first
            if table.count() == 0:
                logger.warning("Ladder table not found in UI.")
                return players

            headers = table.locator("thead th").all()
            header_texts = [h.inner_text().strip().lower() for h in headers]

            def _col_idx(*names: str) -> int:
                for n in names:
                    for i, ht in enumerate(header_texts):
                        if n in ht:
                            return i
                return -1

            idx_rank = _col_idx("#", "rank", "position")
            idx_name = _col_idx("player")
            idx_ep = _col_idx("ep", "event points")
            idx_wdl = _col_idx("w/d/l", "w-l", "wl")
            if idx_name < 0 or idx_wdl < 0:
                logger.warning(
                    f"Unexpected ladder columns: {header_texts}")
                return players

            rows = table.locator("tbody tr").all()
            logger.info("Ladder UI rows found: %s", len(rows))

            for row in rows:
                cells = row.locator("td").all()
                if len(cells) <= max(idx_name, idx_wdl):
                    continue

                name = cells[idx_name].inner_text().strip()
                if not name:
                    continue

                rank = -1
                if 0 <= idx_rank < len(cells):
                    rtxt = cells[idx_rank].inner_text().strip()
                    if rtxt.isdigit():
                        rank = int(rtxt)

                wins = -1
                losses = -1
                draws = 0
                points = None

                wdl = cells[idx_wdl].inner_text().strip()
                wdl_match = re.search(r"(\d+)\s*/\s*(\d+)\s*/\s*(\d+)", wdl)
                if wdl_match:
                    wins = int(wdl_match.group(1))
                    draws = int(wdl_match.group(2))
                    losses = int(wdl_match.group(3))

                if 0 <= idx_ep < len(cells):
                    etxt = cells[idx_ep].inner_text().strip()
                    if etxt.isdigit():
                        points = int(etxt)

                players.append(
                    PlayerStanding(
                        player_name=name,
                        swiss_rank=rank,
                        swiss_wins=wins,
                        swiss_losses=losses,
                        swiss_draws=draws,
                        swiss_event_points=points,
                        swiss_tie_breaker_points=-1,
                    )
                )
        except Exception as exc:
            logger.warning(f"Standings UI player scrape failed: {exc}")

        logger.info("Standings UI players parsed: %s", len(players))

        return players

    def _fetch_api_json(self, url: str) -> dict | None:
        try:
            req = urllib.request.Request(
                url,
                headers={
                    "User-Agent": "Mozilla/5.0",
                    "Accept": "application/json",
                },
            )
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except (urllib.error.URLError, json.JSONDecodeError) as exc:
            logger.debug(f"API fetch failed for {url}: {exc}")
            return None

    def _parse_api_date(self, value: str | None) -> datetime:
        if not value:
            return datetime.now()
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return datetime.now()

    def _try_fetch_api_data(self, tournament_id: str, url: str) -> dict | None:
        api_base = f"https://api.rollbetter.gg/tournaments/{tournament_id}"
        info = self._fetch_api_json(api_base)
        players_payload = self._fetch_api_json(f"{api_base}/players")

        if not info or not players_payload:
            return None

        ladder = players_payload.get("ladder", []) or []
        waitlist = players_payload.get("waitlist", []) or []
        player_count = len(ladder) if ladder else info.get(
            "registrationCount", 0) or 0

        if player_count <= 1 and len(waitlist) <= 1:
            logger.warning(
                f"Tournament {tournament_id} has insufficient players (API). Skipping."
            )
            return None

        title = info.get("title") or info.get(
            "name") or f"Rollbetter Event {tournament_id}"
        date_value = info.get("endDate") or info.get("startDate")
        parsed_date = self._parse_api_date(date_value)
        if parsed_date.date() > datetime.now().date():
            logger.warning(
                f"Tournament {tournament_id} is in the future ({parsed_date.date()}). Skipping."
            )
            return None

        location = None
        venue = info.get("venue") or ""
        city = info.get("city") or ""
        state = info.get("stateProvince") or ""
        country = info.get("country") or ""
        attendee_presence = (info.get("attendeePresence") or "").lower()
        location_text = ", ".join(
            [p for p in [venue, city, state, country] if p])

        if "online" in attendee_presence or "virtual" in attendee_presence:
            location = Location.create(
                city="Virtual", country="Virtual", continent="Virtual")
        elif location_text:
            from ..utils.geocoding import resolve_location
            location = resolve_location(location_text)

        tz = info.get("timezone") or ""
        if tz and ":" in tz:
            cont = tz.split(":")[0].strip()
            if location:
                if not location.continent or location.continent == "Unknown":
                    location.continent = cont
            else:
                location = Location.create(
                    city="Unknown", country="Unknown", continent=cont)

        tournament = Tournament(
            id=int(tournament_id),
            name=title,
            date=parsed_date.date(),
            player_count=player_count,
            source=Source.ROLLBETTER,
            url=url,
            format=Format.UNKNOWN,
        )
        if location:
            tournament.location = location

        players = []
        for entry in ladder:
            player = entry.get("player", {}) or {}
            ranking = entry.get("ranking", {}) or {}
            name = player.get("realName") or player.get(
                "username") or "Unknown"

            swiss_points = ranking.get("points1")
            if swiss_points is None:
                swiss_points = ranking.get("combinedPoints1")

            players.append(
                PlayerStanding(
                    player_name=name,
                    swiss_rank=ranking.get("seed") or -1,
                    swiss_wins=ranking.get("wins", -1),
                    swiss_losses=ranking.get("losses", -1),
                    swiss_draws=ranking.get("draws", 0),
                    swiss_event_points=swiss_points,
                    swiss_tie_breaker_points=ranking.get("mov"),
                    cut_rank=ranking.get("elimPlacement"),
                )
            )

        return {
            "tournament": tournament,
            "players": players,
            "matches": [],
        }

    def list_tournaments(
        self,
        date_from: date_type,
        date_to: date_type,
        max_pages: int | None = None
    ) -> list[dict]:
        """Discover tournament URLs from the Rollbetter API.

        Uses the public API directly — a single HTTP request replaces
        ~60 pages of Playwright UI scraping.

        Args:
            date_from: Start of date range (inclusive).
            date_to: End of date range (inclusive).
            max_pages: Unused (API returns all in one call).

        Returns:
            List of dicts: {url, name, date, player_count}.
        """
        if not self.game_id:
            raise ValueError(
                "game_id is required for list_tournaments. Set it in constructor.")

        results = []
        api_url = (
            f"https://api.rollbetter.gg/tournaments"
            f"?skip=0&take=2000&gameId={self.game_id}&when=past"
        )

        data = self._fetch_api_json(api_url)
        if not data:
            logger.warning(
                f"Rollbetter API listing returned no data for gameId={self.game_id}")
            return []

        logger.info(
            f"Rollbetter API returned {data.get('count', 0)} total tournaments for gameId={self.game_id}"
        )

        for t in data.get("tournaments", []):
            try:
                date_str = t.get("endDate") or t.get("startDate")
                t_date = self._parse_api_date(date_str).date()

                # Client-side date filtering
                if t_date < date_from or t_date > date_to:
                    continue

                t_id = t.get("id")
                if not t_id:
                    continue

                title = (t.get("title") or "").strip()
                if not title:
                    title = f"Rollbetter Event {t_id}"

                results.append({
                    "url": f"{self.BASE_URL}/tournaments/{t_id}",
                    "name": title,
                    "date": t_date.isoformat(),
                    "player_count": t.get("maxPlayerCount", 0),
                })
            except Exception as exc:
                logger.debug(f"Skipping malformed API tournament entry: {exc}")

        logger.info(
            f"Discovered {len(results)} tournaments in range "
            f"from Rollbetter (game {self.game_id})."
        )
        return results

    def get_tournament_data(self, tournament_id: str, inferred_format: Format | None = None) -> Tournament:
        self._ensure_data(tournament_id)
        return self.cache[tournament_id]['tournament']

    def get_participants(self, tournament_id: str) -> list[PlayerStanding]:
        self._ensure_data(tournament_id)
        players = self.cache[tournament_id]['players']
        if not players:
            logger.warning(
                f"Rollbetter: No players found for {tournament_id} even after ensure_data.")
        return players

    def get_matches(self, tournament_id: str) -> list[Match]:
        self._ensure_data(tournament_id)
        return self.cache[tournament_id]['matches']

    def _scrape_date_from_ui(self, page) -> datetime:
        try:
            # 1. High Confidence: Event Calendar Icon
            calendar_icon = page.locator(
                ".bi-calendar-event, .bi-calendar-date").first
            if calendar_icon.count() > 0:
                raw_text = calendar_icon.locator("xpath=..").inner_text()
                # Clean hidden characters (NBSP, etc)
                import unicodedata
                clean_text = unicodedata.normalize("NFKD", raw_text).strip()
                return self._parse_date(clean_text)

            # 2. Low Confidence: Generic Icon
            calendar_icon = page.locator(".bi-calendar, .fa-calendar").first
            if calendar_icon.count() > 0:
                parent = calendar_icon.locator("xpath=..").inner_text()
                parsed = self._parse_date(parent)
                if parsed.date() != datetime.now().date():
                    return parsed

            # 3. Last Resort: Search Body Text for "Date: Mmm dd, YYYY" or just the date pattern
            # Using regex on the first 2000 chars of body might be safer/faster
            body_intro = page.locator("body").inner_text()[:2000]
            # Look for specific keys first
            m = re.search(
                r"(?:Date|When):\s*([a-zA-Z]+\s+\d{1,2},?\s+\d{4})", body_intro, re.IGNORECASE)
            if m:
                return self._parse_date(m.group(1))

            # Look for raw date pattern (riskier, but 'Aug 19, 2023' is distinct)
            m2 = re.search(
                r"\b([A-Z][a-z]{2}\s+\d{1,2},?\s+\d{4})\b", body_intro)
            if m2:
                return self._parse_date(m2.group(1))

        except:
            pass
        return datetime.now()

    def _validate_page(self, page, tournament_id) -> bool:
        body_text = page.inner_text("body")

        # 1. Game System
        h1_text = ""
        try:
            h1 = page.locator("h1").first
            if h1.count() > 0:
                h1_text = h1.inner_text()
        except:
            pass

        is_xwing_title = "x-wing" in h1_text.lower()

        if "Marvel Crisis Protocol" in body_text and not is_xwing_title:
            logger.warning(
                f"Tournament {tournament_id} seems to be Marvel Crisis Protocol. Skipping.")
            return False

        if "Star Wars: Legion" in body_text and not is_xwing_title:
            logger.warning(
                f"Tournament {tournament_id} seems to be Legion. Skipping.")
            return False

        if "X-Wing" not in body_text and "Miniatures Game" not in body_text and not is_xwing_title:
            logger.warning(
                f"Tournament {tournament_id} missing 'X-Wing' identifier. Proceeding.")
            # return False

        # Date
        date_obj = self._scrape_date_from_ui(page)

        # Allow "Today" as valid (<=)
        if date_obj.date() > datetime.now().date():
            logger.warning(
                f"Tournament {tournament_id} is in the future ({date_obj.date()}). Skipping.")
            return False

        # Count
        player_count = None
        try:
            badges = page.locator(".badge").all_inner_texts()
            for b in badges:
                if "/" in b:
                    parts = b.split("/")
                    if parts[0].strip().isdigit():
                        player_count = int(parts[0].strip())
                        break
            if player_count is not None and player_count <= 1:
                logger.warning(
                    f"Tournament {tournament_id} has insufficient players. Skipping.")
                return False
        except:
            pass

        return True

    def _extract_location(self, page) -> dict | None:
        from ..utils.geocoding import resolve_location
        from ..data_structures.location import Location
        location_data = None

        # Strategy 0: Scoped Metadata Check (Avoids matching "Online" in description)
        try:
            # The metadata row often has justify-last-start class
            meta_row = page.locator("div.justify-last-start").first
            if meta_row.count() > 0:
                # Check for Online icons/text within this container only
                online_indicators = meta_row.locator(
                    "i.bi-person-video, i.fa-laptop, i.bi-laptop, :text('Online')").all()
                for el in online_indicators:
                    txt = el.inner_text().lower() if el.count() > 0 else ""
                    # Also check parent text if it's just the icon
                    parent_txt = el.locator("..").inner_text().lower()
                    if "online" in txt or "online" in parent_txt:
                        logger.info(
                            f"Found Online indicator in metadata: '{parent_txt}'. Forcing Virtual.")
                        return Location.create(city="Virtual", country="Virtual", continent="Virtual")

                # If we find "In Person" here, we should NOT return Virtual,
                # even if Strategy 2/3 would find it elsewhere.
                in_person = meta_row.locator(
                    "i.bi-person-fill, i.fa-users, :text('In Person')").first
                if in_person.count() > 0:
                    logger.info(
                        "Found 'In Person' in metadata. Avoiding Virtual override.")
                    # Continue to Strategy 1 (standard location resolution)
        except Exception as e:
            logger.debug(f"Metadata scoped check failed: {e}")

        # Check Title for Online/Virtual (High confidence)
        try:
            h1 = page.locator("h1").first
            if h1.count() > 0:
                h1_text = h1.inner_text().lower()
                if "online" in h1_text or "virtual" in h1_text:
                    logger.info(
                        f"Found '{h1_text}' in title. Forcing Virtual.")
                    return Location.create(city="Virtual", country="Virtual", continent="Virtual")
        except:
            pass

        # Strategy 1: Icons (wait for them)
        try:
            page.wait_for_selector(
                ".bi-geo-alt, .fa-map-marker-alt, .fa-map-marker", timeout=3000)
        except:
            pass

        loc_icon = page.locator(
            ".bi-geo-alt, .fa-map-marker-alt, .fa-map-marker").first
        if loc_icon.count() > 0:
            full_text = loc_icon.locator("..").inner_text().strip()
            if full_text:
                # Use new geocoding logic
                location_data = resolve_location(full_text)

        # Strategy 2: Fallback to text blocks
        if not location_data:
            try:
                page.wait_for_selector("div.overflow-protected", timeout=3000)
            except:
                pass

            blocks = page.locator("div.overflow-protected").all()
            for block in blocks:
                text = block.inner_text().strip()
                if text in ["Started", "Open", "More", "Show More", "List Fortress", "In Person"]:
                    continue
                # Handle "Online" explicitly - aggressively
                if "online" in text.lower():
                    return Location.create(city="Virtual", country="Virtual", continent="Virtual")
                if "X-Wing" in text or "Standard" in text or "Legacy" in text or "Round" in text:
                    continue
                if ":" in text and ("AM" in text or "PM" in text):
                    continue

                if len(text) < 100:
                    # Try to resolve any short text block that might be a location
                    loc = resolve_location(text)
                    if loc:
                        location_data = loc
                        break
        return location_data

    # _try_listfortress_export removed as logic moved into _ensure_data retry loop

    def _parse_from_json_v2(self, data: dict, tid: str, url: str):
        """
        Parse Rollbetter's ListFortress JSON export into Tournament + Players
        (+ matches, which the LF JSON carries in its "rounds" payload).

        The LF JSON player entries look like::

            {"name": "lscomanche", "id": "lscomanche", "mov": 96,
             "score": 3, "sos": 2, "rank": {"swiss": 5}, "dropped": false,
             "list": "{...xws json string...}"}

        and the rounds look like::

            {"round-type": "swiss", "round-number": 1, "scenario": "...",
             "matches": [{"player1": ..., "player1-id": ..., "player2": ...,
                          "player1points": 25, "player2points": 27,
                          "winner-id": ..., "result": "win"}, ...]}
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
            try:
                formatted_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            except:
                pass

        # Players
        players_json = data.get("players", []) or data.get(
            "participants", []) or data.get("standings", [])

        t = Tournament(
            id=int(tid), name=name, date=formatted_date,
            player_count=len(players_json), source=Source.ROLLBETTER, url=url, format=Format.UNKNOWN
        )

        results = []
        try:
            for player in players_json:
                raw_list = player.get("list", {})
                list_json = {}
                if isinstance(raw_list, str) and raw_list.strip():
                    try:
                        list_json = json.loads(raw_list)
                    except:
                        pass
                elif isinstance(raw_list, dict):
                    list_json = raw_list

                # Rollbetter JSON typically has: rank, wins, losses, draws, points
                # Use these as Swiss stats (and general stats if no cut)
                # Helper for safe int casting
                def safe_int(val, default=-1):
                    if val is None:
                        return default
                    try:
                        return int(val)
                    except:
                        return default

                # Rollbetter JSON typically has: rank, wins, losses, draws, points
                # Use these as Swiss stats (and general stats if no cut)
                # Rollbetter JSON typically has: rank, wins, losses, draws, points
                # Use these as Swiss stats (and general stats if no cut)
                player_rank = safe_int(player.get("rank"), 0)
                cut_rank = None
                swiss_rank = player_rank

                if isinstance(player.get("rank"), dict):
                    # Handle nested rank object: {"swiss": 1, "elimination": 2}
                    pr_dict = player.get("rank")
                    swiss_rank = safe_int(pr_dict.get("swiss"), 0)
                    cut_rank = safe_int(pr_dict.get("elimination"), None)

                swiss_wins = safe_int(player.get("wins"), -1)
                swiss_losses = safe_int(player.get("losses"), -1)
                swiss_draws = safe_int(player.get("draws"), 0)
                # Points can be "points", "tournament_points", or "score"
                # (the Rollbetter LF export uses "score" for event points).
                swiss_points = safe_int(player.get("points"), safe_int(
                    player.get("tournament_points"), safe_int(
                        player.get("score"), -1)))

                # Tie Breaker: Use MOV or SOS or MP
                swiss_tb = safe_int(player.get("mov"), safe_int(
                    player.get("sos"), safe_int(player.get("mission_points"), -1)))

                pr = PlayerStanding(
                    tournament_id=int(tid),
                    player_name=player.get("name", "Unknown"),
                    swiss_rank=swiss_rank,
                    swiss_event_points=swiss_points,
                    swiss_wins=swiss_wins,
                    swiss_losses=swiss_losses,
                    swiss_draws=swiss_draws,
                    swiss_tie_breaker_points=swiss_tb,
                    cut_rank=cut_rank,
                    list_json=list_json
                )

                results.append(pr)
        except Exception as e:
            logger.error(f"Error checking LF data for {tid}: {e}")
            import traceback
            traceback.print_exc()
            # We still want to allow scraping other data, but players might be empty if we rely on JSON

        # Format Inference
        f = Format.UNKNOWN
        for p in results[:10]:
            if p.list_json and p.list_json.get("pilots"):
                inferred = infer_format_from_xws(p.list_json)
                if inferred != Format.UNKNOWN:
                    f = inferred
                    break
        t.format = f

        # Apply Legacy Logic: Nullify EP if Legacy
        # Note: We might detect Legacy later from body text in _ensure_data,
        # so this loop might need to run again or be handled in _ensure_data?
        # Let's handle it here IF inferred, and also in _ensure_data.
        if f == Format.LEGACY_X2PO:
            for p in results:
                p.swiss_event_points = None

        # Matches: the LF JSON export carries the full round data, which is
        # far more reliable than scraping the UI tables afterwards.
        matches: list[dict] = []
        for r in data.get("rounds", []) or []:
            rtype_raw = str(r.get("round-type", "")).lower()
            r_type = (
                RoundType.CUT
                if rtype_raw in ("elimination", "cut", "top")
                else RoundType.SWISS
            )
            try:
                round_number = int(r.get("round-number", 0))
            except (TypeError, ValueError):
                round_number = 0

            scen_raw = (r.get("scenario") or "").strip()
            scenario = self._parse_scenario(scen_raw) if scen_raw else None

            for m in r.get("matches", []) or []:
                p1 = (m.get("player1") or "").strip()
                p2 = (m.get("player2") or "").strip()
                s1 = self._parse_int(m.get("player1points"))
                s2 = self._parse_int(m.get("player2points"))

                winner = None
                winner_id = m.get("winner-id")
                if winner_id:
                    if winner_id == m.get("player1-id"):
                        winner = p1
                    elif winner_id == m.get("player2-id"):
                        winner = p2
                    else:
                        winner = winner_id if winner_id in (p1, p2) else None

                is_bye = (not p2) or "bye" in p2.lower()
                if is_bye:
                    winner = p1 or None

                matches.append({
                    "round_number": round_number,
                    "round_type": r_type,
                    "scenario": scenario,
                    "player1_score": s1,
                    "player2_score": s2,
                    "is_bye": is_bye,
                    "p1_name_temp": p1 or "Unknown",
                    "p2_name_temp": p2 or None,
                    "winner_name_temp": winner,
                })

        return {'tournament': t, 'players': results, 'matches': matches}

    def _scrape_standings_ui(self, page) -> dict[str, dict]:
        """
        Scrape W/L/D and Points from the Ladder (standings) UI tab.
        Returns a map: normalized_name -> {wins, losses, draws, points, rank}
        """
        stats_map = {}
        try:
            players = self._scrape_players_ui(page)
            for p in players:
                stats_map[p.player_name.lower().strip()] = {
                    "wins": p.swiss_wins,
                    "losses": p.swiss_losses,
                    "draws": p.swiss_draws,
                    "points": p.swiss_event_points if p.swiss_event_points is not None else 0,
                    "rank": p.swiss_rank,
                }
        except Exception as e:
            logger.warning(f"UI Standings scrape failed: {e}")

        return stats_map

    def _scrape_detailed_matches(self, page, tid: str) -> list[dict]:
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
            page.wait_for_timeout(2000)  # Slightly longer wait

            # 2. Find all round sub-tabs
            import re
            round_btns = page.get_by_role(
                "tab", name=re.compile(r"Round \d+", re.IGNORECASE)).all()

            if not round_btns:
                logger.info(
                    "Found no 'Round' role tabs, trying generic buttons...")
                all_btns = page.locator("button").all()
                round_btns = [b for b in all_btns if "Round" in (
                    b.inner_text() or "")]

            if not round_btns:
                logger.warning("No round buttons found.")
                return []

            logger.info(f"Found {len(round_btns)} rounds to scrape.")

            # Check for Legacy format indicators
            is_legacy = False
            try:
                body_text = page.inner_text("body").lower()
                if "legacy" in body_text or "2.0" in body_text:
                    is_legacy = True
            except:
                pass

            for r_idx, btn in enumerate(round_btns):
                try:
                    btn_text = btn.inner_text()
                    logger.info(f"Scraping {btn_text}...")

                    round_type = RoundType.SWISS
                    if "Top" in btn_text or "Elimination" in btn_text or "Cut" in btn_text:
                        round_type = RoundType.CUT

                    btn.click()

                    # Wait for the active round panel to load a match table.
                    try:
                        page.wait_for_selector(
                            ".tab-pane.active table:has(th:has-text('Result')), "
                            ".tab-pane.active table:has(th:has-text('Players')), "
                            ".tab-pane.active table:has(td:has-text('Win'))",
                            timeout=10000,
                        )
                    except Exception:
                        page.wait_for_timeout(2000)

                    # Extract Scenario
                    scenario_text = ""
                    scenario_el = page.locator(
                        "div:has-text('Scenario:'), p:has-text('Scenario:'), b:has-text('Scenario:')").last
                    if scenario_el.count() > 0:
                        text = scenario_el.inner_text().strip()
                        if "Scenario:" in text:
                            scenario_text = text.split("Scenario:")[1].strip()

                    # Map Scenario Enum
                    # DEFAULT: Other/Unknown if extraction fails (User requirement)
                    # UNLESS Legacy -> No Scenario
                    scenario_val = Scenario.OTHER_UNKNOWN
                    if is_legacy:
                        scenario_val = Scenario.NO_SCENARIO

                    if scenario_text:
                        s_norm = scenario_text.lower().replace(" ", "_")

                        # Fix for Assault at/the Satellite Array
                        if "assault_the_satellite" in s_norm:
                            s_norm = "assault_at_the_satellite_array"

                        found = False
                        for s in Scenario:
                            if s.value == s_norm:
                                scenario_val = s
                                found = True
                                break
                        if not found:
                            logger.warning(
                                f"Unknown scenario text: {scenario_text}")
                            # If we found text but couldn't map it, keep OTHER_UNKNOWN?
                            # Or use logic? Let's check strict mapping.
                            pass

                    # Extract Matches
                    # Find the table that contains 'Player' or 'Result'
                    active_panel = page.locator(".tab-pane.active")
                    table = active_panel.locator(
                        "table:has(th:has-text('Result')), "
                        "table:has(th:has-text('Players')), "
                        "table:has(td:has-text('Win'))",
                    ).first
                    if table.count() == 0:
                        logger.warning(
                            f"No match table found for round {r_idx+1}")
                        continue

                    # New Logic: Iterate rows and look for pairs based on rowspan
                    # Rollbetter Structure:
                    # Row 1 (Top): [Table# rowspan=2] [P1 Name] [Result] [EP] [Score/MP]
                    # Row 2 (Bot): [P2 Name] [Result] [EP] [Score/MP]

                    # Convert to ElementHandle for query_selector_all support
                    table_el = table.element_handle()
                    if not table_el:
                        logger.warning(
                            f"Could not get element handle for table round {r_idx+1}")
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
                                p1_res = cells1[2].inner_text(
                                ).strip().lower()  # "win" or "loss"
                                p1_score = self._parse_int(
                                    cells1[4].inner_text())
                            else:
                                p1_name = "Unknown"
                                p1_score = 0
                                p1_res = ""

                            # Extract P2 (Row 2) which has NO Table# cell
                            # Indices shifted: cell 0 is Name, 1 is Result, 2 is EP, 3 is Score
                            if len(cells2) >= 4:
                                p2_name = cells2[0].inner_text().strip()
                                p2_res = cells2[1].inner_text().strip().lower()
                                p2_score = self._parse_int(
                                    cells2[3].inner_text())
                            else:
                                p2_name = "Unknown"
                                p2_score = 0
                                p2_res = ""

                            # Refine Winner
                            winner_name = None
                            if "win" in p1_res:
                                winner_name = p1_name
                            elif "win" in p2_res:
                                winner_name = p2_name

                            # Detect Bye
                            is_bye = False
                            if "bye" in str(p2_name).lower() or not p2_name or p2_name == "Unknown":
                                is_bye = True
                                p2_name = None

                            m_dict = {
                                "round_number": r_idx + 1,
                                "round_type": round_type,
                                "scenario": Scenario.NO_SCENARIO if is_bye else scenario_val,
                                "player1_score": p1_score,
                                "player2_score": p2_score,
                                "is_bye": is_bye,
                                "p1_name_temp": p1_name,
                                "p2_name_temp": p2_name,
                                "winner_name_temp": winner_name
                            }
                            matches.append(m_dict)

                            i += 2  # Skip the second row of the pair

                        else:
                            # Single or Bye row
                            if len(cells1) >= 2:
                                p1_name = cells1[1].inner_text().strip()
                                m_dict = {
                                    "round_number": r_idx + 1,
                                    "round_type": round_type,
                                    "scenario": None,
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
                    logger.warning(
                        f"Error scraping round {r_idx+1}: {round_err}")

        except Exception as e:
            logger.warning(f"Detailed match scrape failed: {e}")

        return matches
