"""Human-readable chassis names for display.

The vendored game data gives the plain and the integrated-loadout BTA-NR2
Y-Wing the same ``name`` field ("BTA-NR2 Y-Wing"), so the split is illegible
in the UI even though the two chassis are distinct entries. This module is the
single backend source of truth for those display names.

DISPLAY ONLY. The labels never touch xws ids, pilot ids, the ``-wartime``
suffix, stored lists, the vendored data or any generated manifest; they are
applied where a name is rendered.

Naming evidence, checked against the real sources on 2026-09-19:

* YASB 2 (``https://yasb.app/javascripts/xwingcontent.min.js``, HTTP 200) —
  the ship table for the XWA set spells the pair
  ``"BTA-NR2 Y-wing"`` and ``"BTA-NR2-W Y-wing"``, the latter carrying the
  integrated statline:

      "BTA-NR2-W Y-wing":{name:"BTA-NR2-W Y-wing",icon:"btanr2ywing",
      factions:["Resistance"],attack:2,agility:1,hull:4,shields:5,
      chassis:"Devastating Barrage",...}

  Its variant pilots reference that chassis by name
  (``{name:"Zorii Bliss (Wartime)",...,xwsaddon:"wartime",ship:"BTA-NR2-W Y-wing"}``).
* XWA points document 50P2.1 (2026-08-17) prints the same two rows as
  ``BTA-NR2 Y-Wing`` and ``BTA-NR2-W Y-Wing`` — same ``-W`` marker, capital
  ``Wing``.
* The vendored ``xwing-data2`` files keep ``"name": "BTA-NR2 Y-Wing"`` in
  both, which is why the split is illegible without this layer.

The variant label follows YASB 2, the source named in the requirement, down to
its casing (``BTA-NR2-W Y-wing``). The plain chassis keeps the vendored and
XWA-document spelling (``BTA-NR2 Y-Wing``), so the pair differs in the case of
``wing``. If the product owner prefers one spelling for both, that is a
one-line change here and in the frontend mirror.
"""

SHIP_DISPLAY_LABELS: dict[str, str] = {
    "btanr2ywing": "BTA-NR2 Y-Wing",
    "btanr2wywing": "BTA-NR2-W Y-wing",
}


def ship_display_name(ship_xws: str, fallback: str = "") -> str:
    """Return the display name for ``ship_xws``, or ``fallback`` when unlabelled."""
    if not isinstance(ship_xws, str):
        return fallback or ""
    return SHIP_DISPLAY_LABELS.get(ship_xws) or fallback or ship_xws
