"""Human-facing ship display labels.

The vendored XWA data gives both halves of a chassis split the same ``name``
field: ``bta-nr2-y-wing.json`` and ``bta-nr2-w-y-wing.json`` both carry
``"name": "BTA-NR2 Y-Wing"``, so a reader cannot tell the two chassis apart
even though they have different statlines and different chassis abilities.

This module is a **display-only** overlay keyed by the internal ship xws. It
never touches the ids, the XWS codes, the pilot ``-wartime`` suffixes or any
stored data: callers pass the vendored name in and get the label to render.

The map is deliberately tiny and obvious. Add one entry per split whose two
halves are otherwise indistinguishable by name in the sources.
"""

SHIP_DISPLAY_LABELS: dict[str, str] = {
    # Pre-split chassis; the Wartime Loadout stays a separate upgrade.
    "btanr2ywing": "Y-wing",
    # Integrated Wartime Loadout chassis (its pilots use the -wartime suffix).
    "btanr2wywing": "Y-wing (Wartime Loadout)",
}


def get_ship_display_name(ship_xws: str, fallback: str | None = None) -> str:
    """Return the human-facing label for a ship xws id.

    Ships that are not in the label map keep the vendored name (or, when no
    name is known, the xws id itself).
    """
    label = SHIP_DISPLAY_LABELS.get(ship_xws or "")
    if label:
        return label
    return fallback or ship_xws or "Unknown Ship"
