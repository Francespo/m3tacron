"""Test format detection on real tournament data."""
import asyncio
import sys
sys.path.insert(0, '.')

from m3tacron.backend.format_detector import (
    detect_format_from_xws,
    detect_format_from_tournament_lists,
    detect_format_from_listfortress,
)
from m3tacron.backend.scrapers.listfortress import fetch_tournament_details


async def test_format_detection():
    print("=" * 60)
    print("Testing Format Detection")
    print("=" * 60)
    
    # Test with known XWS samples
    print("\n1. Testing XWS Builder Detection")
    print("-" * 40)
    
    test_cases = [
        {"builder": "YASB XWA 2.5", "expected": "XWA"},
        {"builder": "YASB 2.0 legacy", "expected": "Legacy (X2PO)"},
        {"builder": "YASB 2.0 raithos", "expected": "FFG"},
        {"builder": "YASB 2.0 lorenzosanti", "expected": "Legacy (XLC)"},
        {"builder": "launchbaynext", "ruleset": "XWA", "expected": "XWA"},
        {"builder": "launchbaynext", "ruleset": "AMG", "expected": "AMG"},
        {"builder": "launchbaynext", "ruleset": "legacy", "expected": "Legacy (X2PO)"},
        {"builder": "xwingsquaddesigner", "expected": None},
    ]
    
    for case in test_cases:
        xws = {"builder": case["builder"]}
        if "ruleset" in case:
            xws["ruleset"] = case["ruleset"]
        
        result = detect_format_from_xws(xws)
        expected = case["expected"]
        status = "[OK]" if result == expected else "[FAIL]"
        print(f"  {status} '{case['builder']}' -> {result} (expected {expected})")
    
    # Test on real ListFortress tournaments
    print("\n2. Testing on Real ListFortress Data")
    print("-" * 40)
    
    # Fetch some recent tournaments
    tournament_ids = [10073, 10074, 10075]  # Sample IDs
    
    for tid in tournament_ids:
        try:
            details = await fetch_tournament_details(tid)
            if not details:
                print(f"  - Tournament {tid}: No data")
                continue
            
            name = details.get("name", "Unknown")
            lf_format = details.get("format_id", "")
            participants = details.get("participants", [])
            
            # Extract XWS lists
            xws_lists = []
            for p in participants[:5]:  # Sample first 5
                xws = p.get("list_json") or p.get("xws")
                if xws:
                    xws_lists.append(xws)
            
            # Detect format
            if xws_lists:
                macro, sub = detect_format_from_tournament_lists(xws_lists)
            else:
                macro, sub = detect_format_from_listfortress(
                    lf_format, name, "2026-01-01", []
                )
            
            print(f"  - {name[:40]}: {macro} {sub}")
            print(f"    LF format: {lf_format}, XWS samples: {len(xws_lists)}")
            
            # Show first XWS builder if available
            if xws_lists and xws_lists[0]:
                builder = xws_lists[0].get("builder", "N/A")
                ruleset = xws_lists[0].get("ruleset", "N/A")
                print(f"    Builder: {builder[:50]}...")
                print(f"    Ruleset: {ruleset}")
        except Exception as e:
            print(f"  - Tournament {tid}: Error - {e}")
    
    print("\n" + "=" * 60)
    print("Format detection test complete!")


if __name__ == "__main__":
    asyncio.run(test_format_detection())
