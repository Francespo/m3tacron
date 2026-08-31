import type { PageLoad } from './$types';
import { API_BASE } from '$lib/api';
import { browser } from '$app/environment';
import { filters } from '$lib/stores/filters.svelte';

export const load: PageLoad = async ({ fetch, params, url }) => {
    url.search; // Force reactivity
    const upgradeXws = params.id;
    const ds = url.searchParams.get('data_source') || (browser ? filters.dataSource : 'xwa');

    const formatsFromUrl = url.searchParams.getAll('formats');
    const formats = formatsFromUrl.length > 0
        ? formatsFromUrl
        : (ds === 'xwa' ? ['xwa'] : ['legacy_x2po']);

    const formatQuery = formats.map((f) => `formats=${encodeURIComponent(f)}`).join('&');
    const formatSuffix = formatQuery ? `&${formatQuery}` : '';

    // Fire every fetch at once — page render never blocks on any single endpoint.
    const infoP = fetch(`${API_BASE}/upgrade/${upgradeXws}?data_source=${ds}`);
    const pilotsP = fetch(`${API_BASE}/upgrade/${upgradeXws}/pilots?data_source=${ds}${formatSuffix}`);
    const shipsP = fetch(`${API_BASE}/upgrade/${upgradeXws}/ships?data_source=${ds}${formatSuffix}`);
    const chartP = fetch(`${API_BASE}/upgrade/${upgradeXws}/chart?data_source=${ds}${formatSuffix}`);
    const statsP = fetch(`${API_BASE}/cards/upgrades?data_source=${ds}&upgrade_id=${upgradeXws}&size=1&page=0${formatSuffix}`);

    const infoRes = await infoP;
    const pilotsRes = await pilotsP;
    const shipsRes = await shipsP;
    const chartRes = await chartP;
    const statsRes = await statsP;

    let info: any = null;
    if (infoRes.ok) info = await infoRes.json().catch(() => null);

    let pilots: any[] = [];
    if (pilotsRes.ok) {
        const j = await pilotsRes.json().catch(() => null);
        pilots = Array.isArray(j) ? j : (Array.isArray(j?.items) ? j.items : []);
    }

    let ships: any[] = [];
    if (shipsRes.ok) {
        const j = await shipsRes.json().catch(() => null);
        ships = Array.isArray(j) ? j : (Array.isArray(j?.items) ? j.items : []);
    }

    let chart: any[] = [];
    let chartSeries: string[] = [];
    if (chartRes.ok) {
        const j = await chartRes.json().catch(() => null);
        chart = Array.isArray(j?.data) ? j.data : (Array.isArray(j) ? j : []);
        chartSeries = Array.isArray(j?.series) ? j.series : [];
    }

    // Fallback stats from cards/upgrades aggregate (for GAMES/LISTS/WR pills) when /upgrade/{xws} has none
    let stats: any = null;
    if (statsRes.ok) {
        const j = await statsRes.json().catch(() => null);
        const items = Array.isArray(j?.items) ? j.items : [];
        stats = items.find((it: any) => it?.xws === upgradeXws) ?? (items[0] ?? null);
    }

    return {
        upgradeXws,
        ds,
        formats,
        info,
        pilots,
        ships,
        chart,
        chartSeries,
        stats,
    };
};
