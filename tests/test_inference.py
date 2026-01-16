"""Test inference logic."""
import json
import sys
import os
sys.path.insert(0, ".")

from m3tacron.backend.inference import infer_format_from_xws
from m3tacron.backend.models import GameFormat

def test_inference():
    # Load sample data
    try:
        with open("rollbetter_playwright_test.json", "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        print("Sample file not found, creating dummy data")
        data = {"players": []}

    players = data.get("players", [])
    
    print(f"Testing inference on {len(players)} players...")
    
    # Add manual test cases based on user request
    manual_cases = [
        # User provided examples
        {
            "case": "Lorenzo Santi (XLC)",
            "xws": {"vendor": {"yasb": {"builder": "YASB 2.0", "builder_url": "https://lorenzosanti359-beep.github.io/X-wing-builder-madness/", "link": "https://lorenzosanti359-beep.github.io/X-wing-builder-madness/?f=Galactic%20Republic..."}}, "version": "2.0.0"},
            "expected": GameFormat.LEGACY_XLC.value
        },
        {
            "case": "XWA Standard",
            "xws": {"vendor": {"yasb": {"builder": "YASB - X-Wing 2.5 XWA", "builder_url": "https://yasb.app/", "link": "https://yasb.app/?f=..."}}, "version": "50P-1.1", "ruleset": "XWA"},
            "expected": GameFormat.XWA.value
        },
        {
            "case": "X2PO Legacy",
            "xws": {"vendor": {"yasb": {"builder": "YASB 2.0", "builder_url": "https://xwing-legacy.com/", "link": "https://xwing-legacy.com/?f=..."}}, "version": "2.0.1"},
            "expected": GameFormat.LEGACY_X2PO.value
        },
        {
            "case": "FFG (Raithos)",
            "xws": {"vendor": {"yasb": {"builder": "YASB 2.0", "builder_url": "https://raithos.github.io/", "link": "https://raithos.github.io/?f=Galactic%20Republic..."}}, "version": "2.0.0"},
            "expected": GameFormat.FFG.value
        },
        # LBN Cases provided by user
        {
            "case": "LBN Legacy (X2PO)",
            "xws": {"name":"New Squadron","faction":"rebelalliance","ruleset":"legacy","points":77,"version":"2.2.2","vendor":{"lbn":{"builder":"Launch Bay Next"}}},
            "expected": GameFormat.LEGACY_X2PO.value
        },
        {
            "case": "LBN XWA",
            "xws": {"name":"New Squadron","faction":"rebelalliance","ruleset":"xwa","points":22,"version":"2.2.3","vendor":{"lbn":{"builder":"Launch Bay Next"}}},
            "expected": GameFormat.XWA.value
        },
        {
            "case": "LBN AMG",
            "xws": {"name":"New Squadron","faction":"rebelalliance","ruleset":"amg","points":17,"version":"2.4.4","vendor":{"lbn":{"builder":"Launch Bay Next"}}},
            "expected": GameFormat.AMG.value
        },
        # Other cases
        {
            "case": "YASB Raithos (FFG)",
            "xws": {"vendor": {"yasb": {"link": "https://raithos.github.io/?"}}},
            "expected": GameFormat.FFG.value
        },
        {
            "case": "LBN Standard",
            "xws": {"vendor": {"lbn": {"builder": "Launch Bay Next"}}},
            "expected": GameFormat.XWA.value # Default assumption
        }
    ]
    
    for case in manual_cases:
        result = infer_format_from_xws(case["xws"])
        status = "PASS" if result == case["expected"] else f"FAIL (Got {result})"
        print(f"Manual Case '{case['case']}': {status}")

    print("\nReal Data Results:")
    for p in players[:5]:
        xws = p.get("xws", {})
        fmt = infer_format_from_xws(xws)
        print(f"Player {p['name']}: {fmt}")

test_inference()
