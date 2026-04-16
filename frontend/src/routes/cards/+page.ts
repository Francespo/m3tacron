import type { PageLoad } from './$types';
import { API_BASE } from '$lib/api';

export const load: PageLoad = async ({ fetch, url }) => {
    url.search; // Force reactivity when any query param changes
    const tab = url.searchParams.get('tab') || 'pilots';
    const page = Number(url.searchParams.get('page') ?? '0');
    const size = Number(url.searchParams.get('size') ?? '20');
    const sort_metric = url.searchParams.get('sort_metric') || 'Popularity';
    const sort_direction = url.searchParams.get('sort_direction') || 'desc';
    const search_text = url.searchParams.get('search_text') || '';
    const selectedFactions = url.searchParams.getAll('factions');

    const endpoint = tab === 'upgrades' ? 'upgrades' : 'pilots';
    const apiUrl = new URL(`${API_BASE}/cards/${endpoint}`, url.origin);

    for (const [key, value] of url.searchParams.entries()) {
        if (key !== 'tab') apiUrl.searchParams.append(key, value);
    }
    if (!apiUrl.searchParams.has('page')) apiUrl.searchParams.set('page', String(page));
    if (!apiUrl.searchParams.has('size')) apiUrl.searchParams.set('size', String(size));

    try {
        const response = await fetch(apiUrl.toString());
        if (!response.ok) throw new Error('Failed to fetch cards');
        const data = await response.json();
        return {
            items: data.items,
            total: data.total,
            page: Number(data.page ?? page),
            size: Number(data.size ?? size),
            tab,
            sort_metric,
            sort_direction,
            search_text,
            selectedFactions,
        };
    } catch (e) {
        console.error(e);
        return {
            items: [],
            total: 0,
            page,
            size,
            tab,
            sort_metric,
            sort_direction,
            search_text,
            selectedFactions,
        };
    }
};
