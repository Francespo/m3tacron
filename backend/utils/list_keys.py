import json
from typing import Any


def coerce_list_json(raw: Any) -> dict:
    """Return a dict for a list payload, parsing JSON strings when needed."""
    if isinstance(raw, dict):
        return raw

    if isinstance(raw, str):
        try:
            parsed = json.loads(raw)
        except Exception:
            return {}
        if isinstance(parsed, dict):
            return parsed

    return {}


def iter_upgrade_ids(raw_upgrades: Any) -> list[str]:
    """Extract upgrade xws ids from an XWS `upgrades` field.

    Handles the dict (slot -> ids), flat list, and flat list-of-dicts shapes
    that appear in stored list_json payloads.
    """
    ids: list[str] = []

    def _push(item: Any) -> None:
        if isinstance(item, dict):
            item = item.get("xws") or item.get("id") or item.get("name")
        if item:
            ids.append(str(item))

    if isinstance(raw_upgrades, dict):
        for items in raw_upgrades.values():
            if isinstance(items, list):
                for item in items:
                    _push(item)
            else:
                _push(items)
    elif isinstance(raw_upgrades, list):
        for item in raw_upgrades:
            _push(item)

    return ids


def canonical_pilot_reference(pilot: dict) -> tuple[str, list[str], list[str]]:
    """Return ``(pilot_xws, upgrade_ids, extra_ship_ids)`` for one pilot.

    Resolves deprecated pre-split references at read time via
    ``xwing_data.aliases``; absorbed trigger upgrades are dropped so the
    pre-split and post-split encodings of one squad collapse to one identity.
    """
    from .xwing_data.aliases import resolve_pilot_reference

    pid = pilot.get("id") or pilot.get("name") or ""
    upgrade_ids = sorted(iter_upgrade_ids(pilot.get("upgrades", {})))

    resolution = resolve_pilot_reference(pid, upgrade_ids)
    canonical_upgrades = [
        u for u in upgrade_ids if u not in resolution.absorbed_upgrades
    ]
    return resolution.pilot_xws or pid, canonical_upgrades, []


def get_list_key(xws: Any) -> str:
    """
    Generate a unique, canonical signature for a list based on pilots and upgrades.
    """
    xws = coerce_list_json(xws)
    if not xws:
        return ""

    pilots = xws.get("pilots", [])
    if not pilots:
        return ""

    temp_pilots = []
    for p in pilots:
        pilot_xws, upgrade_ids, _ = canonical_pilot_reference(p)
        temp_pilots.append({
            "xws": pilot_xws,
            "upgrades": [{"xws": u} for u in upgrade_ids],
        })

    # Sort by pilot xws then upgrades
    temp_pilots.sort(key=lambda x: (x["xws"], str(x["upgrades"])))

    return json.dumps(temp_pilots, sort_keys=True)


def get_ship_list(xws: dict) -> str:
    """
    Extract sorted ship XWS list from list_json for squadron grouping.
    Returns comma-joined string like "btla4ywing,t65xwing,t65xwing".

    Deprecated pre-split references resolve to the variant they represent, and
    the ship is derived from the pilot when list_json has no `ship` field.
    """
    if not xws or not isinstance(xws, dict):
        return ""

    from .xwing_data.aliases import resolve_pilot_reference, resolve_ship_id

    pilots = xws.get("pilots", [])
    ships = []
    for p in pilots:
        pid = p.get("id") or p.get("name") or ""
        upgrade_ids = iter_upgrade_ids(p.get("upgrades", {}))
        ship = p.get("ship") or ""
        if ship:
            ship = resolve_ship_id(ship, upgrade_ids)
        else:
            ship = resolve_pilot_reference(pid, upgrade_ids).ship_xws
        if ship:
            ships.append(ship)

    ships.sort()
    return ",".join(ships)
