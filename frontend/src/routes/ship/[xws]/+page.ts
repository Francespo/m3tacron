import type { PageLoad } from './$types';
import { API_BASE } from '$lib/api';

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
        const ds = url.searchParams.get('data_source') || 'xwa';
        out.set('data_source', ds);
    }

    return out;
}

export const load: PageLoad = async ({ fetch, params, url }) => {
    url.search; // Force reactivity
    const shipXws = params.xws;

    const fwd = buildForwardParams(url);
    const qs = fwd.toString();
    const factionParam = url.searchParams.get('faction') || 'all';

    // Streaming load: header + pilots are cache-warm (0.002s) and render first paint.
    // Below-fold lists/squadrons stream in after, with a small Updating… indicator.
    const infoData: Promise<any> = fetch(`${API_BASE}/ship/${shipXws}?${qs}`)
        .then(r => r.ok ? r.json() : { info: { name: shipXws, xws: shipXws, factions: [] }, stats: {} })
        .catch(() => ({ info: { name: shipXws, xws: shipXws, factions: [] }, stats: {} }));
    const pilotsDataP: Promise<any> = fetch(`${API_BASE}/ship/${shipXws}/pilots?${qs}`)
        .then(r => r.ok ? r.json() : { pilots: [] })
        .catch(() => ({ pilots: [] }));
    const listsDataP: Promise<any> = fetch(`${API_BASE}/ship/${shipXws}/lists?${qs}&limit=10`)
        .then(r => r.ok ? r.json() : { lists: [] })
        .catch(() => ({ lists: [] }));
    const squadronsDataP: Promise<any> = fetch(`${API_BASE}/ship/${shipXws}/squadrons?${qs}`)
        .then(r => r.ok ? r.json() : { squadrons: [] })
        .catch(() => ({ squadrons: [] }));

    return {
        shipXws,
        faction: factionParam,
        infoData,
        pilotsData: pilotsDataP,
        listsData: listsDataP,
        squadronsData: squadronsDataP,
        // sync fallbacks for back-compat while the .svelte awaits
        info: { name: shipXws, xws: shipXws, factions: [] }, stats: {},
        pilots: [], lists: [], squadrons: [],
    };
};
