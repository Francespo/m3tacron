#!/usr/bin/env python3
"""
sync_game_data.py — Synchronize X-Wing game data across sources and rebuild manifests.

Sources supported:
1. Submodules: update `external_data` and child submodules (`xwing-data2`, `xwing-data2-legacy`)
2. J1mBob: fetch & merge card/asset fixes from `https://github.com/J1mBob/xwing-data2.git`
3. YASB (Raithos): parse instant points and loadouts from `https://github.com/raithos/xwing`
4. Legacy (Darker333 / SogeMoge): fetch & merge updates for `xwing-data2-legacy`
5. Manifest compiler: re-runs `frontend/scripts/generate-xwing-data.js`
"""

import argparse
import json
import os
import re
import subprocess
import sys
import urllib.request
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
EXTERNAL_DATA_DIR = ROOT_DIR / "external_data"
XWA_DIR = EXTERNAL_DATA_DIR / "xwing-data2"
LEGACY_DIR = EXTERNAL_DATA_DIR / "xwing-data2-legacy"
GENERATE_SCRIPT = ROOT_DIR / "frontend" / "scripts" / "generate-xwing-data.js"


def run_cmd(cmd: list[str], cwd: Path | None = None, check: bool = True) -> subprocess.CompletedProcess:
    """Run a shell command and print output."""
    print(f"--> Running: {' '.join(cmd)} (in {cwd or ROOT_DIR})")
    res = subprocess.run(cmd, cwd=cwd or ROOT_DIR, capture_output=True, text=True)
    if res.stdout:
        print(res.stdout.strip())
    if res.stderr and res.returncode != 0:
        print(f"Error: {res.stderr.strip()}", file=sys.stderr)
    if check and res.returncode != 0:
        raise RuntimeError(f"Command failed with returncode {res.returncode}: {' '.join(cmd)}")
    return res


def sync_submodules():
    """Update all git submodules recursively from their remote HEADs."""
    print("\n=== Sincronizzazione Submoduli Git ===")
    if not (ROOT_DIR / ".git").exists():
        print("Not a git repository, skipping submodule update.")
        return
    run_cmd(["git", "submodule", "update", "--init", "--recursive", "--remote"])


def sync_j1mbob():
    """Fetch and merge latest fixes from J1mBob into xwing-data2."""
    print("\n=== Sincronizzazione da J1mBob (xwing-data2) ===")
    if not XWA_DIR.exists():
        print(f"Directory {XWA_DIR} does not exist.")
        return

    # Check if upstream remote exists, otherwise add it
    remotes_res = run_cmd(["git", "remote"], cwd=XWA_DIR, check=False)
    remotes = remotes_res.stdout.split()
    if "j1mbob" not in remotes:
        run_cmd(["git", "remote", "add", "j1mbob", "https://github.com/J1mBob/xwing-data2.git"], cwd=XWA_DIR)

    run_cmd(["git", "fetch", "j1mbob"], cwd=XWA_DIR)
    # Merge master with default strategy
    merge_res = run_cmd(["git", "merge", "j1mbob/master", "--no-edit"], cwd=XWA_DIR, check=False)
    if merge_res.returncode != 0:
        print("Notice: merge conflicts or non-fast-forward merge. Resetting or keeping local changes.")


def sync_legacy_darker():
    """Fetch and merge latest points from Darker333 / SogeMoge into xwing-data2-legacy."""
    print("\n=== Sincronizzazione da Darker333 / SogeMoge (xwing-data2-legacy) ===")
    if not LEGACY_DIR.exists():
        print(f"Directory {LEGACY_DIR} does not exist.")
        return

    remotes_res = run_cmd(["git", "remote"], cwd=LEGACY_DIR, check=False)
    remotes = remotes_res.stdout.split()
    if "darker" not in remotes:
        run_cmd(["git", "remote", "add", "darker", "https://github.com/Darker333/xwing-data2-legacy.git"], cwd=LEGACY_DIR)

    run_cmd(["git", "fetch", "darker"], cwd=LEGACY_DIR)
    run_cmd(["git", "merge", "darker/master", "--no-edit"], cwd=LEGACY_DIR, check=False)


def normalize_xws(name: str) -> str:
    """Canonicalize a card/pilot name to XWS format."""
    return re.sub(r"[^a-z0-9]", "", name.lower())


