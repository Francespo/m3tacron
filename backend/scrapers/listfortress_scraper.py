from datetime import datetime, timedelta
import logging
import httpx
from typing import List, Tuple, Optional, Any

from m3tacron.backend.scrapers.base import BaseScraper
from m3tacron.backend.models import Tournament, Match, PlayerResult
from m3tacron.backend.data_structures.formats import Format
from m3tacron.backend.data_structures.platforms import Platform
from m3tacron.backend.data_structures.round_types import RoundType

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
    ) -> List[dict]:
        """Discover tournament URLs from ListFortress API.

        Args:
            date_from: Start date.
            date_to: End date.
            max_pages: Ignored for now (fetched in one go or limited).

        Returns:
            List of dicts with keys: url, name, date, player_count.
        """
        """Fetch list of tournaments from API.

        Note: ListFortress API returns ALL tournaments in one go usually, 
        or we might need to filter client-side if the API doesn't support format filtering parameters.
        Docs are sparse, so we'll fetch all and filter.
        
        Args:
            fmt: Format filter (STANDARD/EXTENDED/etc).
            offset: Not fully supported by LF API in standard way, might be ID based. 
                   For now, we'll fetch recent ones.
        """
        # ListFortress doesn't seem to have a robust "since" filter in /tournaments
        # It returns a huge JSON. We might want to limit this in production or cache it.
        # For this prototype, we'll fetch and filter the last ~50-100 relevant ones.
        
        try:
            resp = self.session.get(f"{self.BASE_URL}/tournaments")
            resp.raise_for_status()
            data = resp.json()
            
            # data is a list of dicts
            results = []
            # Sort by ID descending to get newest first (approx) or date
            data.sort(key=lambda x: x.get("id", 0), reverse=True)
            
            count = 0
            for item in data:
                if count >= 20: # Limit for now to avoid hammering/processing 5000+ items
                    break
                    
                t_format = self._map_format(item.get("format_id"))
                if t_format != fmt:
                    continue

                t_date = self._parse_date(item.get("date"))
                if t_date.date() < date_from or t_date.date() > date_to:
                    continue

                # Return dict as per BaseScraper contract
                results.append({
                    "url": f"https://listfortress.com/tournaments/{item['id']}",
                    "name": str(item["name"]).strip(),
                    "date": t_date,
                    "player_count": 0 # Not available in simple list?
                })
                count += 1
                
            return results

        except Exception as e:
            logger.error(f"Failed to fetch ListFortress tournaments: {e}")
            return []

    def get_tournament_data(
        self, 
        tournament_id: str,
        inferred_format: Optional[Format] = None
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
                date=self._parse_date(data.get("date")),
                format=fmt,
                platform=Platform.LISTFORTRESS,
                location=self._format_location(data),
                player_count=len(data.get("participants", [])),
                matches_count=0 # Updated later
            )
        except Exception as e:
            logger.error(f"Failed to get tournament {tournament_id}: {e}")
            return Tournament(id=tournament_id, name="Unknown", date=datetime.now(), format=Format.UNKNOWN, platform=Platform.LISTFORTRESS)

    def get_participants(self, tournament_id: str) -> List[PlayerResult]:
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

                pr = PlayerResult(
                    player_name=p.get("name", "Unknown"),
                    list_json=xws,
                    swiss_rank=p.get("swiss_rank", 0),
                    top_cut_rank=p.get("top_cut_rank"),
                    score=p.get("score"),
                    mov=p.get("mov"),
                    sos=float(p.get("sos", 0.0)) if p.get("sos") else 0.0
                )
                results.append(pr)
                
        except Exception as e:
            logger.error(f"Error fetching participants for {tournament_id}: {e}")
            
        return results

    def get_matches(self, tournament_id: str) -> List[Match]:
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
                r_type = RoundType.SWISS if r["roundtype_id"] == 1 else RoundType.ELIMINATION 
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

    def _format_location(self, data: dict) -> str:
        locs = [data.get("location"), data.get("state"), data.get("country")]
        return ", ".join([x for x in locs if x])
