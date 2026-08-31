import type { PageLoad } from './$types';
import { API_BASE } from '$lib/api';
import { browser } from '$app/environment';
import { filters } from '$lib/stores/filters.svelte';

// Client-side cache for the ships stats lookup.
// Page changes are client-side sliced (mergedShips.slice), so changing page
// must NOT trigger a new network request. `load` re-runs on every URL change
// (including ?page=), so we cache the stats promise keyed by the filter set
// (excluding page/size) and reuse it until filters actually change.
const shipsCache = new Map<string, Promise<any[]>>();

function shipsFilterKey(url: URL): string {
    const p = new URLSearchParams(url.searchParams);
    p.delete('page');
    p.delete('size');
    // Stable sort for cache key
    const entries = [...p.entries()].sort((a, b) => a[0].localeCompare(b[0]) || a[1].localeCompare(b[1]));
    return entries.map(([k, v]) => `${k}=${v}`).join('&');
}

export const load: PageLoad = async ({ fetch, url }) => {
    url.search; // Force reactivity when any query param changes
    const ds = url.searchParams.get('data_source') || (browser ? filters.dataSource : 'xwa');

    const sort_metric = url.searchParams.get('sort_metric') || 'Lists';
    const sort_direction = url.searchParams.get('sort_direction') || 'desc';

    const filterKey = shipsFilterKey(url);

    let apiShipsPromise = shipsCache.get(filterKey);
    if (!apiShipsPromise) {
        const mergeApiUrl = new URL(`${API_BASE}/ships`, url.origin);
        for (const [key, value] of url.searchParams.entries()) {
            if (key === 'page' || key === 'size') continue;
            mergeApiUrl.searchParams.append(key, value);
        }
        if (!mergeApiUrl.searchParams.has('data_source')) {
            mergeApiUrl.searchParams.set('data_source', ds);
        }
        if (!mergeApiUrl.searchParams.has('formats')) {
            const defFormats = ds === 'legacy' ? ['legacy_x2po'] : ['xwa'];
            for (const f of defFormats) {
                mergeApiUrl.searchParams.append('formats', f);
            }
        }
        mergeApiUrl.searchParams.set('page', '0');
        mergeApiUrl.searchParams.set('size', '200');
        const target = mergeApiUrl.toString();
        apiShipsPromise = fetch(target)
            .then(async (response) => {
                if (!response.ok) return [];
                const data = await response.json();
                return data?.items ?? [];
            })
            .catch((e) => {
                console.error('Fetch failed:', e);
                // Don't cache failures — allow retry
                shipsCache.delete(filterKey);
                return [];
            });
        shipsCache.set(filterKey, apiShipsPromise);
        // Bound cache
        if (shipsCache.size > 50) {
            const oldest = shipsCache.keys().next().value;
            if (oldest) shipsCache.delete(oldest);
        }
    }

    return { apiShipsPromise, sort_metric, sort_direction };
};
