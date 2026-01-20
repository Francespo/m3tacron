from m3tacron.backend.models import Match
from m3tacron.backend.enums.scenarios import Scenario

def verify():
    print(f"Scenario.CHANCE_ENGAGEMENT value: {Scenario.CHANCE_ENGAGEMENT}")
    match = Match(
        tournament_id=1,
        round_number=1,
        player1_id=1,
        scenario=Scenario.CHANCE_ENGAGEMENT
    )
    print(f"Match scenario: {match.scenario}")
    assert match.scenario == Scenario.CHANCE_ENGAGEMENT
    
    match.first_player_id = 1
    print(f"Match first player: {match.first_player_id}")
    assert match.first_player_id == 1
    
    from m3tacron.backend.enums.round_types import RoundType
    print(f"Match round_type (default): {match.round_type}")
    print(f"Match round_type label: {match.round_type.label}")
    assert match.round_type == RoundType.SWISS
    assert match.round_type.label == "Swiss"
    
    match.round_type = RoundType.CUT
    print(f"Match round_type (updated): {match.round_type}")
    print(f"Match round_type label: {match.round_type.label}")
    assert match.round_type == RoundType.CUT
    assert match.round_type.label == "Cut"
    
    print(f"Scenario label: {match.scenario.label}")
    assert match.scenario.label == "Chance Engagement"

    print("Verification successful!")

if __name__ == "__main__":
    verify()
