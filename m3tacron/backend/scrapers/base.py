"""
Base Scraper Module.

This module defines the abstract interface that all tournament scrapers must implement.
It ensures consistency across different platforms (Rollbetter, Longshanks) by enforcing
a standard return type for tournament data, participants, and matches.

Also provides shared utility methods (_parse_date, _parse_int, _parse_scenario,
_compute_stats_from_matches) to avoid duplication across scraper implementations.
"""
import logging
import re
from abc import ABC, abstractmethod
from datetime import datetime, date

# Database Models
from ..models import Tournament, PlayerResult, Match
from ..data_structures.formats import Format, infer_format_from_xws
from ..data_structures.round_types import RoundType
from ..data_structures.scenarios import Scenario

logger = logging.getLogger(__name__)


class BaseScraper(ABC):
    """
    Abstract base class for tournament scrapers.

    Any platform-specific scraper should inherit from this class and implement
    the abstract methods to transform platform-specific data into our standard Models.
    """

    # --- Shared Utility Methods ---

    def _parse_date(self, text: str) -> datetime:
        """Parse a date string with multiple format strategies.

        Handles ordinal suffixes (1st, 2nd), date ranges (split on –),
        and tries multiple strptime formats.

        Args:
            text: Raw date string from HTML.

        Returns:
            Parsed datetime, or datetime.now() if all formats fail.
        """
        if not text:
            return datetime.now()

        # Remove ordinal suffixes (1st, 2nd, 3rd, 4th)
        clean = re.sub(r"(\d+)(st|nd|rd|th)", r"\1", text.strip())

        # Handle date ranges ("2026-01-10 – 2026-01-11")
        # We prefer the END date for recently-concluded usage
        if "–" in clean:
            clean = clean.split("–")[-1].strip()
        if " - " in clean:
            clean = clean.split(" - ")[-1].strip()

        formats = [
            "%d %b %Y",     # 14 Jan 2024
            "%d %B %Y",     # 14 January 2024
            "%Y-%m-%d",     # 2024-01-14
            "%d/%m/%Y",     # 14/01/2024
            "%B %d, %Y",    # January 14, 2024
            "%b %d, %Y",    # Jan 14, 2024
        ]

        for fmt in formats:
            try:
                return datetime.strptime(clean, fmt)
            except ValueError:
                continue

        # Fallback: regex for "Jan 25, 2026" or "August 5, 2023"
        match = re.search(r"([A-Za-z]+)\s+(\d{1,2}),\s+(\d{4})", text)
        if match:
            try:
                d_str = f"{match.group(1)[:3]} {match.group(2)}, {match.group(3)}"
                return datetime.strptime(d_str, "%b %d, %Y")
            except ValueError:
                pass

        logger.warning(f"Could not parse date: '{text}'")
        return datetime.now()

    def _parse_int(self, val) -> int:
        """Safely parse an integer from a string.

        Args:
            val: Value to parse (str, int, or None).

        Returns:
            Parsed integer, or 0 on failure.
        """
        try:
            return int(str(val).strip())
        except (ValueError, AttributeError):
            return 0

    def _parse_scenario(self, text: str) -> str:
        """Match text to a Scenario enum value.

        Normalizes text and searches for a matching scenario.

        Args:
            text: Scenario text from HTML.

        Returns:
            Scenario enum value string, or Scenario.OTHER_UNKNOWN.
        """
        if not text:
            return Scenario.OTHER_UNKNOWN
        text_norm = text.lower().replace(" ", "_").strip()

        # Known mapping fix
        if "assault_the_satellite" in text_norm:
            text_norm = "assault_at_the_satellite_array"

        for s in Scenario:
            if s.value == "unknown":
                continue
            if s.value.replace("_", " ") in text.lower():
                return s.value
            if s.value in text_norm:
                return s.value
        return Scenario.OTHER_UNKNOWN

    def _compute_stats_from_matches(
        self,
        players: list[PlayerResult],
        matches: list[dict],
        fmt: Format
    ) -> None:
        """Compute W/L/D, Event Points, and Tie Breakers from match data.

        Only runs if players have placeholder stats (swiss_wins == -1).
        Modifies players in place.

        Args:
            players: List of PlayerResult to update.
            matches: List of match dicts with p1/p2 names, scores, winner.
            fmt: Tournament format (affects point calculation).
        """
        # Check if computation is needed
        needs_compute = any(
            p.swiss_wins == -1 or p.swiss_tie_breaker_points == -1
            for p in players
        )
        if not needs_compute:
            return

        logger.info("Computing W/L/D and Tie Breakers from matches...")
        p_map = {p.player_name.lower().strip(): p for p in players}

        # Reset placeholders to 0
        for p in players:
            if p.swiss_wins == -1:
                p.swiss_wins = 0
            if p.swiss_losses == -1:
                p.swiss_losses = 0
            if p.swiss_draws == -1:
                p.swiss_draws = 0
            p.swiss_tie_breaker_points = 0

        for m in matches:
            if m["round_type"] != RoundType.SWISS:
                continue

            p1_name = m.get("p1_name_temp")
            p2_name = m.get("p2_name_temp")
            winner = m.get("winner_name_temp")

            p1 = p_map.get(p1_name.lower().strip()) if p1_name else None
            p2 = p_map.get(p2_name.lower().strip()) if p2_name else None

            s1 = m.get("player1_score", 0)
            s2 = m.get("player2_score", 0)

            # Determine result
            p1_win = p2_win = draw = False
            if winner:
                w_norm = winner.lower().strip()
                if p1_name and w_norm == p1_name.lower().strip():
                    p1_win = True
                elif p2_name and w_norm == p2_name.lower().strip():
                    p2_win = True
            else:
                if s1 > s2:
                    p1_win = True
                elif s2 > s1:
                    p2_win = True
                elif s1 == s2 and s1 > 0:
                    draw = True

            # Update stats
            if p1:
                p1.swiss_tie_breaker_points += s1
                if p1_win:
                    p1.swiss_wins += 1
                elif p2_win:
                    p1.swiss_losses += 1
                elif draw:
                    p1.swiss_draws += 1

            if p2:
                p2.swiss_tie_breaker_points += s2
                if p2_win:
                    p2.swiss_wins += 1
                elif p1_win:
                    p2.swiss_losses += 1
                elif draw:
                    p2.swiss_draws += 1

        # Points calculation
        pt_win = 3 if fmt != Format.LEGACY_X2PO else 1
        pt_draw = 1 if fmt != Format.LEGACY_X2PO else 0

        for p in players:
            if p.swiss_event_points is None or p.swiss_event_points <= 0:
                p.swiss_event_points = (p.swiss_wins * pt_win) + (p.swiss_draws * pt_draw)

    # --- Abstract Methods ---

    @abstractmethod
    def list_tournaments(
        self,
        date_from: date,
        date_to: date,
        max_pages: int | None = None
    ) -> list[dict]:
        """Discover tournament URLs from the platform's listing pages.

        Args:
            date_from: Start of date range (inclusive).
            date_to: End of date range (inclusive).
            max_pages: Max listing pages to scrape. None = no limit.

        Returns:
            List of dicts with keys: url, name, date, player_count.
        """
        pass

    @abstractmethod
    def get_tournament_data(
        self,
        tournament_id: str,
        inferred_format: Format | None = None
    ) -> Tournament:
        """Fetch and parse the high-level tournament metadata.

        Args:
            tournament_id: Platform-specific tournament identifier.
            inferred_format: Format inferred from XWS data (takes priority
                             over URL/platform-based detection). Implementations
                             may ignore this if format is determined elsewhere.

        Returns:
            Tournament model instance.
        """
        pass

    @abstractmethod
    def get_participants(self, tournament_id: str) -> list[PlayerResult]:
        """Fetch all registered players and their squad lists.

        Returns:
            List of PlayerResult model instances.
        """
        pass

    @abstractmethod
    def get_matches(self, tournament_id: str) -> list[Match]:
        """Fetch all match results from all rounds.

        Returns:
            List of Match model instances.
        """
        pass

    # --- Orchestration ---

    def run_full_scrape(
        self,
        tournament_id: str
    ) -> tuple[Tournament, list[PlayerResult], list[Match]]:
        """Execute a complete scrape with XWS-priority format inference.

        Flow:
        1. Get participants first (provides XWS data)
        2. Infer format from XWS (priority over URL detection)
        3. Get tournament metadata (passing inferred format)
        4. Update player count if missing
        5. Get matches

        Returns:
            Tuple of (Tournament, list[PlayerResult], list[Match]).
        """
        # 1. Get participants first for XWS data
        players = self.get_participants(tournament_id)

        # 2. Infer format from XWS data
        inferred_format = None
        for pl in players[:20]:
            if pl.list_json and pl.list_json.get("pilots"):
                inferred = infer_format_from_xws(pl.list_json)
                if inferred != Format.OTHER:
                    inferred_format = inferred
                    logger.info(
                        f"XWS-inferred format {inferred.value} "
                        f"from player {pl.player_name}"
                    )
                    break

        # 3. Get tournament metadata with inferred format
        tournament = self.get_tournament_data(
            tournament_id, inferred_format=inferred_format
        )

        # 4. Update player count from actual results
        if players and tournament.player_count == 0:
            tournament.player_count = len(players)

        # 5. Get matches
        matches = self.get_matches(tournament_id)

        return tournament, players, matches
