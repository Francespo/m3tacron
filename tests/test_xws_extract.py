"""Quick test for XWS extraction from Longshanks."""
import asyncio
import sys
sys.path.insert(0, '.')

from m3tacron.backend.scrapers.longshanks import scrape_tournament


async def test_xws_extraction():
    """Test XWS extraction from a tournament with encoded lists."""
    print("=" * 60)
    print("Testing XWS Extraction from Longshanks")
    print("=" * 60)
    
    # Event 31565 "Zasypana Lomza" has encoded lists
    event_id = 31565
    subdomain = "xwing"
    
    print(f"\nScraping event {event_id} from {subdomain}.longshanks.org...")
    result = await scrape_tournament(event_id, subdomain=subdomain)
    
    if not result:
        print("[FAIL] Failed to scrape tournament")
        return
    
    tournament = result.get("tournament", {})
    players = result.get("players", [])
    
    print(f"\n[OK] Tournament: {tournament.get('name')}")
    print(f"[OK] Format: {tournament.get('format')}")
    print(f"[OK] Players found: {len(players)}")
    
    # Count players with XWS links
    with_lists = [p for p in players if p.get('xws_link')]
    print(f"\nPlayers with XWS links: {len(with_lists)}/{len(players)}")
    
    if with_lists:
        print("\nPlayers with lists:")
        for p in with_lists[:5]:
            link = p.get('xws_link', '')[:60] + "..." if len(p.get('xws_link', '')) > 60 else p.get('xws_link', '')
            print(f"  #{p['rank']} {p['name']}: {link}")
    else:
        print("\n[WARN] No XWS links extracted")
        if players:
            print("\nAll players found:")
            for p in players[:10]:
                print(f"  #{p['rank']} {p['name']} (faction: {p.get('faction')})")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    asyncio.run(test_xws_extraction())
