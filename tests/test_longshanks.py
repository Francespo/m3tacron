"""Test Longshanks scraper with X-Wing subdomains."""
import asyncio
import sys
sys.path.insert(0, '.')

from datetime import datetime
from sqlmodel import Session, select
from m3tacron.backend.database import engine, create_db_and_tables
from m3tacron.backend.models import Tournament, PlayerResult
from m3tacron.backend.scrapers.longshanks import (
    scrape_tournament,
    scrape_longshanks_history,
)


async def test_longshanks_history():
    """Test scraping tournament history from X-Wing subdomains."""
    print("=" * 60)
    print("Testing Longshanks History Scraper")
    print("=" * 60)
    
    # Test 2.5 history
    print("\n1. Scraping X-Wing 2.5 history...")
    tournaments_25 = await scrape_longshanks_history(subdomain="xwing", max_pages=1)
    print(f"   [OK] Found {len(tournaments_25)} tournaments")
    
    if tournaments_25:
        print("\n   Recent 2.5 tournaments:")
        for t in tournaments_25[:3]:
            print(f"   - {t['name']} ({t['date'].strftime('%Y-%m-%d')}) - {t['player_count']} players")
    
    # Test 2.0 legacy history
    print("\n2. Scraping X-Wing Legacy (2.0) history...")
    tournaments_20 = await scrape_longshanks_history(subdomain="xwing-legacy", max_pages=1)
    print(f"   [OK] Found {len(tournaments_20)} tournaments")
    
    if tournaments_20:
        print("\n   Recent 2.0 tournaments:")
        for t in tournaments_20[:3]:
            print(f"   - {t['name']} ({t['date'].strftime('%Y-%m-%d')}) - {t['player_count']} players")
    
    return tournaments_25, tournaments_20


async def test_tournament_scrape():
    """Test scraping a single tournament with player lists."""
    print("\n" + "=" * 60)
    print("Testing Single Tournament Scrape")
    print("=" * 60)
    
    # First get a tournament ID from history
    tournaments = await scrape_longshanks_history(subdomain="xwing", max_pages=1)
    
    if not tournaments:
        print("   [FAIL] No tournaments found in history")
        return None
    
    # Pick the first one
    event = tournaments[0]
    event_id = event["id"]
    subdomain = "xwing"
    
    print(f"\n1. Scraping event {event_id}: {event['name']}...")
    result = await scrape_tournament(event_id, subdomain=subdomain)
    
    if not result:
        print("   [FAIL] Failed to scrape tournament")
        return None
    
    tournament = result.get("tournament", {})
    players = result.get("players", [])
    
    print(f"   [OK] Tournament: {tournament.get('name')}")
    print(f"   [OK] Format: {tournament.get('format')}")
    print(f"   [OK] Players found: {len(players)}")
    
    if players:
        print("\n   Player results:")
        for p in players[:5]:
            faction = p.get('faction', 'Unknown')
            xws_link = p.get('xws_link', '')
            link_indicator = "[LIST]" if xws_link else "[NO LIST]"
            print(f"   - #{p['rank']} {p['name']} ({faction}) {link_indicator}")
        
        # Count players with lists
        with_lists = sum(1 for p in players if p.get('xws_link'))
        print(f"\n   Players with XWS links: {with_lists}/{len(players)}")
    
    return result


async def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("LONGSHANKS SCRAPER TEST SUITE")
    print("=" * 60 + "\n")
    
    # Test history scraping
    await test_longshanks_history()
    
    # Test single tournament scrape
    await test_tournament_scrape()
    
    print("\n" + "=" * 60)
    print("All tests complete!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
