"""
Populate database with Legacy 2.0 tournaments from RollBetter.
"""
import asyncio
import sys
sys.path.insert(0, '.')

from datetime import datetime
from sqlmodel import Session, select
from m3tacron.backend.database import engine, create_db_and_tables
from m3tacron.backend.models import Tournament, PlayerResult, Match
from m3tacron.backend.scrapers.rollbetter import (
    fetch_tournament,
    fetch_players,
    fetch_round_matches,
    extract_xws_from_player,
)


# Legacy 2.0 tournament IDs to import
TOURNAMENT_IDS = [2510, 2530, 2502]


async def import_tournament(tournament_id: int, session: Session) -> bool:
    """Import a single tournament into the database."""
    print(f"\n{'='*50}")
    print(f"Importing tournament {tournament_id}...")
    
    # Check if already exists
    existing = session.exec(
        select(Tournament).where(Tournament.url.contains(str(tournament_id)))
    ).first()
    if existing:
        print(f"  → Already exists: {existing.name}")
        return False
    
    # Fetch tournament metadata
    t_data = await fetch_tournament(tournament_id)
    if not t_data:
        print(f"  ✗ Failed to fetch tournament")
        return False
    
    # Create tournament record
    tournament = Tournament(
        name=t_data.get("name", f"Tournament {tournament_id}"),
        date=datetime.now(),  # Will update with actual date if available
        platform="RollBetter",
        format="Legacy 2.0",
        url=f"https://rollbetter.gg/tournaments/{tournament_id}",
    )
    session.add(tournament)
    session.commit()
    session.refresh(tournament)
    print(f"  ✓ Tournament: {tournament.name} (ID: {tournament.id})")
    
    # Fetch and import players
    players_data = await fetch_players(tournament_id)
    print(f"  → Found {len(players_data)} players")
    
    player_map = {}  # RollBetter player ID -> our PlayerResult ID
    
    for i, p in enumerate(players_data):
        # Extract player info
        player_name = p.get("name") or p.get("displayName") or f"Player {i+1}"
        rank = p.get("rank") or p.get("position") or (i + 1)
        
        # Extract XWS
        xws = extract_xws_from_player(p)
        if not xws:
            # Try to get squad data in different format
            squad = p.get("squad") or p.get("list") or {}
            if isinstance(squad, dict):
                xws = squad
        
        # Calculate points (try different field names)
        points = 200  # Default
        if isinstance(xws, dict) and "points" in xws:
            points = xws.get("points", 200)
        
        player_result = PlayerResult(
            tournament_id=tournament.id,
            player_name=player_name,
            rank=rank,
            list_json=xws if xws else {},
            points_at_event=points,
        )
        session.add(player_result)
        session.commit()
        session.refresh(player_result)
        
        # Map RollBetter ID to our ID
        rb_id = p.get("id") or p.get("playerId")
        if rb_id:
            player_map[rb_id] = player_result.id
    
    print(f"  ✓ Imported {len(players_data)} player results")
    
    # Fetch and import matches
    rounds_info = t_data.get("rounds", [])
    total_matches = 0
    
    for round_num in range(1, len(rounds_info) + 1):
        matches_data = await fetch_round_matches(tournament_id, round_num)
        
        for m in matches_data:
            # Extract match data (field names vary)
            p1_id = m.get("player1Id") or m.get("player1")
            p2_id = m.get("player2Id") or m.get("player2")
            winner_id = m.get("winnerId") or m.get("winner")
            p1_score = m.get("player1Score") or m.get("score1") or 0
            p2_score = m.get("player2Score") or m.get("score2") or 0
            
            match = Match(
                tournament_id=tournament.id,
                round_number=round_num,
                round_type="swiss",
                player1_id=player_map.get(p1_id),
                player2_id=player_map.get(p2_id),
                winner_id=player_map.get(winner_id),
                player1_score=p1_score if isinstance(p1_score, int) else 0,
                player2_score=p2_score if isinstance(p2_score, int) else 0,
                is_bye=(p2_id is None or m.get("isBye", False)),
            )
            session.add(match)
            total_matches += 1
        
        session.commit()
    
    print(f"  ✓ Imported {total_matches} matches across {len(rounds_info)} rounds")
    return True


async def main():
    print("="*60)
    print("M3taCron Database Population - Legacy 2.0 Tournaments")
    print("="*60)
    
    # Initialize database
    create_db_and_tables()
    print("✓ Database initialized")
    
    imported = 0
    with Session(engine) as session:
        for tid in TOURNAMENT_IDS:
            try:
                if await import_tournament(tid, session):
                    imported += 1
            except Exception as e:
                print(f"  ✗ Error importing {tid}: {e}")
    
    print("\n" + "="*60)
    print(f"Import complete! {imported}/{len(TOURNAMENT_IDS)} tournaments imported.")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())
