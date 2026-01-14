"""
Consolidated Import Script for M3taCron.

Imports data from:
1. RollBetter (JSON API) - via static ID list
2. ListFortress (JSON API) - via listing endpoint
3. Longshanks (Playwright Scraper) - via static ID list

Applies format detection using XWS data and heuristics.
"""
import asyncio
import sys
import os
from datetime import datetime, timedelta

sys.path.insert(0, '.')

from sqlmodel import Session, select
from m3tacron.backend.database import engine, create_db_and_tables
from m3tacron.backend.models import Tournament, PlayerResult, Match

# Scrapers
from m3tacron.backend.scrapers.rollbetter import (
    fetch_tournament as fetch_rb_tournament,
    fetch_players as fetch_rb_players,
    fetch_round_matches as fetch_rb_matches,
    extract_xws_from_player as extract_rb_xws
)
from m3tacron.backend.scrapers.listfortress import (
    fetch_tournaments as fetch_lf_tournaments,
    fetch_tournament_details as fetch_lf_details,
    extract_xws_from_participant as extract_lf_xws
)
from m3tacron.backend.scrapers.longshanks import scrape_tournament as scrape_ls_tournament

# Format Detector
from m3tacron.backend.format_detector import (
    detect_format_from_tournament_lists,
    detect_format_from_listfortress,
    get_format_display,
    MACRO_2_0, MACRO_2_5, MACRO_OTHER,
    SUB_X2PO, SUB_AMG, SUB_XWA, SUB_UNKNOWN
)

# Known RollBetter IDs (Legacy 2.0 focus)
RB_IDS = [2510, 2530, 2502] 

async def import_rollbetter(session: Session):
    """Import specific RollBetter tournaments."""
    print(f"\n--- Importing RollBetter (Static List) ---")
    
    count = 0
    for t_id in RB_IDS:
        print(f"Fetching RB {t_id}...")
        try:
            t_data = await fetch_rb_tournament(t_id)
            if not t_data:
                print(f"  ✗ Failed to fetch RB {t_id}")
                continue
            
            t_name = t_data.get("name", "Unknown")
            players = await fetch_rb_players(t_id)
            
            if len(players) < 4:
                print(f"  ✗ Too few players: {len(players)}")
                continue

            # Detect format
            rb_format_raw = t_data.get("format", "Unknown")
            print(f"  RB Format Raw: {rb_format_raw}")
            
            # Extract XWS to help detection
            xws_lists = []
            for p in players:
                xws = extract_rb_xws(p)
                if xws:
                    xws_lists.append(xws)
            
            # Default RB detection
            macro = MACRO_OTHER
            sub = SUB_UNKNOWN
            
            if "Legacy 2.0" in rb_format_raw or "2.0" in rb_format_raw: # Expanded check
                macro = MACRO_2_0
                # Check XWS for X2PO vs FFG vs XLC
                m, s = detect_format_from_tournament_lists(xws_lists)
                sub = s if s != SUB_UNKNOWN else SUB_X2PO
            elif "Standard" in rb_format_raw or "Extended" in rb_format_raw:
                macro = MACRO_2_5
                # Check XWS for XWA vs AMG
                m, s = detect_format_from_tournament_lists(xws_lists)
                sub = s if s != SUB_UNKNOWN else SUB_AMG
                
            display_format = get_format_display(macro, sub)
            
            # Save to DB
            t = Tournament(
                name=t_name,
                date=datetime.now(), # Placeholder as API date parsing varies
                platform="RollBetter",
                format=display_format,
                macro_format=macro,
                sub_format=sub,
                url=f"https://rollbetter.gg/tournaments/{t_id}"
            )
            session.add(t)
            session.commit()
            session.refresh(t)
            
            player_map = {}
            # Save players
            for i, p in enumerate(players):
                p_name = p.get("name") or p.get("displayName") or f"Player {i+1}"
                xws = extract_rb_xws(p)
                
                pr = PlayerResult(
                    tournament_id=t.id,
                    player_name=p_name or "Unknown Player",
                    rank=p.get("rank") or (i+1),
                    list_json=xws or {},
                    points_at_event=0
                )
                session.add(pr)
                session.commit()
                session.refresh(pr)
                
                # Map ID
                rb_pid = p.get("id") or p.get("playerId")
                if rb_pid:
                    player_map[rb_pid] = pr.id
            
            # Save Matches (if rounds > 0)
            rounds = t_data.get("rounds", [])
            for r_num in range(1, len(rounds) + 1):
                try:
                    matches = await fetch_rb_matches(t_id, r_num)
                    for m in matches:
                        p1_id = m.get("player1Id")
                        p2_id = m.get("player2Id")
                        winner_id = m.get("winnerId")
                        
                        match = Match(
                            tournament_id=t.id,
                            round_number=r_num,
                            round_type="swiss",
                            player1_id=player_map.get(p1_id),
                            player2_id=player_map.get(p2_id),
                            winner_id=player_map.get(winner_id),
                            player1_score=m.get("player1Score", 0) or 0,
                            player2_score=m.get("player2Score", 0) or 0,
                            is_bye=(p2_id is None)
                        )
                        session.add(match)
                except Exception:
                    pass # Ignore match errors for now
            
            session.commit()
            print(f"  ✓ Imported RB: {t_name} ({display_format}) - {len(players)} players")
            count += 1

        except Exception as e:
            print(f"  ✗ Error RB {t_id}: {e}")
            
    print(f"Imported {count} RollBetter tournaments.")


