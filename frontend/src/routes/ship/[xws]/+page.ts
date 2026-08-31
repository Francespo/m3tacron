import type { PageLoad } from './$types';
import { API_BASE } from '$lib/api';
import { browser } from '$app/environment';
import { filters } from '$lib/stores/filters.svelte';

function buildForwardParams(url: URL): URLSearchParams {
    // Forward every global filter from the URL to the 4 ship detail endpoints.
    // Exclude keys that are ships-overview specific (pagination/sort) — the
    // detail endpoint's own `faction` toggle is forwarded explicitly below.
    const SKIP = new Set(['page', 'size', 'sort_metric', 'sort_direction']);
    const out = new URLSearchParams();

    for (const [k, v] of url.searchParams.entries()) {
        if (SKIP.has(k)) continue;
        if (k === 'epic') continue;
        out.append(k, v);
    }

    // Ensure data_source always present (backend defaults to xwa but we want explicit)
    if (!out.has('data_source')) {
        const ds = url.searchParams.get('data_source') || (browser ? filters.dataSource : 'xwa');
        out.set('data_source', ds);
    }

    const ds = out.get('data_source') || 'xwa';
    if (!out.has('formats')) {
        const defFormats = ds === 'legacy' ? ['legacy_x2po'] : ['xwa'];
        for (const f of defFormats) {
            out.append('formats', f);
        }
    }
    return out;
}

export const load: PageLoad = async ({ fetch, params, url }) => {
    url.search; // Force reactivity
    const shipXws = params.xws;

    const fwd = buildForwardParams(url);
    const qs = fwd.toString();
    const factionParam = url.searchParams.get('faction') || 'all';

    // Fetch all endpoints in parallel, all sharing the same global filters
    const [infoRes, pilotsRes, listsRes, squadronsRes] = await Promise.allSettled([
        fetch(`${API_BASE}/ship/${shipXws}?${qs}`),
        fetch(`${API_BASE}/ship/${shipXws}/pilots?${qs}`),
        fetch(`${API_BASE}/ship/${shipXws}/lists?${qs}&limit=10`),
        fetch(`${API_BASE}/ship/${shipXws}/squadrons?${qs}&limit=10`),
    ]);

    const shipData = infoRes.status === 'fulfilled' && infoRes.value.ok
        ? await infoRes.value.json() : { info: { name: shipXws, xws: shipXws, factions: [] }, stats: {} };

    const pilotsData = pilotsRes.status === 'fulfilled' && pilotsRes.value.ok
        ? await pilotsRes.value.json() : { pilots: [] };

    const listsData = listsRes.status === 'fulfilled' && listsRes.value.ok
        ? await listsRes.value.json() : { lists: [] };

    const squadronsData = squadronsRes.status === 'fulfilled' && squadronsRes.value.ok
        ? await squadronsRes.value.json() : { squadrons: [] };

    return {
        shipXws,
        info: shipData.info,
        stats: shipData.stats,
        pilots: pilotsData.pilots || [],
        lists: listsData.lists || [],
        squadrons: squadronsData.squadrons || [],
        faction: factionParam,
    };
};
