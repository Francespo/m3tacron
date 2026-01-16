"""Test full XWS extraction from Longshanks."""
import asyncio
import json
import sys
sys.path.insert(0, '.')

from m3tacron.backend.scrapers.longshanks import scrape_tournament


async def main():
    print("Testing full XWS extraction...")
    result = await scrape_tournament(31565, subdomain="xwing")
    
    players = result.get("players", [])
    with_xws = [p for p in players if p.get("xws")]
    
    output = {
        "tournament": result.get("tournament", {}).get("name"),
        "players_with_xws": []
    }
    
    for p in with_xws:
        xws = p.get("xws", {})
        output["players_with_xws"].append({
            "rank": p["rank"],
            "name": p["name"],
            "xws": xws
        })
    
    # Save to file
    with open("xws_full_test.json", "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print(f"\nExtracted {len(with_xws)} XWS entries")
    print("Saved to xws_full_test.json")
    
    # Preview first entry
    if with_xws:
        print("\nPreview first XWS:")
        print(json.dumps(output["players_with_xws"][0], indent=2, ensure_ascii=False))


if __name__ == "__main__":
    asyncio.run(main())
