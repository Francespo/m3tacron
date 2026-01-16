"""Show XWS results from Longshanks tournament."""
import asyncio
import sys
import os

# Fix console encoding for Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

sys.path.insert(0, '.')

from m3tacron.backend.scrapers.longshanks import scrape_tournament


async def show_xws():
    print("Fetching tournament data...")
    result = await scrape_tournament(31565, subdomain="xwing")
    players = result.get("players", [])
    
    print("=" * 80)
    print("XWS RESULTS - Zasypana Lomza - PSO side")
    print("=" * 80)
    
    with_xws = [p for p in players if p.get("xws_link")]
    
    print(f"\nFound {len(with_xws)} players with XWS links:\n")
    
    for p in with_xws:
        # Sanitize player name for console output
        name = p['name'].encode('ascii', 'replace').decode('ascii')
        print(f"#{p['rank']} {name}")
        print(f"   {p['xws_link']}")
        print()


if __name__ == "__main__":
    asyncio.run(show_xws())
