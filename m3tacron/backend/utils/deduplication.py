from datetime import timedelta
from difflib import SequenceMatcher
from typing import List, Optional
import logging

from m3tacron.backend.models import Tournament, PlayerResult

logger = logging.getLogger(__name__)

class DedupService:
    """Service to identify duplicate tournaments across different sources."""

    def find_duplicate(
        self, 
        target: Tournament, 
        candidates: List[Tournament],
        target_players: Optional[List[PlayerResult]] = None,
        candidate_players_map: Optional[dict[str, List[PlayerResult]]] = None
    ) -> Optional[Tournament]:
        """Find a duplicate of the target tournament in the list of candidates.

        Args:
            target: The tournament we are trying to save/check.
            candidates: Existing tournaments to check against.
            target_players: Optional list of players for the target tournament (for overlap check).
            candidate_players_map: Optional map of tournament_id -> list of players for candidates.

        Returns:
            The matching Tournament object if a duplicate is found, else None.
        """
        possible_matches = []

        for candidate in candidates:
            # 1. Filter by Date (+/- 1 day)
            # Some sources might be in different timezones or report "end date" vs "start date"
            # If dates are missing, we skip this check (but likely can't confirm dedup easily)
            if not target.date or not candidate.date:
                continue
                
            delta = abs(target.date - candidate.date)
            if delta > timedelta(days=2): # Allow 48h slop for timezone/reporting diffs
                continue

            # 2. Calculate Name Similarity
            name_score = self._similarity(target.name, candidate.name)

            # 3. Calculate Player Overlap (if data available)
            player_score = 0.0
            if target_players and candidate_players_map:
                c_players = candidate_players_map.get(str(candidate.id)) or candidate_players_map.get(candidate.id)
                if c_players:
                    player_score = self._calculate_player_overlap(target_players, c_players)

            # 4. Location Check (Simple country/state match if available)
            # Not strict scoring, but used as a tie-breaker or confidence booster?
            # For now, we rely on Name/Date/Players.

            # Decision Logic
            is_match = False
            
            # High Confidence: Lots of player overlap
            if player_score > 0.5: 
                is_match = True
                logger.debug(f"Dedup Match (Player Overlap): {target.name} ({target.platform}) == {candidate.name} ({candidate.platform}) | Score: {player_score:.2f}")

            # Medium Confidence: High Name Match + Date Match (already filtered) + Same Player Count (approx)
            elif name_score > 0.85:
                # Check player count if available to avoid matching "Main Event" vs "Side Event" with similar names
                # Allow 20% variance in player count (drops/no-shows)
                if abs(target.player_count - candidate.player_count) / max(candidate.player_count, 1) < 0.2:
                    is_match = True
                    logger.debug(f"Dedup Match (Name+Date): {target.name} ({target.platform}) == {candidate.name} ({candidate.platform}) | Score: {name_score:.2f}")

            if is_match:
                return candidate

        return None

    def _similarity(self, a: str, b: str) -> float:
        """Return a similarity score between 0.0 and 1.0."""
        return SequenceMatcher(None, str(a).lower(), str(b).lower()).ratio()

    def _calculate_player_overlap(self, list_a: List[PlayerResult], list_b: List[PlayerResult]) -> float:
        """Calculate Jaccard index of player names."""
        if not list_a or not list_b:
            return 0.0

        names_a = set(p.player_name.lower().strip() for p in list_a)
        names_b = set(p.player_name.lower().strip() for p in list_b)

        intersection = len(names_a.intersection(names_b))
        union = len(names_a.union(names_b))

        if union == 0:
            return 0.0
            
        return intersection / union