async def import_listfortress(session: Session, limit: int = 5):
    """Import recent tournaments from ListFortress."""
    print(f"\n--- Importing ListFortress (limit={limit}) ---")
    tournaments = await fetch_lf_tournaments(limit=limit * 4) 
    
    count = 0
    for t_summary in tournaments:
        if count >= limit:
            break
            
        t_id = t_summary.get("id")
        t_name = t_summary.get("name")
        t_date = t_summary.get("date", "1900-01-01")
        lf_format = str(t_summary.get("format_id", "0"))
        
        # Pass if too small participant count in summary
        # (Optimization: check summary first if available)
        
        try:
            details = await fetch_lf_details(t_id)
        except Exception as e:
            print(f"Failed to fetch LF {t_id}: {e}")
            continue
            
        if not details:
            continue
            
        participants = details.get("participants", [])
        if len(participants) < 8: # Increased threshold
            continue
            
        print(f"  Processing {t_name}: {len(participants)} players")
            
        # Extract XWS
        xws_lists = []
        for i, p in enumerate(participants):
            if i == 0:
                 print(f"  Debug P0 keys: {list(p.keys())}")
                 raw_list = p.get("list_json")
                 print(f"  Debug P0 list_json type: {type(raw_list)}")
                 if isinstance(raw_list, dict):
                     print(f"  Debug P0 list_json keys: {list(raw_list.keys())}")
            
            xws = extract_lf_xws(p)
            if xws:
                xws_lists.append(xws)
                # Debug first valid XWS
                if len(xws_lists) == 1:
                     print(f"  Debug XWS Valid (first): keys={list(xws.keys())}")
                     if "vendor" in xws:
                         print(f"  Debug XWS Vendor: {xws['vendor']}")
                     if "builder" in xws:
                         print(f"  Debug XWS Builder: {xws['builder']}")
        
        print(f"  Extracted {len(xws_lists)} valid XWS lists")
        
        # Detect Format
        macro, sub = detect_format_from_listfortress(
            lf_format, t_name, t_date, xws_lists
        )
        display_format = get_format_display(macro, sub)
        
        # Save to DB
        t = Tournament(
            name=t_name,
            date=datetime.fromisoformat(t_date),
            platform="ListFortress",
            format=display_format,
            macro_format=macro,
            sub_format=sub,
            url=f"https://listfortress.com/tournaments/{t_id}"
        )
        session.add(t)
        session.commit()
        session.refresh(t)
        
        # Save Players
        for p in participants:
            p_name = p.get("name")
            pr = PlayerResult(
                tournament_id=t.id,
                player_name=p_name or "Unknown Player",
                rank=p.get("rank", 0),
                swiss_rank=p.get("swiss_rank"),
                list_json=extract_lf_xws(p) or {},
                points_at_event=p.get("score", 0)
            )
            session.add(pr)
            
        session.commit()
        print(f"  ✓ Imported LF: {t_name} ({display_format}) - {len(participants)} players")
        count += 1
        
    print(f"Imported {count} ListFortress tournaments.")


async def import_longshanks(session: Session):
    """Import specific Longshanks tournament (as example)."""
    print(f"\n--- Importing Longshanks (Example) ---")
    event_ids = [30874] 
    
    for eid in event_ids:
        try:
            result = await scrape_ls_tournament(eid)
            if not result:
                continue
                
            tournament = result.get("tournament")
            players = result.get("players")
            
            # Simple heuristic since XWS is scarce on LS
            display_format = "2.5 XWA" # Assume recent LS is XWA
            macro = MACRO_2_5
            sub = SUB_XWA
                
            t = Tournament(
                name=tournament.get("name"),
                date=tournament.get("date"),
                platform="Longshanks",
                format=display_format,
                macro_format=macro,
                sub_format=sub,
                url=tournament.get("url")
            )
            session.add(t)
            session.commit()
            session.refresh(t)
            
            for p in players:
                p_name = p.get("name")
                pr = PlayerResult(
                    tournament_id=t.id,
                    player_name=p_name or "Unknown Player",
                    rank=p.get("rank"),
                    list_json={"faction": p.get("faction")} if p.get("faction") else {},
                    points_at_event=0
                )
                session.add(pr)
                
            session.commit()
            print(f"  ✓ Imported LS: {t.name} ({display_format}) - {len(players)} players")
            
        except Exception as e:
            print(f"Failed to import LS {eid}: {e}")


def reset_database():
    """Delete the database file if it exists."""
    db_file = "metacron.db"
    if os.path.exists(db_file):
        print(f"Deleting existing database: {db_file}")
        try:
            os.remove(db_file)
            print("✓ Database deleted")
        except Exception as e:
            print(f"✗ Failed to delete database: {e}")
    else:
        print(f"Database file not found: {db_file}")


async def main():
    print("="*60)
    print("M3taCron - Comprehensive Data Import with Format Detection")
    print("="*60)
    
    reset_database()
    create_db_and_tables()
    print("✓ Tables created")
    
    with Session(engine) as session:
        await import_rollbetter(session)
        await import_listfortress(session, limit=5)
        await import_longshanks(session)
    
    print("\n" + "="*60)
    print("Import process complete!")


if __name__ == "__main__":
    asyncio.run(main())
