import type { PageLoad } from './$types';
import { API_BASE } from '$lib/api';
import { browser } from '$app/environment';
import { filters } from '$lib/stores/filters.svelte';

export const load: PageLoad = async ({ fetch, params, url }) => {
    url.search; // Force reactivity
    const shipXws = params.xws;
    const ds = url.searchParams.get('data_source') || 'xwa';

    // Include Epic: honor the URL param when present (SSR / direct nav) and
    // fall back to the shared filter store on the client so navigating from
    // /ships with the toggle on keeps Huge-ship pilots visible. Never read
    // the module-level store on the server (no cross-request contamination).
    const includeEpic =
        url.searchParams.get('epic') === 'true' ||
        (browser && filters.includeEpic);

    // Optional faction scoping: /ships?faction=rebelalliance carries the
    // selected faction from the ships-page pill into this detail page.
    // When set, pilots/lists/squadrons/stats (and the page accent) restrict
    // to that faction.
    const factionParam = url.searchParams.get('faction') || '';

    const pilotsUrl = new URL(`${API_BASE}/ship/${shipXws}/pilots`, url.origin);
    pilotsUrl.searchParams.set('data_source', ds);
    pilotsUrl.searchParams.set('epic', String(includeEpic));
    if (factionParam && factionParam !== 'all') {
        pilotsUrl.searchParams.set('faction', factionParam);
    }

    const listsUrl = new URL(`${API_BASE}/ship/${shipXws}/lists`, url.origin);
    listsUrl.searchParams.set('data_source', ds);
    listsUrl.searchParams.set('limit', '10');
    if (factionParam && factionParam !== 'all') {
        listsUrl.searchParams.set('faction', factionParam);
    }

    const squadronsUrl = new URL(`${API_BASE}/ship/${shipXws}/squadrons`, url.origin);
    squadronsUrl.searchParams.set('data_source', ds);
    squadronsUrl.searchParams.set('limit', '10');
    if (factionParam && factionParam !== 'all') {
        squadronsUrl.searchParams.set('faction', factionParam);
    }

    // Fetch all endpoints in parallel
    const [infoRes, pilotsRes, listsRes, squadronsRes] = await Promise.allSettled([
        fetch(`${API_BASE}/ship/${shipXws}?data_source=${ds}&epic=${includeEpic}${factionParam && factionParam !== 'all' ? `&faction=${factionParam}` : ''}`),
        fetch(pilotsUrl.toString()),
        fetch(listsUrl.toString()),
        fetch(squadronsUrl.toString()),
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
        faction: factionParam || 'all',
    };
};
