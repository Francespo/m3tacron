import type { PageLoad } from './$types';
import { API_BASE } from '$lib/api';

export const load: PageLoad = async ({ fetch, url }) => {
    url.search; // Force reactivity when any query param changes

    const apiUrl = new URL(`${API_BASE}/lists`);
    for (const [key, value] of url.searchParams.entries()) {
        apiUrl.searchParams.append(key, value);
    }
    if (!apiUrl.searchParams.has('page')) apiUrl.searchParams.set('page', '0');
    if (!apiUrl.searchParams.has('size')) apiUrl.searchParams.set('size', '20');

    const sort_metric = url.searchParams.get('sort_metric') || 'Games';
    const sort_direction = url.searchParams.get('sort_direction') || 'desc';

    try {
        const response = await fetch(apiUrl.toString());
        if (!response.ok) throw new Error('Failed to fetch lists');
        const data = await response.json();
        return { 
            items: data.items, 
            total: data.total, 
            page: parseInt(data.page), 
            size: parseInt(data.size), 
            sort_metric, 
            sort_direction,
            includeEpic: url.searchParams.get('include_epic') === 'true'
        };
    } catch (e) {
        console.error(e);
        return { items: [], total: 0, page: 0, size: 20, sort_metric, sort_direction, includeEpic: false };
    }
};
