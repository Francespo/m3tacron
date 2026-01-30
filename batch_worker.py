import sys
import logging
import json
from pathlib import Path
from sqlmodel import Session, create_engine, SQLModel, select, delete

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("batch_worker")

# DB Import
from m3tacron.backend.models import Tournament, PlayerResult, Match, RoundType, Scenario

# Scraper Imports
from m3tacron.backend.scrapers.rollbetter import RollbetterScraper
from m3tacron.backend.scrapers.longshanks import LongshanksScraper

DB_PATH = "scraped_data.db"
# Allow overriding DB path (useful for testing)
if "test" in sys.argv:
    DB_PATH = "test_results.db"

DATABASE_URL = f"sqlite:///{DB_PATH}"

def get_engine():
    return create_engine(DATABASE_URL)

def run_url(url: str):
    logger.info(f"--- Worker Processing: {url} ---")
    
    # 1. Determin Scraper
    scraper = None
    if "rollbetter.gg" in url:
        scraper = RollbetterScraper()
    elif "longshanks.org" in url:
        scraper = LongshanksScraper()
    else:
        logger.error(f"Unknown URL type: {url}")
        return

    engine = get_engine()
    SQLModel.metadata.create_all(engine)

    try:
        # Extract ID (rough logic, scrapers handle it better internally usually but we need it for cache key)
        # Actually scrapers take logic from ID.
        # Longshanks: event/ID
        # Rollbetter: tournaments/ID
        tid = url.rstrip("/").split("/")[-1]
        
        with Session(engine) as session:
            # 1. SCOPE TOURNAMENT
            t_data = scraper.get_tournament_data(tid)
            print(f"Scraped Tournament: {t_data.name} | {t_data.date} | {t_data.location}")
            
            # Use merge to avoid PK violation if exists
            session.merge(t_data)
            session.commit() 
            # Re-fetch to ensure we have the attached object
            t_data = session.get(Tournament, t_data.id)
            
            # 2. SAVE PLAYERS & BUILD MAP
            players = scraper.get_participants(tid)
            print(f"Scraped {len(players)} players.")
            
            player_map = {} 
            
            # RE-IMPLEMENT Player Loop safely
            for p in players:
                 p.tournament_id = t_data.id
                 # Check if exists
                 existing = session.exec(select(PlayerResult).where(
                     PlayerResult.tournament_id == t_data.id, 
                     PlayerResult.player_name == p.player_name
                 )).first()
                 
                 p_bound = None
                 if existing:
                     # Update
                     existing.swiss_rank = p.swiss_rank
                     existing.swiss_points = p.swiss_points
                     existing.swiss_wins = p.swiss_wins
                     existing.swiss_losses = p.swiss_losses
                     existing.swiss_draws = p.swiss_draws
                     existing.cut_rank = p.cut_rank
                     existing.cut_wins = p.cut_wins
                     existing.cut_losses = p.cut_losses
                     existing.cut_draws = p.cut_draws
                     existing.list_json = p.list_json
                     session.add(existing)
                     session.commit()
                     session.refresh(existing)
                     p_bound = existing
                 else:
                     session.add(p)
                     session.commit()
                     session.refresh(p)
                     p_bound = p
                 
                 clean_name = p.player_name.strip()
                 player_map[clean_name] = p_bound.id
                 player_map[clean_name.lower()] = p_bound.id

            print(f"Mapped {len(player_map) // 2} players. Sample: {list(player_map.keys())[:5]}")

            # 3. SAVE MATCHES 
            # Clear existing matches for this tournament to avoid dupes/integrity errors on re-run
            session.exec(delete(Match).where(Match.tournament_id == t_data.id))
            session.commit()

            matches = scraper.get_matches(tid)
            print(f"Scraped {len(matches)} matches.")
            
            saved_matches = 0
            for i, m_data in enumerate(matches):
                # Check mapping
                p1_name = m_data.get("p1_name_temp") or m_data.get("player1_name") # Handle key variance
                p2_name = m_data.get("p2_name_temp") or m_data.get("player2_name")
                
                p1_id = None
                p2_id = None

                if p1_name:
                    p1_clean = p1_name.strip()
                    if p1_clean in player_map:
                        p1_id = player_map[p1_clean]
                    elif p1_clean.lower() in player_map:
                        p1_id = player_map[p1_clean.lower()]
                    else:
                        if i < 3: 
                            print(f"DEBUG: P1 {repr(p1_name)} NOT in map.")
                
                if p2_name:
                    p2_clean = p2_name.strip()
                    if p2_clean in player_map:
                        p2_id = player_map[p2_clean]
                    elif p2_clean.lower() in player_map:
                        p2_id = player_map[p2_clean.lower()]
                    else:
                        if i < 3: 
                            print(f"DEBUG: P2 {repr(p2_name)} NOT in map.")
                
                if p1_id:
                    # Enum Serialization
                    r_type = m_data["round_type"]
                    if hasattr(r_type, "value"): r_type = r_type.value
                    
                    scen = m_data["scenario"]
                    if hasattr(scen, "value"): scen = scen.value

                    # Create the actual Match DB object now 
                    m = Match(
                        tournament_id=t_data.id,
                        round_number=m_data["round_number"],
                        round_type=r_type,
                        scenario=scen,
                        player1_id=p1_id,
                        player2_id=p2_id,
                        player1_score=m_data["player1_score"],
                        player2_score=m_data["player2_score"],
                        is_bye=m_data["is_bye"]
                    )
                    
                    # Winner Assignment (Robust)
                    winner_name = m_data.get("winner_name_temp")
                    if winner_name:
                        # Clean and check against cleaned P1/P2 names
                        w_clean = winner_name.strip().lower()
                        p1_clean_check = p1_name.strip().lower() if p1_name else ""
                        p2_clean_check = p2_name.strip().lower() if p2_name else ""
                        
                        if w_clean == p1_clean_check:
                            m.winner_id = p1_id
                        elif w_clean == p2_clean_check:
                            m.winner_id = p2_id
                    
                    # Fallback: Score-based winner if not explicit
                    if not m.winner_id and m.player1_score != m.player2_score:
                        if m.player1_score > m.player2_score:
                            m.winner_id = p1_id
                        else:
                            m.winner_id = p2_id
                    
                    session.add(m)
                    saved_matches += 1
                elif i < 3:
                     print(f"DEBUG: Match {i} has NO player1_id. p1={repr(p1_name)}")
            
            session.commit()
            print(f"DONE: Saved {saved_matches} matches to DB.")

    except Exception as e:
        logger.error(f"Worker Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python batch_worker.py <url> [test]")
        sys.exit(1)
    
    run_url(sys.argv[1])
