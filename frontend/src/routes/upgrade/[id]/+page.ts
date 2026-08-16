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
 * Limitations surfaced to the page (and to the user):
 *  - No endpoint returns lists/squadrons filtered to a single upgrade.
 *    The `filter_upgrade_id` slot in `aggregate_card_stats` is defined
 *    but not wired into the SQL WHERE clause (see
 *    `backend/analytics/core.py` lines 52-54), so we cannot use it.
 *  - The static upgrade metadata (name, image, slot, description text,
 *    cost) is loaded client-side from the `xwingData` reactive manifest
 *    store, which is identical to what `UpgradeCard.svelte` uses.
 *  - We over-fetch the cards/upgrades list with a large page size to
 *    find this one row. Acceptable for a detail page; flagged for a
 *    follow-up that adds a dedicated endpoint.
 */
export const load: PageLoad = async ({ fetch, params, url }) => {
    url.search; // Force reactivity on URL params
    const upgradeXws = params.id;
    const ds = url.searchParams.get('data_source') === 'legacy' ? 'legacy' : 'xwa';

    // Pull the full upgrade catalog page; the per-xws row contains
    // (games_count, wins, list_count, different_lists_count). The cards
    // endpoint already excludes invalid formats via the analytics layer,
    // so the row here reflects the current data_source.
    const statsRes = await fetch(
        `${API_BASE}/cards/upgrades?data_source=${ds}&size=2000&page=0`,
    );

    let stats: any = null;
    if (statsRes.ok) {
        try {
            const data = await statsRes.json();
            const items = Array.isArray(data?.items) ? data.items : [];
            stats = items.find((it: any) => it?.xws === upgradeXws) ?? null;
        } catch {
            stats = null;
        }
    }

    return {
        upgradeXws,
        ds,
        stats,
    };
};
