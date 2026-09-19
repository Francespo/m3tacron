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
    """Extract upgrade xws ids from an XWS ``upgrades`` field.

    Handles all shapes that appear in stored ``list_json`` payloads: a dict of
    slot -> ids, a flat list of ids, and a flat list of ``{"xws": id}`` entries.
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


def _pilot_reference(pilot: dict) -> tuple[str, list[str]]:
    """Return ``(pilot_xws, upgrade_ids)`` for one pilot entry."""
    pid = pilot.get("id") or pilot.get("name") or ""
    return pid, iter_upgrade_ids(pilot.get("upgrades", {}))


def get_list_key(xws: Any) -> str:
    """
    Generate a unique, canonical signature for a list based on pilots and upgrades.

    Pre-split references are resolved at read time (see ``xwing_data.aliases``)
    so the pre-split and post-split encodings of one squad produce the same
    signature; an absorbed upgrade is dropped because it is baked into the
    resolved chassis rather than being a separate card.
    """
    xws = coerce_list_json(xws)
    if not xws:
        return ""

    pilots = xws.get("pilots", [])
    if not pilots:
        return ""

    from .xwing_data.aliases import resolve_pilot_reference

    temp_pilots = []
    for p in pilots:
        pid, upgrade_ids = _pilot_reference(p)
        resolution = resolve_pilot_reference(pid, upgrade_ids)
        canonical_upgrades = sorted(
            u for u in upgrade_ids if u not in resolution.absorbed_upgrades
        )
        temp_pilots.append({
            "xws": resolution.pilot_xws or pid,
            "upgrades": [{"xws": u} for u in canonical_upgrades]
        })

    # Sort by pilot xws then upgrades
    temp_pilots.sort(key=lambda x: (x["xws"], str(x["upgrades"])))

    return json.dumps(temp_pilots, sort_keys=True)


def get_ship_list(xws: dict) -> str:
    """
    Extract sorted ship XWS list from list_json for squadron grouping.
    Returns comma-joined string like "btla4ywing,t65xwing,t65xwing".

    Pre-split references resolve at read time to the chassis they are actually
    played on, and the chassis is derived from the pilot when list_json has no
    ``ship`` field.
    """
    if not xws or not isinstance(xws, dict):
        return ""

    from .xwing_data.aliases import resolve_pilot_reference, resolve_ship_id

    pilots = xws.get("pilots", [])
    ships = []
    for p in pilots:
        pid, upgrade_ids = _pilot_reference(p)
        ship = p.get("ship") or ""
        if ship:
            ship = resolve_ship_id(ship, upgrade_ids)
        else:
            ship = resolve_pilot_reference(pid, upgrade_ids).ship_xws
        if ship:
            ships.append(ship)

    ships.sort()
    return ",".join(ships)
