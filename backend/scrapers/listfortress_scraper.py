from datetime import datetime, timedelta
import logging
import httpx

from .base import BaseScraper
from ..models import Tournament, Match, PlayerStanding
from ..data_structures.formats import Format, infer_format_from_xws
from ..data_structures.source import Source
from ..data_structures.round_types import RoundType
from ..data_structures.location import Location

logger = logging.getLogger(__name__)


class ListFortressScraper(BaseScraper):
    """Scraper logic for ListFortress API."""

    BASE_URL = "https://listfortress.com/api/v1"

    def __init__(self):
        # ListFortress API doesn't require complex session handling, but we init session anyway
        super().__init__()
        self.session = httpx.Client(timeout=30.0)

    def list_tournaments(
        self,
        date_from: datetime.date,
        date_to: datetime.date,
        max_pages: int | None = None
    ) -> list[dict]:
        """Discover tournament URLs from the ListFortress API.

        Fetches the full tournament list (single API call), then filters
        client-side by date range. The ListFortress API returns all
        tournaments in one response — no pagination needed.

        Args:
            date_from: Start of date range (inclusive).
            date_to: End of date range (inclusive).
            max_pages: Unused (ListFortress returns all in one call).

        Returns:
            List of dicts: {url, name, date, player_count}.
        """
        try:
            resp = self.session.get(f"{self.BASE_URL}/tournaments")
            resp.raise_for_status()
            data = resp.json()

            # Sort by ID descending (newest first, roughly chronological)
            sorted_data = sorted(
                data, key=lambda x: x.get("id", 0), reverse=True)

            results = []
            for item in sorted_data:
                t_date = self._parse_date(item.get("date"))
                if t_date.date() < date_from or t_date.date() > date_to:
                    continue

                results.append({
                    "url": f"https://listfortress.com/tournaments/{item['id']}",
                    "name": str(item["name"]).strip(),
                    "date": t_date.date().isoformat(),
                    "player_count": item.get("participants_count", 0),
                })

            logger.info(
                f"Discovered {len(results)} tournaments from ListFortress "
                f"(out of {len(sorted_data)} total)."
            )
            return results

        except Exception as e:
            logger.error(f"Failed to fetch ListFortress tournaments: {e}")
            return []

    def get_tournament_data(
        self,
        tournament_id: str,
        inferred_format: Format | None = None
    ) -> Tournament:
        """Fetch detailed metadata for a single tournament."""
        url = f"{self.BASE_URL}/tournaments/{tournament_id}"
        try:
            resp = self.session.get(url)
            resp.raise_for_status()
            data = resp.json()

            # Format might be overridden by inferred_format if provided
            fmt = inferred_format
            if not fmt or fmt == Format.UNKNOWN:
                # Fallback to ListFortress format_id when XWS inference yields UNKNOWN
                # (e.g. pre-2019 events like 2797/105 with empty vendor). For the
                # FFG era (pre-2021 second edition), format_id 1/2/34 were all FFG
                # — mapping them to AMG would pick the wrong pt_win and keep the
                # format as "unknown" even though 12808 already heals via raithos.
                # So era-gate the _map_format fallback.
                fid = data.get("format_id")
                try:
                    event_date = self._parse_date(data.get("date") or "").date()
                except Exception:
                    event_date = None
                if event_date is not None and event_date < __import__("datetime").date(2021, 1, 1):
                    # Pre-AMG era: everything was FFG 2.0.
                    fmt = Format.FFG
                elif fid is not None:
                    mapped = self._map_format(fid)
                    if mapped != Format.UNKNOWN:
                        fmt = mapped

            return Tournament(
                id=str(data["id"]),
                name=str(data["name"]).strip(),
                date=self._parse_date(data.get("date")).date(),
                format=fmt,
                source=Source.LISTFORTRESS,
                location=self._format_location(data),
                player_count=len(data.get("participants", [])),
                matches_count=0  # Updated later
            )
        except Exception as e:
            logger.error(f"Failed to get tournament {tournament_id}: {e}")
            return Tournament(
                id=tournament_id,
                name="Unknown",
                date=datetime.now(),
                format=Format.UNKNOWN,
                source=Source.LISTFORTRESS,
                location=Location.create(
                    city="Unknown",
                    country="Unknown",
                    continent="Unknown",
                ),
            )

    def get_participants(self, tournament_id: str) -> list[PlayerStanding]:
        """Fetch players and lists."""
        url = f"{self.BASE_URL}/tournaments/{tournament_id}"
        results = []
        try:
            resp = self.session.get(url)
            resp.raise_for_status()
            data = resp.json()

            parts = data.get("participants", [])
            for p in parts:
                # ListFortress provides 'list_json' string which is XWS
                xws = None
                if p.get("list_json"):
                    import json
                    try:
                        xws = json.loads(p["list_json"])
                    except json.JSONDecodeError:
                        logger.warning(
                            f"Invalid JSON for player {p.get('id')}")

                pr = PlayerStanding(
                    player_name=p.get("name") or "Unknown",
                    list_json=xws or {},
                    swiss_rank=p.get("swiss_rank", 0),
                    cut_rank=p.get("top_cut_rank"),
                    swiss_event_points=p.get("score"),
                    swiss_tie_breaker_points=p.get("mov")
                )
                results.append(pr)

        except Exception as e:
            logger.error(
                f"Error fetching participants for {tournament_id}: {e}")

        return results

    def get_matches(self, tournament_id: str) -> list[Match]:
        """Fetch matches if available."""
        url = f"{self.BASE_URL}/tournaments/{tournament_id}"
        matches = []
        try:
            resp = self.session.get(url)
            resp.raise_for_status()
            data = resp.json()

            rounds = data.get("rounds", [])
            if not rounds:
                return []  # Many LF events have no rounds

            # Need to map player IDs to Names for the Match object
            # (Match object uses names currently, though IDs would be better long term)
            p_map = {p["id"]: p["name"] for p in data.get("participants", [])}

            for r in rounds:
                r_type = RoundType.SWISS if r.get(
                    "roundtype_id", 1) == 1 else RoundType.CUT
                # Note: roundtype_id 1 = Swiss, anything else (e.g. 2) = cut.
                scenario = self._parse_scenario(
                    r.get("scenario") or "") if r.get("scenario") else None
                r_number = r.get("round_number", 0)

                for m in r.get("matches", []):
                    p1_id = m.get("player1_id")
                    p2_id = m.get("player2_id")
                    winner_id = m.get("winner_id")

                    p1_name = p_map.get(p1_id, "Unknown")
                    p2_name = p_map.get(
                        p2_id, "Bye" if not p2_id else "Unknown")

                    # Result logic
                    winner_name = None
                    if winner_id == p1_id:
                        winner_name = p1_name
                    elif winner_id == p2_id:
                        winner_name = p2_name

                    is_bye = (not p2_id) or "bye" in p2_name.lower()
                    if is_bye:
                        winner_name = p1_name

                    p1_pts = m.get("player1_points")
                    p2_pts = m.get("player2_points")
                    match = {
                        "round_number": r_number,
                        "round_type": r_type,
                        "scenario": scenario,
                        "p1_name_temp": p1_name,
                        "p2_name_temp": p2_name,
                        "player1_score": p1_pts if isinstance(p1_pts, int) else 0,
                        "player2_score": p2_pts if isinstance(p2_pts, int) else 0,
                        "winner_name_temp": winner_name,
                        "is_bye": is_bye,
                    }
                    matches.append(match)

        except Exception as e:
            logger.error(f"Error fetching matches for {tournament_id}: {e}")

        return matches

    @staticmethod
    def _estimate_swiss_rounds(num_players: int) -> int:
        """Estimate Swiss rounds from attendance (FFG/AMG table).

        FFG/AMG regulations: 4-8→3, 9-16→4, 17-32→4, 33-64→5, 65-128→6, 129+→7.
        This matches observed ListFortress events (e.g. 99 players → 6 rounds).
        """
        if num_players <= 8:
            return 3
        if num_players <= 32:
            return 4
        if num_players <= 64:
            return 5
        if num_players <= 128:
            return 6
        return 7

    def run_full_scrape(
        self, tournament_id: str
    ) -> tuple[Tournament, list[PlayerStanding], list[Match]]:
        """Full scrape, then derive W/L/D from match results.

        The ListFortress API does not expose per-player win/loss/draw counts,
        so they are computed from the round match data (winner_id per match).
        When no rounds are present (common for pre-2019 ListFortress events)
        W/L are inferred from tournament points — as the user noted, given
        that ties do not exist for 12808/Nordics 2018, wins = TP / pt_win
        and losses = inferred_rounds − wins.
        """
        tournament, players, matches = super().run_full_scrape(tournament_id)

        if players and matches:
            from ..data_structures.round_types import RoundType
            p_map = {
                p.player_name.lower().strip(): p for p in players
            }

            def _get(name) -> PlayerStanding | None:
                return p_map.get((name or "").lower().strip())

            for m in matches:
                if not isinstance(m, dict) or m.get("round_type") != RoundType.SWISS:
                    continue
                p1 = _get(m.get("p1_name_temp"))
                p2 = _get(m.get("p2_name_temp"))
                if not p1 and not p2:
                    continue

                w = m.get("winner_name_temp")
                w_norm = (w or "").lower().strip()
                s1 = m.get("player1_score", -1)
                s2 = m.get("player2_score", -1)

                p1_win = bool(w and p1 and w_norm == p1.player_name.lower().strip())
                p2_win = bool(w and p2 and w_norm == p2.player_name.lower().strip())
                draw = (not w) and s1 >= 0 and s2 >= 0 and s1 == s2 and s1 > 0

                if p1:
                    if p1_win:
                        p1.swiss_wins = (p1.swiss_wins or 0) + 1
                    elif p2_win:
                        p1.swiss_losses = (p1.swiss_losses or 0) + 1
                    elif draw:
                        p1.swiss_draws = (p1.swiss_draws or 0) + 1
                if p2:
                    if p2_win:
                        p2.swiss_wins = (p2.swiss_wins or 0) + 1
                    elif p1_win:
                        p2.swiss_losses = (p2.swiss_losses or 0) + 1
                    elif draw:
                        p2.swiss_draws = (p2.swiss_draws or 0) + 1

        # Fallback when no round data is available (e.g. 12808/Nordics 2018).
        # The API still provides `score` (event_points) and `mov`, so we can
        # reconstruct W/L even though there are no rounds to iterate — given
        # that a tie does not exist, losses = inferred_rounds − wins.
        if players and not matches:
            has_points = any(
                p.swiss_event_points not in (None, 0) for p in players
            )
            all_zero = all(
                (p.swiss_wins or 0) == 0 and (p.swiss_losses or 0) == 0
                for p in players
            )
            if has_points and all_zero:
                fmt = tournament.format
                # Try to resolve UNKNOWN via XWS inference on the squad lists.
                if fmt == Format.UNKNOWN or fmt is None:
                    for pl in players[:20]:
                        if pl.list_json:
                            inferred = infer_format_from_xws(pl.list_json)
                            if inferred != Format.UNKNOWN:
                                fmt = inferred
                                break
                # Points per win depends on ruleset.
                pt_win = 1 if fmt in (
                    Format.FFG,
                    Format.LEGACY_X2PO,
                    Format.LEGACY_PANDORUM,
                ) else 3
                if fmt == Format.UNKNOWN or fmt is None:
                    max_pts = max((p.swiss_event_points or 0) for p in players)
                    # Heuristic: small maxima (≤8) with 1-pt scores imply 1 pt/win.
                    pt_win = 1 if max_pts <= 8 else 3
                # Infer total Swiss rounds from both points and attendance so we
                # don't underestimate when the winner is not undefeated.
                max_pts = max((p.swiss_event_points or 0) for p in players)
                if pt_win == 1:
                    rounds_from_points = max_pts  # wins = pts
                else:
                    # 3 pt/win (+1 per draw). For 12808-style no-draw events
                    # wins = pts // 3, draws = pts % 3.
                    # Inferred rounds is max wins+draws (undefeated assumption).
                    rounds_from_points = max(
                        ((p.swiss_event_points or 0) // 3) + ((p.swiss_event_points or 0) % 3)
                        for p in players
                    )
                rounds_from_attendance = self._estimate_swiss_rounds(len(players))
                inferred_rounds = max(rounds_from_points, rounds_from_attendance)
                # Extra guard: rounds should be at least max_pts//pt_win (handles draws).
                inferred_rounds = max(inferred_rounds, max_pts // pt_win if pt_win else max_pts)
                for p in players:
                    pts = p.swiss_event_points or 0
                    if pt_win == 1:
                        wins = pts
                        draws = 0
                    else:
                        wins = pts // 3
                        draws = pts % 3  # 4 = 1W+1D, 7 = 2W+1D, etc.
                    p.swiss_wins = wins
                    p.swiss_draws = draws
                    p.swiss_losses = max(0, inferred_rounds - wins - draws)
                logger.info(
                    f"Inferred W/L from points for {tournament.name} "
                    f"(no rounds): pt_win={pt_win}, rounds={inferred_rounds}, "
                    f"max_pts={max_pts}, fmt={fmt}"
                )

        return tournament, players, matches

    def _map_format(self, fmt_id: int) -> Format:
        # Standard=1, Extended=2? Guessing based on common knowledge of X-Wing legacy.
        # Ideally, we should fetch /api/v1/formats but it's static enough for now.
        if fmt_id == 1:
            return Format.AMG
        elif fmt_id == 2:
            return Format.UNKNOWN  # Extended
        elif fmt_id == 34:  # From API ID 360 result (2nd Ed?)
            return Format.AMG  # Assume 2.0/2.5 are grouped or handle specifically
        return Format.AMG  # Default fallback

    def _format_location(self, data: dict) -> Location:
        from ..utils.geocoding import resolve_location

        locs = [data.get("location"), data.get("state"), data.get("country")]
        raw_location = ", ".join([x for x in locs if x])
        if raw_location:
            resolved = resolve_location(raw_location)
            if resolved:
                return resolved

        return Location.create(
            city="Unknown",
            country="Unknown",
            continent="Unknown",
        )
