/**
 * Human-facing ship labels for XWA upgrade-to-chassis splits.
 *
 * The vendored data gives the two BTA-NR2 Y-Wing chassis the same `name`
 * ("BTA-NR2 Y-Wing"), which makes the split illegible in the UI. The label
 * difference is applied here — the layer that derives the human name — never
 * to the xws ids, which stored squads and XWS codes key off.
 *
 * `shipLabels.json` mirrors `SHIP_SPLIT_ALIASES` in
 * `backend/utils/xwing_data/aliases.py`; the manifest generator reads the same
 * JSON so prebuilt manifests carry the labels too. Keep both in sync when a
 * new split is added.
 */
import shipLabels from "./shipLabels.json";

export const SHIP_DISPLAY_LABELS: Record<string, string> = shipLabels;

/** Resolve the display name for a ship xws, falling back to the given name. */
export function getShipDisplayName(xws: string, fallback?: string | null): string {
    if (xws && SHIP_DISPLAY_LABELS[xws]) return SHIP_DISPLAY_LABELS[xws];
    return fallback || xws;
}
