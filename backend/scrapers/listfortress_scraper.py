from datetime import datetime, timedelta
import logging
import httpx

from .base import BaseScraper
from ..models import Tournament, Match, PlayerStanding
from ..data_structures.formats import Format
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
            sorted_data = sorted(data, key=lambda x: x.get("id", 0), reverse=True)

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
            if not fmt:
                # User Requirement: Ignore ListFortress definition
                # fmt = self._map_format(data.get("format_id")) 
                fmt = Format.OTHER

            return Tournament(
                id=str(data["id"]),
                name=str(data["name"]).strip(),
                date=self._parse_date(data.get("date")).date(),
                format=fmt,
                source=Source.LISTFORTRESS,
                location=self._format_location(data),
                player_count=len(data.get("participants", [])),
                matches_count=0 # Updated later
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
                        logger.warning(f"Invalid JSON for player {p.get('id')}")

                pr = PlayerStanding(
                    player_name=p.get("name", "Unknown"),
                    list_json=xws or {},
                    swiss_rank=p.get("swiss_rank", 0),
                    cut_rank=p.get("top_cut_rank"),
                    swiss_event_points=p.get("score"),
                    swiss_tie_breaker_points=p.get("mov")
                )
                results.append(pr)
                
        except Exception as e:
            logger.error(f"Error fetching participants for {tournament_id}: {e}")
            
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
                return [] # Many LF events have no rounds

            # Need to map player IDs to Names for the Match object
            # (Match object uses names currently, though IDs would be better long term)
            p_map = {p["id"]: p["name"] for p in data.get("participants", [])}

            for r in rounds:
                r_type = RoundType.SWISS if r["roundtype_id"] == 1 else RoundType.CUT 
                # Note: roundtype_id mapping is a guess/standard. 1=Swiss usually.
                # Just assuming 'swiss' for now unless we see distinct ID.
                # Actually, ListFortress might use "round_type" field? 
                # rounds json: [{"roundtype_id": 1, "matches": [...]}]
                
                for m in r.get("matches", []):
                    p1_id = m.get("player1_id")
                    p2_id = m.get("player2_id")
                    winner_id = m.get("winner_id")
                    
                    p1_name = p_map.get(p1_id, "Unknown")
                    p2_name = p_map.get(p2_id, "Bye" if not p2_id else "Unknown")

                    # Result logic
                    winner_name = None
                    if winner_id == p1_id:
                        winner_name = p1_name
                    elif winner_id == p2_id:
                        winner_name = p2_name
                    
                    match = {
                        "round_number": r.get("round_number", 0),
                        "round_type": r_type,
                        "p1_name_temp": p1_name,
                        "p2_name_temp": p2_name,
                        "player1_score": m.get("player1_points", 0),
                        "player2_score": m.get("player2_points", 0),
                        "winner_name_temp": winner_name
                    }
                    matches.append(match)

        except Exception as e:
            logger.error(f"Error fetching matches for {tournament_id}: {e}")

        return matches
        
    def _map_format(self, fmt_id: int) -> Format:
        # Standard=1, Extended=2? Guessing based on common knowledge of X-Wing legacy.
        # Ideally, we should fetch /api/v1/formats but it's static enough for now.
        if fmt_id == 1:
            return Format.AMG
        elif fmt_id == 2:
            return Format.OTHER # Extended
        elif fmt_id == 34: # From API ID 360 result (2nd Ed?)
             return Format.AMG # Assume 2.0/2.5 are grouped or handle specifically
        return Format.AMG # Default fallback

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
