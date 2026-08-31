import type { PageLoad } from './$types';
import { API_BASE } from '$lib/api';
import { browser } from '$app/environment';
import { filters } from '$lib/stores/filters.svelte';

export const load: PageLoad = async ({ fetch, params, url }) => {
    url.search; // Force reactivity
    const pilotXws = params.id;
    const ds = url.searchParams.get('data_source') || (browser ? filters.dataSource : 'xwa');
    const includeEpic = url.searchParams.get('epic') === 'true';
    const hasEpicParam = url.searchParams.has('epic');

    const formatsFromUrl = url.searchParams.getAll('formats');
    const formats = formatsFromUrl.length > 0
        ? formatsFromUrl
        : (ds === 'xwa' ? ['xwa'] : ['legacy_x2po']);

    const formatQuery = formats.map((f) => `formats=${encodeURIComponent(f)}`).join('&');
    const formatSuffix = formatQuery ? `&${formatQuery}` : '';

    // All fetches fire in parallel (no sequential awaits). Each resolves independently.
    const infoP = fetch(`${API_BASE}/pilot/${pilotXws}?data_source=${ds}`);
    const upgradesP = fetch(`${API_BASE}/pilot/${pilotXws}/upgrades?data_source=${ds}&size=200${formatSuffix}`);
    const chartP = fetch(`${API_BASE}/pilot/${pilotXws}/chart?data_source=${ds}${formatSuffix}`);
    const configP = fetch(`${API_BASE}/pilot/${pilotXws}/configurations?data_source=${ds}&limit=100${formatSuffix}`);
    const listsP = (async () => {
        const p = new URLSearchParams({ data_source: ds, sort_metric: "Games", sort_direction: "desc", size: "4", page: "0" });
        for (const f of formats) p.append("formats", f);
        const r = await fetch(`${API_BASE}/pilot/${pilotXws}/lists?${p.toString()}`);
        if (!r.ok) return { items: [], total: 0 };
        const j = await r.json().catch(() => null);
        return { items: Array.isArray(j?.items) ? j.items : [], total: Number(j?.total ?? 0) || 0 };
    })();

    const infoRes = await infoP;
    const upgradesRes = await upgradesP;
    const chartRes = await chartP;
    const configRes = await configP;
    const listsRes = await listsP;

    // Header stats come from /api/pilot/{xws} (_headerStats) — no extra /cards fetches needed

    const pilotLists = Array.isArray(listsRes.items) ? listsRes.items : [];
    const pilotListsTotal = Number(listsRes.total ?? 0) || 0;

    const info = infoRes.ok
        ? await infoRes.json().catch(() => ({ name: pilotXws, xws: pilotXws, image: '' })) : { name: pilotXws, xws: pilotXws, image: '' };
    const headerStats = (info as any)?._headerStats ?? null;

    const upgradesData = upgradesRes.ok
        ? await upgradesRes.json().catch(() => ({ items: [], total: 0 })) : { items: [], total: 0 };

    const chartData = chartRes.ok
        ? await chartRes.json().catch(() => ({ data: [], series: [] })) : { data: [], series: [] };

    const configData = configRes.ok
        ? await configRes.json().catch(() => ({ configurations: [], total: 0 })) : { configurations: [], total: 0 };

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
