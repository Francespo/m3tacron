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
        out.append(k, v);
    }

    // Ensure data_source always present (backend defaults to xwa but we want explicit)
    if (!out.has('data_source')) {
        const ds = url.searchParams.get('data_source') || (browser ? filters.dataSource : 'xwa');
        out.set('data_source', ds);
    }

    // Epic: URL param wins; on client, also honor the shared filter store so
    // navigating from /ships with the toggle on keeps Huge pilots visible.
    // Always forward epic so the backend cache key (|epic=...) is explicit.
    const includeEpic =
        url.searchParams.get('epic') === 'true' ||
        (browser && filters.includeEpic === true);
    out.set('epic', String(includeEpic));

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

    // Fetch unified ship detail endpoint (matches the Cards detail pattern)
    const res = await fetch(`${API_BASE}/ship/${shipXws}?${qs}&limit=10`);
    const data = res.ok ? await res.json() : null;

    return {
        shipXws,
        info: data?.info || { name: shipXws, xws: shipXws, factions: [] },
        stats: data?.stats || {},
        pilots: data?.pilots || [],
        lists: data?.lists || [],
        squadrons: data?.squadrons || [],
        faction: factionParam,
    };
};
