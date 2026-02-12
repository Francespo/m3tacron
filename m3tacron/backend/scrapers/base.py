"""
Base Scraper Module.

This module defines the abstract interface that all tournament scrapers must implement.
It ensures consistency across different platforms (Rollbetter, Longshanks) by enforcing
a standard return type for tournament data, participants, and matches.
"""
from abc import ABC, abstractmethod

from datetime import datetime, date

# Database Models
from ..models import Tournament, PlayerResult, Match

class BaseScraper(ABC):
    """
    Abstract base class for tournament scrapers.
    
    Any platform-specific scraper should inherit from this class and implement
    the abstract methods to transform platform-specific data into our standard Models.
    """

    @abstractmethod
    def list_tournaments(
        self,
        date_from: date,
        date_to: date,
        max_pages: int | None = None
    ) -> list[dict]:
        """
        Discover tournament URLs from the platform's listing pages.

        Args:
            date_from: Start of date range (inclusive).
            date_to: End of date range (inclusive).
            max_pages: Max listing pages to scrape. None = no limit.

        Returns:
            List of dicts with keys: url, name, date, player_count.
        """
        pass

    @abstractmethod
    def get_tournament_data(self, tournament_id: str) -> Tournament:
        """
        Fetch and parse the high-level tournament metadata.
        
        Should return a Tournament model instance with fields like:
        - name
        - date
        - format / macro_format
        """
        pass

    @abstractmethod
    def get_participants(self, tournament_id: str) -> list[PlayerResult]:
        """
        Fetch all registered players and their squad lists.
        
        Should return a list of PlayerResult model instances.
        Required fields:
        - player_name
        - list_json (XWS dict)
        - rank (swiss rank)
        - points / sos (optional)
        """
        pass

    @abstractmethod
    def get_matches(self, tournament_id: str) -> list[Match]:
        """
        Fetch all match results from all rounds.
        
        Should return a list of Match model instances.
        Required fields:
        - round_number
        - player1_id / player2_id (names or IDs)
        - winner_id
        - score
        """
        pass

    def run_full_scrape(
        self, 
        tournament_id: str
    ) -> tuple[Tournament, list[PlayerResult], list[Match]]:
        """
        Execute a complete scrape of a tournament.
        
        Orchestrates the individual fetch methods to return a complete dataset.
        This generic implementation ensures the order of operations is consistent.
        """
        # 1. Get metadata first to establish the tournament context
        tournament = self.get_tournament_data(tournament_id)
        
        # 2. Get players to establish who is playing
        players = self.get_participants(tournament_id)
        
        # 3. Get matches to establish results
        matches = self.get_matches(tournament_id)
        
        return tournament, players, matches
