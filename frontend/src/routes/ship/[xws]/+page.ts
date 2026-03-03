import type { PageLoad } from './$types';
import { API_BASE } from '$lib/api';

export const load: PageLoad = async ({ fetch, params, url }) => {
    url.search; // Force reactivity
    const shipXws = params.xws;
    const ds = url.searchParams.get('data_source') || 'xwa';

    // Fetch all endpoints in parallel
    const [infoRes, pilotsRes, listsRes, squadronsRes] = await Promise.allSettled([
        fetch(`${API_BASE}/ship/${shipXws}?data_source=${ds}`),
        fetch(`${API_BASE}/ship/${shipXws}/pilots?data_source=${ds}`),
        fetch(`${API_BASE}/ship/${shipXws}/lists?data_source=${ds}&limit=10`),
        fetch(`${API_BASE}/ship/${shipXws}/squadrons?data_source=${ds}&limit=10`),
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
    };
};
