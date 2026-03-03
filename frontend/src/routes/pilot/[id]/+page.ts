import type { PageLoad } from './$types';
import { API_BASE } from '$lib/api';

export const load: PageLoad = async ({ fetch, params, url }) => {
    url.search; // Force reactivity
    const pilotXws = params.id;
    const ds = url.searchParams.get('data_source') || 'xwa';

    // Fetch all 4 endpoints in parallel
    const [infoRes, upgradesRes, chartRes, configRes] = await Promise.allSettled([
        fetch(`${API_BASE}/pilot/${pilotXws}?data_source=${ds}`),
        fetch(`${API_BASE}/pilot/${pilotXws}/upgrades?data_source=${ds}&size=50`),
        fetch(`${API_BASE}/pilot/${pilotXws}/chart?data_source=${ds}`),
        fetch(`${API_BASE}/pilot/${pilotXws}/configurations?data_source=${ds}&limit=10`),
    ]);

    const info = infoRes.status === 'fulfilled' && infoRes.value.ok
        ? await infoRes.value.json() : { name: pilotXws, xws: pilotXws, image: '' };

    const upgradesData = upgradesRes.status === 'fulfilled' && upgradesRes.value.ok
        ? await upgradesRes.value.json() : { items: [], total: 0 };

    const chartData = chartRes.status === 'fulfilled' && chartRes.value.ok
        ? await chartRes.value.json() : { data: [], series: [] };

    const configData = configRes.status === 'fulfilled' && configRes.value.ok
        ? await configRes.value.json() : { configurations: [], total: 0 };

    return {
        pilotXws,
        info,
        upgrades: upgradesData.items || [],
        upgrades_total: upgradesData.total || 0,
        chart: chartData.data || [],
        chartSeries: chartData.series || [],
        configurations: configData.configurations || [],
        configTotal: configData.total || 0,
    };
};
