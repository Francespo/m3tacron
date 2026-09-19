/**
 * Human-readable chassis names for display.
 *
 * The vendored game data gives the plain and the integrated-loadout BTA-NR2
 * Y-Wing the same `name` field ("BTA-NR2 Y-Wing"), so the split is illegible in
 * the UI even though the two chassis are distinct entries. This mirrors
 * `backend/utils/xwing_data/labels.py`, the backend source of truth.
 *
 * DISPLAY ONLY. These labels never touch xws ids, pilot ids, the `-wartime`
 * suffix, stored lists, the vendored data or the generated manifest under
 * `static/data-*`; they are applied where a name is rendered.
 *
 * Naming evidence (2026-09-19): YASB 2's XWA ship table spells the split pair
 * `BTA-NR2 Y-wing` / `BTA-NR2-W Y-wing` (the variant entry carries
 * `icon:"btanr2ywing"`, `shields:5`, `chassis:"Devastating Barrage"`), and
 * the XWA points document 50P2.1 prints `BTA-NR2-W Y-Wing`. The variant label
 * follows YASB 2 including its casing; the plain chassis keeps the vendored
 * spelling. See `backend/utils/xwing_data/labels.py` for the full quotes.
 */
export const SHIP_DISPLAY_LABELS: Record<string, string> = {
    btanr2ywing: "BTA-NR2 Y-Wing",
    btanr2wywing: "BTA-NR2-W Y-wing",
};

export function shipDisplayName(xws: string, fallback?: string | null): string {
    return SHIP_DISPLAY_LABELS[xws] ?? fallback ?? xws;
}
