/**
 * URL <-> store synchronization choke point.
 *
 * The store is pure (no $app/navigation, no setTimeout). Routes mutate the
 * store, then ask this module to push the new state to the URL. The module
 * owns the debounce timer, the route-id derivation, and the echo-loop guard.
 *
 * Callers:
 *   - Immediate sync (pagination, tab, sort, checkbox):
 *       scheduleSync(0, localParams)
 *   - Debounced sync (text inputs that set filters.searchName, then call):
 *       scheduleSync(250)
 */

import { goto } from "$app/navigation";
import { page } from "$app/state";
import { filters } from "$lib/stores/filters.svelte";
import type { RouteId } from "$lib/stores/filters.svelte";

// ---------------------------------------------------------------------------
// Route id derivation
// ---------------------------------------------------------------------------

/**
 * Map a URL pathname to the `RouteId` consumed by `filters.toSearchParams`.
 * Matches on the first path segment. Unknown routes fall back to `'cards'`
 * so the URL is always at least well-formed; `toSearchParams` will return an
 * empty param set for any non-whitelisted key.
 */
export function deriveRouteIdFromPathname(pathname: string): RouteId {
    // Normalize: strip trailing slash, then read the first segment.
    const normalized = pathname.replace(/\/+$/, "");
    const first = normalized.split("/")[1] ?? "";

    switch (first) {
        case "cards":
            return "cards";
        case "lists":
            return "lists";
        case "ships":
        case "ship":
            return "ships";
        case "squadrons":
        case "squadron":
            return "squadrons";
        case "tournaments":
        case "tournament":
            return "tournaments";
        default:
            return "cards";
    }
}

// ---------------------------------------------------------------------------
// Debounce timer (module-level rune state)
// ---------------------------------------------------------------------------

let pendingTimer: ReturnType<typeof setTimeout> | null = null;

/**
 * Schedule a URL sync. Replaces any pending sync (debounce, not throttle).
 *
 * @param delayMs  How long to wait before firing. `0` fires on the next
 *                 microtask via `setTimeout(0)`. Text inputs typically use
 *                 `250`.
 * @param overlay  Optional route-local params to merge on top of the store's
 *                 output (e.g. `page`, `size`, `tab`, `min_games`). Keys
 *                 overwrite (set) — each local key appears once in the URL.
 */
export function scheduleSync(delayMs: number = 0, overlay?: URLSearchParams): void {
    if (pendingTimer !== null) {
        clearTimeout(pendingTimer);
        pendingTimer = null;
    }

    pendingTimer = setTimeout(() => {
        pendingTimer = null;

        const routeId = deriveRouteIdFromPathname(page.url.pathname);
        const params = filters.toSearchParams(routeId);

        if (overlay) {
            for (const [k, v] of overlay) {
                params.set(k, v);
            }
        }

        const next = `?${params.toString()}`;
        const current = page.url.search;

        // Echo-loop guard: if the URL already matches what we'd write, skip
        // the goto. Without this, every store mutation would round-trip
        // through goto() forever.
        if (next === current) return;

        const target = page.url.pathname + next;
        goto(target, {
            replaceState: true,
            keepFocus: true,
            noScroll: true,
        });
    }, delayMs);
}

/**
 * Cancel any pending sync. Called from the layout's `onNavigate` so a
 * pending 250ms timer from the old route never fires goto() against the
 * new route's pathname.
 */
export function clearPendingSync(): void {
    if (pendingTimer !== null) {
        clearTimeout(pendingTimer);
        pendingTimer = null;
    }
}
