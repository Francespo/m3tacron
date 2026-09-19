/**
 * Card-art fallbacks for split chassis whose own pilot art does not exist.
 *
 * Mirrors `backend/utils/xwing_data/assets.py`, the backend source of truth
 * (see there for the full HTTP inventory). The vendored data points the
 * integrated-loadout BTA-NR2 Y-Wing pilots at `pilots/<pilot>-wartime.png`,
 * and every one of those ten URLs returns HTTP 404 — the artwork host never
 * published variant cards. The UI therefore borrows the card of the
 * same-named pilot on the donor (plain) chassis, whose URL the vendored data
 * already carries.
 *
 * DISPLAY ONLY, resolved at lookup time: no URL is invented, and neither the
 * vendored data nor the generated manifest under `static/data-*` is touched.
 */
export interface CardArtFallback {
    /** Chassis whose same-named pilots supply the card art. */
    donorId: string;
    /** Why the variant has no art of its own (HTTP evidence). */
    reason: string;
    verifiedOn: string;
}

export const CARD_ART_FALLBACKS: Record<string, CardArtFallback> = {
    btanr2wywing: {
        donorId: "btanr2ywing",
        reason:
            "upstream ships no W-variant card PNG: all 10 pilots/<pilot>-wartime.png return HTTP 404",
        verifiedOn: "2026-09-19",
    },
};

export function cardArtFallback(xws: string): CardArtFallback | null {
    return CARD_ART_FALLBACKS[xws] ?? null;
}

export function cardArtDonorIds(): Set<string> {
    return new Set(Object.values(CARD_ART_FALLBACKS).map((f) => f.donorId));
}
