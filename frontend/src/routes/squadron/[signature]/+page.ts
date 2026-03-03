import type { PageLoad } from './$types';
import { API_BASE } from '$lib/api';

export const load: PageLoad = async ({ params, fetch, url }) => {
    const signature = params.signature;
    const ds = url.searchParams.get('data_source') || 'xwa';

    const [statsRes, pilotsRes, listsRes] = await Promise.allSettled([
        fetch(`${API_BASE}/squadron/${encodeURIComponent(signature)}/stats?data_source=${ds}`),
        fetch(`${API_BASE}/squadron/${encodeURIComponent(signature)}/pilots?data_source=${ds}`),
        fetch(`${API_BASE}/squadron/${encodeURIComponent(signature)}/lists?data_source=${ds}`)
    ]);

    const stats = statsRes.status === 'fulfilled' && statsRes.value.ok
        ? await statsRes.value.json() : null;
    const pilots = pilotsRes.status === 'fulfilled' && pilotsRes.value.ok
        ? await pilotsRes.value.json() : [];
    const lists = listsRes.status === 'fulfilled' && listsRes.value.ok
        ? await listsRes.value.json() : [];

    return {
        signature,
        stats,
        pilots,
        lists
    };
};
