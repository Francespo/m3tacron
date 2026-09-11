import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

POINTS_HISTORY_DIR = Path(__file__).resolve().parent

# Default fallback dates in case files are missing or unreadable
DEFAULT_LATEST_DATES: Dict[str, str] = {
    "legacy": "2026-03-31",
    "xwa": "2026-08-16",
    "amg": "2024-09-06",
    "ffg": "2020-11-24",
}


def _normalize_system(system_or_format: str) -> str:
    s = (system_or_format or "").strip().lower()
    if "legacy" in s or s in ("x2po", "legacy_x2po", "legacy_xlc", "legacy_pandorum"):
        return "legacy"
    if s in ("xwa", "amg_50p"):
        return "xwa"
    if s in ("amg", "2.5"):
        return "amg"
    if s in ("ffg", "2.0"):
        return "ffg"
    return s


def load_points_history(system_or_format: str) -> Optional[Dict[str, Any]]:
    system = _normalize_system(system_or_format)
    file_path = POINTS_HISTORY_DIR / f"{system}.json"
    if not file_path.exists():
        # Fallback check at repo root data/points_history
        alt_path = POINTS_HISTORY_DIR.parents[2] / "data" / "points_history" / f"{system}.json"
        if alt_path.exists():
            file_path = alt_path
        else:
            return None
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def get_latest_points_date(system_or_format: str) -> Optional[str]:
    system = _normalize_system(system_or_format)
    data = load_points_history(system)
    if data and "latest_date" in data:
        return data["latest_date"]
    return DEFAULT_LATEST_DATES.get(system)


def get_points_updates(system_or_format: str) -> List[Dict[str, Any]]:
    data = load_points_history(system_or_format)
    if data and "updates" in data:
        return data["updates"]
    return []
