import type { PageLoad } from './$types';
import { API_BASE } from '$lib/api';

/**
 * Upgrade detail loader.
 *
 * Phase G scope: implement the upgrade detail page using ONLY existing
 * backend endpoints. The backend has no dedicated upgrade-detail endpoint
 * (no /api/upgrade/{xws} or /api/upgrades/{xws}); the only upgrade-aware
 * endpoint is the paginated /api/cards/upgrades list. We use that to
 * extract this upgrade's aggregate stats row.
 *
 * The fetch runs against the `upgrade_id` query param (size=1) so we stop
 * over-fetching the whole catalog. If the backend change isn't live yet
 * (no matching row comes back), we fall back to the old size=2000 catalog
 * scan so the page keeps working against older backends.
 *
 * Limitations surfaced to the page (and to the user):
 *  - No endpoint returns lists/squadrons filtered to a single upgrade.
 *  - The static upgrade metadata (name, image, slot, description text,
 *    cost) is loaded client-side from the `xwingData` reactive manifest
 *    store, which is identical to what `UpgradeCard.svelte` uses.
 */
export const load: PageLoad = async ({ fetch, params, url }) => {
    url.search; // Force reactivity on URL params
    const upgradeXws = params.id;
    const ds = url.searchParams.get('data_source') === 'legacy' ? 'legacy' : 'xwa';

    // Return a promise so SvelteKit navigates immediately and streams data in.
    // This prevents navigation from blocking on slow API responses.
    const statsPromise = fetch(
        `${API_BASE}/cards/upgrades?data_source=${ds}&upgrade_id=${upgradeXws}&size=1&page=0`,
    )
        .then(async (statsRes) => {
            if (!statsRes.ok) return null;
            const data = await statsRes.json().catch(() => null);
            if (!data) return null;
            const items = Array.isArray(data?.items) ? data.items : [];
            const direct = items.find((it: any) => it?.xws === upgradeXws) ?? null;
            if (direct) return direct;

            // Backend doesn't support `upgrade_id` yet — fall back to the
            // previous full-catalog scan (old behavior, size=2000).
            const fallbackRes = await fetch(
                `${API_BASE}/cards/upgrades?data_source=${ds}&size=2000&page=0`,
            );
            if (!fallbackRes.ok) return null;
            const fallbackData = await fallbackRes.json().catch(() => null);
            const fallbackItems = Array.isArray(fallbackData?.items)
                ? fallbackData.items
                : [];
            return fallbackItems.find((it: any) => it?.xws === upgradeXws) ?? null;
        })
        .catch(() => null);

    return {
        upgradeXws,
        ds,
        statsPromise,
    };
};
