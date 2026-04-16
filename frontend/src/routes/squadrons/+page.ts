import type { PageLoad } from './$types';
import { API_BASE } from '$lib/api';

export const load: PageLoad = async ({ fetch, url }) => {
    url.search; // Force reactivity when any query param changes

    const page = Number(url.searchParams.get('page') ?? '0');
    const size = Number(url.searchParams.get('size') ?? '20');
    const sort_metric = url.searchParams.get('sort_metric') || 'Games';
    const sort_direction = url.searchParams.get('sort_direction') || 'desc';
    const selectedFactions = url.searchParams.getAll('factions');

    const apiUrl = new URL(`${API_BASE}/squadrons`, url.origin);
    for (const [key, value] of url.searchParams.entries()) {
        apiUrl.searchParams.append(key, value);
    }
    if (!apiUrl.searchParams.has('page')) apiUrl.searchParams.set('page', String(page));
    if (!apiUrl.searchParams.has('size')) apiUrl.searchParams.set('size', String(size));

    try {
        const res = await fetch(apiUrl.toString());
        if (!res.ok) throw new Error('Failed to fetch');
        const data = await res.json();
        return {
            items: data.items,
            total: data.total,
            page,
            size,
            sort_metric,
            sort_direction,
            selectedFactions,
        };
    } catch {
        return {
            items: [],
            total: 0,
            page,
            size,
            sort_metric,
            sort_direction,
            selectedFactions,
        };
    }
};
