"""Extract XWS data from Longshanks tournament and save both links and XWS JSON."""
import asyncio
import json
import re
import sys
from urllib.parse import unquote, parse_qs, urlparse

sys.path.insert(0, '.')

from m3tacron.backend.scrapers.longshanks import scrape_tournament


def decode_yasb_url(url: str) -> dict:
    """
    Decode a YASB URL into XWS-like data.
    
    YASB URLs contain faction and encoded squad in 'd' parameter.
    Full XWS decoding requires YASB's card database, but we can extract
    the encoded string and basic info.
    """
    parsed = urlparse(url)
    params = parse_qs(parsed.query)
    
    xws = {
        "link": url,
        "builder": "yasb" if "yasb" in url else "launchbaynext",
    }
    
    # Extract faction
    if "f" in params:
        xws["faction"] = unquote(params["f"][0])
    
    # Extract squadron name
    if "sn" in params:
        xws["name"] = unquote(params["sn"][0])
    
    # Extract encoded data (contains ship/pilot/upgrade IDs)
    if "d" in params:
        xws["encoded_data"] = params["d"][0]
    
    # Extract obstacles
    if "obs" in params:
        xws["obstacles"] = params["obs"][0].split(",")
    
    return xws


async def main():
    print("Fetching tournament data from Longshanks...")
    result = await scrape_tournament(31565, subdomain="xwing")
    
    tournament = result.get("tournament", {})
    players = result.get("players", [])
    
    with_xws = [p for p in players if p.get("xws_link")]
    
    # Build output data
    output = {
        "tournament": {
            "name": tournament.get("name"),
            "date": str(tournament.get("date")),
            "format": tournament.get("format"),
            "platform": tournament.get("platform"),
            "url": tournament.get("url"),
        },
        "players_with_lists": []
    }
    
    for p in with_xws:
        link = p["xws_link"]
        xws_data = decode_yasb_url(link)
        
        player_data = {
            "rank": p["rank"],
            "name": p["name"],
            "xws_link": link,
            "xws": xws_data
        }
        output["players_with_lists"].append(player_data)
    
    # Save to file
    with open("xws_extracted.json", "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print(f"\nSaved {len(with_xws)} XWS entries to xws_extracted.json")
    print("\nPreview:")
    print(json.dumps(output, indent=2, ensure_ascii=False)[:2000])


if __name__ == "__main__":
    asyncio.run(main())
