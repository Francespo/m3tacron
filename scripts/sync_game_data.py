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
import subprocess
import sys
import urllib.request
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
EXTERNAL_DATA_DIR = ROOT_DIR / "external_data"
XWA_DIR = EXTERNAL_DATA_DIR / "xwing-data2"
LEGACY_DIR = EXTERNAL_DATA_DIR / "xwing-data2-legacy"
GENERATE_SCRIPT = ROOT_DIR / "frontend" / "scripts" / "generate-xwing-data.js"
# Shared YASB parser/matcher, owned by the xwing-data2 submodule. Name-only
# matching silently skipped variants such as Anakin Skywalker (Delta-7b).
YASB_SCRIPTS_DIR = XWA_DIR / "scripts"
if YASB_SCRIPTS_DIR.exists():
    sys.path.insert(0, str(YASB_SCRIPTS_DIR))


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
    """Advance external_data to the tip of xwing-unified-data, then honour the
    nested submodule pins from that commit.

    Do *not* use ``--recursive --remote`` here: that would also fast-forward
    xwing-data2 / xwing-data2-legacy to their own remote HEADs, bypassing the
    SHA pins curated in xwing-unified-data and leaving the generated manifests
    inconsistent with the recorded gitlinks.
    """
    print("\n=== Sincronizzazione Submoduli Git ===")
    if not (ROOT_DIR / ".git").exists():
        print("Not a git repository, skipping submodule update.")
        return
    run_cmd(["git", "submodule", "update", "--init", "--remote", "--", "external_data"])
    run_cmd(["git", "-C", "external_data", "submodule", "update", "--init", "--recursive"])


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


def sync_yasb_fast_points():
    """Apply the current YASB snapshot to every pilot and upgrade.

    Uses the shared matcher in the xwing-data2 submodule (name + file-level
    ship/faction + xwsaddon/variant suffix) instead of matching by name alone,
    which silently skipped Delta-7B variants and could overwrite a same-name
    pilot on a different chassis.
    """
    print("\n=== Sincronizzazione Punti Lampo da YASB (Raithos) ===")
    try:
        from yasb_cards import (
            build_pilot_index,
            build_upgrade_index,
            lookup_pilot,
            lookup_upgrade,
            parse_yasb,
        )
    except ImportError:
        print(
            "Cannot import scripts/yasb_cards.py from the xwing-data2 submodule; "
            "run `git submodule update --init --recursive` first."
        )
        return

    url = "https://raw.githubusercontent.com/raithos/xwing/master/coffeescripts/content/cards-common.coffee"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "M3tacron-Data-Sync/1.0"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            content = resp.read().decode("utf-8")
    except Exception as e:
        print(f"Failed to fetch YASB cards-common.coffee: {e}")
        return

    entries = parse_yasb(content)
    pilot_index = build_pilot_index(entries)
    upgrade_index = build_upgrade_index(entries)
    print(f"Found {len(entries)} card definitions in YASB.")

    pilots_dir = XWA_DIR / "data" / "pilots"
    upgrades_dir = XWA_DIR / "data" / "upgrades"
    if not pilots_dir.exists():
        print(f"Pilots directory {pilots_dir} not found.")
        return

    updated_count = 0
    unmatched_pilots = 0
    for json_file in pilots_dir.rglob("*.json"):
        try:
            data = json.loads(json_file.read_text(encoding="utf-8"))
            ship = data.get("name") or data.get("xws") or ""
            faction = data.get("faction") or ""
            file_changed = False
            for pilot in data.get("pilots", []):
                match = lookup_pilot(pilot_index, pilot, ship, faction)
                if not match:
                    unmatched_pilots += 1
                    continue
                if pilot.get("cost") != match["points"]:
                    pilot["cost"] = match["points"]
                    file_changed = True
                    updated_count += 1
                if match["loadout"] is not None and pilot.get("loadout") != match["loadout"]:
                    pilot["loadout"] = match["loadout"]
                    file_changed = True
                    updated_count += 1
            if file_changed:
                written = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
                json_file.write_text(written, encoding="utf-8")
        except Exception as err:
            print(f"Error updating {json_file}: {err}")

    unmatched_upgrades = 0
    if upgrades_dir.exists():
        for json_file in upgrades_dir.glob("*.json"):
            try:
                data = json.loads(json_file.read_text(encoding="utf-8"))
                if isinstance(data, list):
                    items = data
                elif isinstance(data, dict) and isinstance(data.get("upgrades"), list):
                    items = data["upgrades"]
                else:
                    continue
                file_changed = False
                for upgrade in items:
                    match = lookup_upgrade(upgrade_index, upgrade)
                    if not match:
                        unmatched_upgrades += 1
                        continue
                    cost = upgrade.get("cost")
                    new_cost = match["points"]
                    if isinstance(cost, dict):
                        if cost.get("value") != new_cost:
                            cost["value"] = new_cost
                            file_changed = True
                            updated_count += 1
                    elif isinstance(cost, (int, float)):
                        if cost != new_cost:
                            upgrade["cost"] = new_cost
                            file_changed = True
                            updated_count += 1
                    elif cost is None:
                        upgrade["cost"] = {"value": new_cost}
                        file_changed = True
                        updated_count += 1
                if file_changed:
                    written = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
                    json_file.write_text(written, encoding="utf-8")
            except Exception as err:
                print(f"Error updating {json_file}: {err}")

    print(
        f"Updated {updated_count} pilot/upgrade fields in xwing-data2 "
        f"({unmatched_pilots} pilots and {unmatched_upgrades} upgrades had no "
        "confident match and were left unchanged)."
    )


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
