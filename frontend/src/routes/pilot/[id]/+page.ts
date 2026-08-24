import type { PageLoad } from './$types';
import { API_BASE } from '$lib/api';

export const load: PageLoad = async ({ fetch, params, url }) => {
    url.search; // Force reactivity
    const pilotXws = params.id;
    const ds = url.searchParams.get('data_source') === 'legacy' ? 'legacy' : 'xwa';
    const includeEpic = url.searchParams.get('epic') === 'true';
    const hasEpicParam = url.searchParams.has('epic');

    const formatsFromUrl = url.searchParams.getAll('formats');
    const formats = formatsFromUrl.length > 0
        ? formatsFromUrl
        : (ds === 'xwa'
            ? (includeEpic ? ['xwa', 'xwa_epic'] : ['xwa'])
            : (includeEpic ? ['legacy_x2po', 'legacy_xlc', 'ffg', 'legacy_pandorum', 'legacy_epic'] : ['legacy_x2po', 'legacy_xlc', 'ffg', 'legacy_pandorum']));

    const formatQuery = formats.map((f) => `formats=${encodeURIComponent(f)}`).join('&');
    const formatSuffix = formatQuery ? `&${formatQuery}` : '';

    // Fetch all 4 endpoints in parallel — pull enough rows to paginate client-side (20 per page)
    const [infoRes, upgradesRes, chartRes, configRes] = await Promise.allSettled([
        fetch(`${API_BASE}/pilot/${pilotXws}?data_source=${ds}`),
        fetch(`${API_BASE}/pilot/${pilotXws}/upgrades?data_source=${ds}&size=200${formatSuffix}`),
        fetch(`${API_BASE}/pilot/${pilotXws}/chart?data_source=${ds}${formatSuffix}`),
        fetch(`${API_BASE}/pilot/${pilotXws}/configurations?data_source=${ds}&limit=100${formatSuffix}`),
    ]);

    // Header stats come from /api/pilot/{xws} (_headerStats) — no extra /cards fetches needed

    // Server-paginated Top Lists (SQL-backed): fetch page size 4, total is real (not 12 capped). Keep sync filters minimal for pilot detail.
    let pilotLists: any[] = [];
    let pilotListsTotal = 0;
    let pilotListsPageForLoad = 0;
    let pilotListsSortForLoad: "Games" | "Win Rate" = "Games";
    let pilotListsDirForLoad: "asc" | "desc" = "desc";
    // Initial load: page 0, Games desc, size 4 — real total (often 200+ for popular pilots)
    {
        const p = new URLSearchParams({ data_source: ds, sort_metric: pilotListsSortForLoad, sort_direction: pilotListsDirForLoad, size: "4", page: String(pilotListsPageForLoad) });
        for (const f of formats) p.append("formats", f);
        try {
            const r = await fetch(`${API_BASE}/pilot/${pilotXws}/lists?${p.toString()}`);
            if (r.ok) {
                const j = await r.json().catch(() => null);
                pilotLists = Array.isArray(j?.items) ? j.items : [];
                pilotListsTotal = Number(j?.total ?? 0) || 0;
            }
        } catch {}
    }

    const info = infoRes.status === 'fulfilled' && infoRes.value.ok
        ? await infoRes.value.json() : { name: pilotXws, xws: pilotXws, image: '' };
    const headerStats = (info as any)?._headerStats ?? null;

    const upgradesData = upgradesRes.status === 'fulfilled' && upgradesRes.value.ok
        ? await upgradesRes.value.json() : { items: [], total: 0 };

    const chartData = chartRes.status === 'fulfilled' && chartRes.value.ok
        ? await chartRes.value.json() : { data: [], series: [] };

    const configData = configRes.status === 'fulfilled' && configRes.value.ok
        ? await configRes.value.json() : { configurations: [], total: 0 };

    return {
        pilotXws,
        ds,
        includeEpic,
        hasEpicParam,
        formats,
        info,
        upgrades: upgradesData.items || [],
        upgrades_total: upgradesData.total || 0,
        chart: chartData.data || [],
        chartSeries: chartData.series || [],
        configurations: configData.configurations || [],
        configTotal: configData.total || 0,
        pilotLists,
        pilotListsTotal,
        headerStats,
    };
};
