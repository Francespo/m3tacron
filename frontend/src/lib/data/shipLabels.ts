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
 */
export const SHIP_DISPLAY_LABELS: Record<string, string> = {
    btanr2ywing: "BTA-NR2 Y-Wing",
    btanr2wywing: "BTA-NR2 Y-Wing (Wartime Loadout)",
};

export function shipDisplayName(xws: string, fallback?: string | null): string {
    return SHIP_DISPLAY_LABELS[xws] ?? fallback ?? xws;
}
