import unittest
from datetime import date, timedelta
from m3tacron.backend.domain.deduplication import DedupService
from m3tacron.backend.models import Tournament, PlayerResult
from m3tacron.backend.data_structures.platforms import Platform

class TestDedupService(unittest.TestCase):
    def setUp(self):
        self.service = DedupService()
        self.base_date = date(2024, 1, 15)
        
        self.target = Tournament(
            id=1,
            name="X-Wing World Open 2024",
            date=self.base_date,
            platform=Platform.LISTFORTRESS,
            player_count=20,
            url="http://listfortress.com/1"
        )

        self.players_target = [
            PlayerResult(id=1, tournament_id=1, player_name="Han Solo"),
            PlayerResult(id=2, tournament_id=1, player_name="Luke Skywalker"),
            PlayerResult(id=3, tournament_id=1, player_name="Wedge Antilles"),
        ]

    def test_exact_name_match(self):
        candidate = Tournament(
            id=2,
            name="X-Wing World Open 2024",
            date=self.base_date,
            platform=Platform.ROLLBETTER,
            player_count=20,
            url="http://rollbetter.gg/2"
        )
        match = self.service.find_duplicate(self.target, [candidate])
        self.assertEqual(match, candidate)

    def test_fuzzy_name_match(self):
        candidate = Tournament(
            id=2,
            name="X-Wing World Open '24", # Similar enough? Or "X-Wing Worlds Open"
            date=self.base_date,
            platform=Platform.ROLLBETTER,
            player_count=20,
            url="http://rollbetter.gg/2"
        )
        # SequenceMatcher ratio for these strings might be > 0.85
        # "X-Wing World Open 2024" vs "X-Wing World Open '24"
        # ratio: 0.91
        match = self.service.find_duplicate(self.target, [candidate])
        self.assertEqual(match, candidate)

    def test_date_mismatch(self):
        candidate = Tournament(
            id=2,
            name="X-Wing World Open 2024",
            date=self.base_date + timedelta(days=10),
            platform=Platform.ROLLBETTER,
            player_count=20,
            url="http://rollbetter.gg/2"
        )
        match = self.service.find_duplicate(self.target, [candidate])
        self.assertIsNone(match)

    def test_player_overlap_match(self):
        candidate = Tournament(
            id=2,
            name="Completely Different Name",
            date=self.base_date,
            platform=Platform.ROLLBETTER,
            player_count=20,
            url="http://rollbetter.gg/2"
        )
        
        c_players = [
            PlayerResult(id=4, tournament_id=2, player_name="Han Solo"), # Match
            PlayerResult(id=5, tournament_id=2, player_name="Luke Skywalker"), # Match
            PlayerResult(id=6, tournament_id=2, player_name="Biggs Darklighter"),
        ]
        # Overlap: 2/4 union (Han, Luke) / (Han, Luke, Wedge, Biggs) = 0.5
        # Threshold > 0.5. Let's make it 3/4 matches.
        c_players.append(PlayerResult(id=7, tournament_id=2, player_name="Wedge Antilles"))
        # Union: Han, Luke, Wedge, Biggs (4). Intersect: Han, Luke, Wedge (3). 3/4 = 0.75
        
        c_map = {2: c_players}
        
        match = self.service.find_duplicate(
            self.target, 
            [candidate], 
            target_players=self.players_target, 
            candidate_players_map=c_map
        )
        self.assertEqual(match, candidate)

if __name__ == '__main__':
    unittest.main()
