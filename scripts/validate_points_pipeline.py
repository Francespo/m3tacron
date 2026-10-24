#!/usr/bin/env python3
"""Validate points history and generated manifests before a data PR.

Runs in CI and in the daily sync workflow. Uses only the stdlib so it can run
before dependencies are installed.
"""

from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FRONTEND_HISTORY = ROOT / "frontend" / "src" / "lib" / "data" / "points-history.json"
EXTERNAL_HISTORY_DIR = ROOT / "external_data" / "points_history"
MANIFESTS = {
    "xwa": ROOT / "frontend" / "static" / "data-xwa" / "xwing-data.json",
    "legacy": ROOT / "frontend" / "static" / "data-legacy" / "xwing-data.json",
}

errors: list[str] = []


def load_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        errors.append(f"missing file: {path.relative_to(ROOT)}")
    except json.JSONDecodeError as exc:
        errors.append(f"invalid JSON in {path.relative_to(ROOT)}: {exc}")
    return {}


def check_history(label: str, data: dict) -> None:
    latest = data.get("latest_date")
    updates = data.get("updates")

    if not isinstance(latest, str) or not latest:
        errors.append(f"{label}: latest_date is missing")
        return
    try:
        latest_day = date.fromisoformat(latest)
    except ValueError:
        errors.append(f"{label}: latest_date is not ISO: {latest!r}")
        return
    if latest_day > date.today():
        errors.append(f"{label}: latest_date is in the future: {latest}")

    if not isinstance(updates, list) or not updates:
        errors.append(f"{label}: updates must be a non-empty list")
        return

    seen: set[tuple[str, str]] = set()
    dates: list[str] = []
    for index, update in enumerate(updates):
        if not isinstance(update, dict):
            errors.append(f"{label}: updates[{index}] is not an object")
            continue
        update_date = update.get("date")
        version = update.get("version")
        if not isinstance(update_date, str) or not update_date:
            errors.append(f"{label}: updates[{index}].date is missing")
            continue
        try:
            parsed = date.fromisoformat(update_date)
        except ValueError:
            errors.append(f"{label}: updates[{index}].date is not ISO: {update_date!r}")
            continue
        if parsed > latest_day:
            errors.append(f"{label}: updates[{index}] is newer than latest_date")
        if parsed > date.today():
            errors.append(f"{label}: updates[{index}] is in the future")
        if not isinstance(version, str) or not version.strip():
            errors.append(f"{label}: updates[{index}].version is empty")
        key = (update_date, str(version))
        if key in seen:
            errors.append(f"{label}: duplicate entry {key}")
        seen.add(key)
        dates.append(update_date)

    if dates != sorted(dates, reverse=True):
        errors.append(f"{label}: updates are not sorted newest-first")
    if dates and dates[0] != latest:
        errors.append(f"{label}: latest_date {latest} != first update {dates[0]}")


def main() -> int:
    frontend = load_json(FRONTEND_HISTORY)
    if not frontend:
        print("\n".join(errors), file=sys.stderr)
        return 1

    for system in ("xwa", "legacy"):
        external = load_json(EXTERNAL_HISTORY_DIR / f"{system}.json")
        front = frontend.get(system)
        if not isinstance(front, dict):
            errors.append(f"frontend points-history: missing {system}")
            continue
        if not external:
            continue
        check_history(f"external/{system}", external)
        check_history(f"frontend/{system}", front)
        if external.get("latest_date") != front.get("latest_date"):
            errors.append(
                f"{system}: frontend latest_date {front.get('latest_date')} != "
                f"external latest_date {external.get('latest_date')}"
            )

    for system, path in MANIFESTS.items():
        manifest = load_json(path)
        if not manifest:
            continue
        for key in ("pilots", "ships", "upgrades"):
            value = manifest.get(key)
            if not isinstance(value, dict) or not value:
                errors.append(f"{path.relative_to(ROOT)}: {key} is empty or missing")

    if errors:
        print("Points pipeline validation failed:", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        return 1

    print(
        "Points pipeline OK: "
        + ", ".join(
            f"{system}={frontend[system]['latest_date']}"
            for system in ("xwa", "legacy")
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
