/**
 * Human-facing ship display labels.
 *
 * The vendored XWA data gives both halves of a chassis split the same `name`
 * field (both BTA-NR2 Y-Wing files say "BTA-NR2 Y-Wing"), so a reader cannot
 * tell the two chassis apart. This is a display-only overlay keyed by the
 * internal ship xws.
 *
 * It never changes the ids, the XWS codes, the pilot `-wartime` suffixes or
 * anything stored: the backend applies the same map in
 * `backend/utils/xwing_data/labels.py`.
 */
export const SHIP_DISPLAY_LABELS: Record<string, string> = {
    // Pre-split chassis; the Wartime Loadout stays a separate upgrade.
    btanr2ywing: 'Y-wing',
    // Integrated Wartime Loadout chassis (its pilots use the -wartime suffix).
    btanr2wywing: 'Y-wing (Wartime Loadout)',
};

/**
 * Return the label to render for a ship. Ships that are not in the map keep
 * the name passed in (typically the vendored name from the manifest).
 */
export function getShipDisplayName(
    shipXws: string,
    fallbackName?: string | null,
): string {
    if (shipXws && SHIP_DISPLAY_LABELS[shipXws]) {
        return SHIP_DISPLAY_LABELS[shipXws];
    }
    return fallbackName || shipXws || 'Unknown Ship';
}