def sync_yasb_fast_points():
    """Download YASB cards-common.coffee and patch points/loadouts in xwing-data2 JSONs."""
    print("\n=== Sincronizzazione Punti Lampo da YASB (Raithos) ===")
    url = "https://raw.githubusercontent.com/raithos/xwing/master/coffeescripts/content/cards-common.coffee"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "M3tacron-Data-Sync/1.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            content = resp.read().decode("utf-8")
    except Exception as e:
        print(f"Failed to fetch YASB cards-common.coffee: {e}")
        return

    # Parse pilot blocks with regex
    # Format in cards-common.coffee:
    # name: "Luke Skywalker"
    # ...
    # points: 14
    # loadout: 10
    pilot_points: dict[str, dict[str, int]] = {}
    
    # Split by pilot/upgrade entries
    blocks = re.split(r'\n\s*name:\s*"', content)
    for block in blocks[1:]:
        name_match = re.match(r'^([^"]+)"', block)
        if not name_match:
            continue
        name = name_match.group(1)
        pts_match = re.search(r'\bpoints:\s*(\d+)', block)
        loadout_match = re.search(r'\bloadout:\s*(\d+)', block)
        ship_match = re.search(r'\bship:\s*"([^"]+)"', block)

        if pts_match:
            pts = int(pts_match.group(1))
            loadout = int(loadout_match.group(1)) if loadout_match else 0
            xws_key = normalize_xws(name)
            # If ship is specified, also key by xws+ship
            pilot_points[xws_key] = {"points": pts, "loadout": loadout, "name": name}
            if ship_match:
                ship_xws = normalize_xws(ship_match.group(1))
                pilot_points[f"{xws_key}-{ship_xws}"] = {"points": pts, "loadout": loadout, "name": name}

    print(f"Found {len(pilot_points)} point definitions in YASB.")

    # Patch local JSON files in XWA_DIR
    pilots_dir = XWA_DIR / "data" / "pilots"
    if not pilots_dir.exists():
        print(f"Pilots directory {pilots_dir} not found.")
        return

    updated_count = 0
    for json_file in pilots_dir.rglob("*.json"):
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            pilots = data.get("pilots", [])
            file_changed = False
            for p in pilots:
                pxws = p.get("xws") or normalize_xws(p.get("name", ""))
                match = pilot_points.get(pxws) or pilot_points.get(normalize_xws(p.get("name", "")))
                if match:
                    new_cost = match["points"]
                    new_loadout = match["loadout"]
                    if p.get("cost") != new_cost or p.get("loadout") != new_loadout:
                        p["cost"] = new_cost
                        if "loadout" in p or new_loadout > 0:
                            p["loadout"] = new_loadout
                        file_changed = True
                        updated_count += 1

            if file_changed:
                with open(json_file, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                    f.write("\n")
        except Exception as err:
            print(f"Error updating {json_file}: {err}")

    print(f"Updated {updated_count} pilot points/loadouts in xwing-data2.")


def rebuild_manifests():
    """Run frontend/scripts/generate-xwing-data.js to compile static manifests."""
    print("\n=== Ricompilazione Manifest Frontend ===")
    if not GENERATE_SCRIPT.exists():
        print(f"Script {GENERATE_SCRIPT} does not exist.")
        return
    run_cmd(["node", str(GENERATE_SCRIPT)])


def main():
    parser = argparse.ArgumentParser(description="Synchronize X-Wing game data from upstream sources.")
    parser.add_argument("--sync-submodules", action="store_true", help="Update git submodules from remote HEADs")
    parser.add_argument("--sync-j1mbob", action="store_true", help="Fetch & merge card fixes from J1mBob/xwing-data2")
    parser.add_argument("--sync-yasb", action="store_true", help="Patch points and loadouts from YASB (Raithos)")
    parser.add_argument("--sync-legacy", action="store_true", help="Fetch & merge updates from Darker333/xwing-data2-legacy")
    parser.add_argument("--rebuild-manifests", action="store_true", help="Recompile static data JSON files")
    parser.add_argument("--all", action="store_true", help="Run all sync operations and rebuild manifests")

    args = parser.parse_args()

    # If no flags passed, default to submodules + manifests
    if not any(vars(args).values()):
        args.sync_submodules = True
        args.rebuild_manifests = True

    if args.all:
        sync_submodules()
        sync_j1mbob()
        sync_legacy_darker()
        sync_yasb_fast_points()
        rebuild_manifests()
        return

    if args.sync_submodules:
        sync_submodules()
    if args.sync_j1mbob:
        sync_j1mbob()
    if args.sync_legacy:
        sync_legacy_darker()
    if args.sync_yasb:
        sync_yasb_fast_points()
    if args.rebuild_manifests:
        rebuild_manifests()

    print("\nSincronizzazione completata!")


if __name__ == "__main__":
    main()
