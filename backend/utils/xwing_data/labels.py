"""Human-readable chassis names for display.

The vendored game data gives the plain and the integrated-loadout BTA-NR2
Y-Wing the same ``name`` field ("BTA-NR2 Y-Wing"), so the split is illegible
in the UI even though the two chassis are distinct entries. This module is the
single backend source of truth for those display names.

DISPLAY ONLY. The labels never touch xws ids, pilot ids, the ``-wartime``
suffix, stored lists, the vendored data or any generated manifest; they are
applied where a name is rendered.

Naming evidence (see the pull request body for the full audit): no official
XWA display name exists for the integrated-loadout variant. The vendored pair
``delta-7-aethersprite.json`` / ``delta-7b-aethersprite.json`` distinguishes a
variant with a letter inside the name (``Delta-7B Aethersprite``), but the
Y-Wing pair keeps the identical ``name`` in both files, and the AMG points
workbooks carry a single ``BTA-NR2 Y-wing`` ship row. ``(Wartime Loadout)`` is
therefore an explicit product assumption, not an upstream convention.
"""

SHIP_DISPLAY_LABELS: dict[str, str] = {
    "btanr2ywing": "BTA-NR2 Y-Wing",
    "btanr2wywing": "BTA-NR2 Y-Wing (Wartime Loadout)",
}


def ship_display_name(ship_xws: str, fallback: str = "") -> str:
    """Return the display name for ``ship_xws``, or ``fallback`` when unlabelled."""
    if not isinstance(ship_xws, str):
        return fallback or ""
    return SHIP_DISPLAY_LABELS.get(ship_xws) or fallback or ship_xws
