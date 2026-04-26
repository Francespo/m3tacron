import type { PageLoad } from './$types';
import { API_BASE } from '$lib/api';

export const load: PageLoad = async ({ fetch, params, url }) => {
    url.search; // Force reactivity
    const shipXws = params.xws;
    const ds = url.searchParams.get('data_source') || 'xwa';
    const listsUrl = `${API_BASE}/ship/${shipXws}/lists?data_source=${ds}&limit=10`;
    const squadronsUrl = `${API_BASE}/ship/${shipXws}/squadrons?data_source=${ds}&limit=10`;

    // Critical-first: header + pilots.
    const [infoRes, pilotsRes] = await Promise.allSettled([
        fetch(`${API_BASE}/ship/${shipXws}?data_source=${ds}`),
        fetch(`${API_BASE}/ship/${shipXws}/pilots?data_source=${ds}`),
    ]);

    const shipData = infoRes.status === 'fulfilled' && infoRes.value.ok
        ? await infoRes.value.json() : { info: { name: shipXws, xws: shipXws, factions: [] }, stats: {} };

    const pilotsData = pilotsRes.status === 'fulfilled' && pilotsRes.value.ok
        ? await pilotsRes.value.json() : { pilots: [] };

    return {
        shipXws,
        info: shipData.info,
        stats: shipData.stats,
        pilots: pilotsData.pilots || [],
        lists: [],
        squadrons: [],
        listsUrl,
        squadronsUrl,
    };
};
