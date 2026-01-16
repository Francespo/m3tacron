"""Debug XWS links - save to file."""
import asyncio
import sys
sys.path.insert(0, '.')

from m3tacron.backend.scrapers.longshanks import scrape_tournament


async def debug_xws():
    result = await scrape_tournament(31565, subdomain="xwing")
    players = result.get("players", [])
    
    with_xws = [p for p in players if p.get("xws_link")]
    
    with open("xws_debug_output.txt", "w", encoding="utf-8") as f:
        f.write(f"FULL XWS LINKS ({len(with_xws)} found)\n")
        f.write("="*80 + "\n\n")
        
        for p in with_xws:
            link = p['xws_link']
            f.write(f"--- #{p['rank']} {p['name']} ---\n")
            f.write(f"Link length: {len(link)} chars\n")
            f.write(f"Full link:\n{link}\n\n")
    
    print("Output saved to xws_debug_output.txt")


if __name__ == "__main__":
    asyncio.run(debug_xws())
