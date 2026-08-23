import type { PageLoad } from './$types';
import { API_BASE } from '$lib/api';

export const load: PageLoad = async ({ fetch, params, url }) => {
    url.search; // Force reactivity
    const upgradeXws = params.id;
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

    const [infoRes, pilotsRes, shipsRes, chartRes, statsRes] = await Promise.allSettled([
        fetch(`${API_BASE}/upgrade/${upgradeXws}?data_source=${ds}`),
        fetch(`${API_BASE}/upgrade/${upgradeXws}/pilots?data_source=${ds}${formatSuffix}`),
        fetch(`${API_BASE}/upgrade/${upgradeXws}/ships?data_source=${ds}${formatSuffix}`),
        fetch(`${API_BASE}/upgrade/${upgradeXws}/chart?data_source=${ds}${formatSuffix}`),
        fetch(`${API_BASE}/cards/upgrades?data_source=${ds}&upgrade_id=${upgradeXws}&size=1&page=0`),
    ]);

    let info: any = null;
    if (infoRes.status === 'fulfilled' && infoRes.value.ok) {
        info = await infoRes.value.json().catch(() => null);
    }

    let pilots: any[] = [];
    if (pilotsRes.status === 'fulfilled' && pilotsRes.value.ok) {
        const j = await pilotsRes.value.json().catch(() => null);
        pilots = Array.isArray(j) ? j : (Array.isArray(j?.items) ? j.items : []);
    }

    let ships: any[] = [];
    if (shipsRes.status === 'fulfilled' && shipsRes.value.ok) {
        const j = await shipsRes.value.json().catch(() => null);
        ships = Array.isArray(j) ? j : (Array.isArray(j?.items) ? j.items : []);
    }

    let chart: any[] = [];
    let chartSeries: string[] = [];
    if (chartRes.status === 'fulfilled' && chartRes.value.ok) {
        const j = await chartRes.value.json().catch(() => null);
        chart = Array.isArray(j?.data) ? j.data : (Array.isArray(j) ? j : []);
        chartSeries = Array.isArray(j?.series) ? j.series : [];
    }

    // Fallback stats from cards/upgrades aggregate (for GAMES/LISTS/WR pills) when /upgrade/{xws} has none
    let stats: any = null;
    if (statsRes.status === 'fulfilled' && statsRes.value.ok) {
        const j = await statsRes.value.json().catch(() => null);
        const items = Array.isArray(j?.items) ? j.items : [];
        stats = items.find((it: any) => it?.xws === upgradeXws) ?? (items[0] ?? null);
    }

    return {
        upgradeXws,
        ds,
        includeEpic,
        hasEpicParam,
        formats,
        info,
        pilots,
        ships,
        chart,
        chartSeries,
        stats,
    };
};
