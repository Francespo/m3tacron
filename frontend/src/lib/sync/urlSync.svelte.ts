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
 * `true` while a URL sync scheduled by `scheduleSync` is in flight
 * (between the call to `scheduleSync` and the resulting URL change
 * landing in `page.url`). Used by the store's `applyFromSearchParams`
 * to distinguish a stale-URL race condition (skip the write — the
 * store is the source of truth) from a real navigation (hydrate the
 * store from the URL).
 */
let pendingSync = false;

/**
 * `true` until the store has been hydrated from the URL at least
 * once. Used to suppress the `pendingSync` flag for the very first
 * `scheduleSync` call after page load, so the layout's `$effect`
 * gets a chance to run its hydration before the page's `$effect`
 * schedules a URL write that would clobber the URL before the store
 * has read it.
 */
let hasHydrated = false;

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
    // Only arm the race-condition guard for syncs that happen AFTER
    // the store has been hydrated from the URL. The very first
    // `scheduleSync` call after page load races with the layout's
    // hydration `$effect` — if we set `pendingSync = true` here,
    // the layout would see the flag and skip the hydration, leaving
    // the store at its default value and then having this very
    // sync rewrite the URL to match the (empty) default. So: skip
    // the flag for the first call, and let the hydration run.
    pendingSync = hasHydrated;

    pendingTimer = setTimeout(() => {
        pendingTimer = null;

        const routeId = deriveRouteIdFromPathname(page.url.pathname);
        const params = filters.toSearchParams(routeId);

        if (overlay) {
            // The overlay is a snapshot of the route-local URLSearchParams
            // at the time the caller scheduled the sync. It already contains
            // every field produced by `filters.toSearchParams()` for the
            // current route (including multi-value fields like `formats`).
            //
            // Route-local fields (page, size, tab, min_games, etc.) are
            // single-value and use `set()` — that overwrites cleanly.
            //
            // Multi-value fields (formats, factions, ships, sources,
            // continent, country, city, base_sizes) must NOT be re-applied
            // with `set()`: the fresh `params` already has the full list
            // from `toSearchParams()`, and `set()` would replace the whole
            // list with just the LAST entry from the overlay snapshot,
            // silently dropping the user's multi-select.
            const MULTI_VALUE_KEYS = new Set([
                'formats',
                'factions',
                'ships',
                'sources',
                'continent',
                'country',
                'city',
                'base_sizes',
            ]);
            for (const [k, v] of overlay) {
                if (MULTI_VALUE_KEYS.has(k)) continue;
                params.set(k, v);
            }
        }

        const next = `?${params.toString()}`;
        const current = page.url.search;

        // Echo-loop guard: if the URL already matches what we'd write, skip
        // the goto. Without this, every store mutation would round-trip
        // through goto() forever.
        if (next === current) {
            pendingSync = false;
            return;
        }

        const target = page.url.pathname + next;
        goto(target, {
            replaceState: true,
            keepFocus: true,
            noScroll: true,
        });
        // `pendingSync` stays true until the URL actually changes.
        // `applyFromSearchParams` clears it once it sees a matching URL.
    }, delayMs);
}

/**
 * Returns `true` while a URL sync is in flight (the store has mutated
 * but the URL has not yet been updated). The store uses this to skip
 * a stale-URL re-hydration that would otherwise clobber the user's
 * pending mutation.
 */
export function isPendingSync(): boolean {
    return pendingSync;
}

/**
 * Mark the pending sync as resolved. Called by
 * `filters.applyFromSearchParams` once it has observed a URL that
 * matches the store's current output, so the next URL change (a real
 * navigation) is no longer treated as a race-condition echo.
 */
export function resolvePendingSync(): void {
    pendingSync = false;
    hasHydrated = true;
}

/**
 * Mark the store as hydrated from the URL. Called on the first
 * `applyFromSearchParams` after page load, so subsequent
 * `scheduleSync` calls (e.g. a user clicking a checkbox) will arm
 * the race-condition guard. Does NOT clear `pendingSync` — use
 * `resolvePendingSync` for that.
 */
export function markHydrated(): void {
    hasHydrated = true;
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
    pendingSync = false;
}
