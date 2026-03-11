import type { PageLoad } from './$types';
import { API_BASE } from '$lib/api';

export const load: PageLoad = async ({ fetch, url }) => {
    url.search; // Force reactivity when any query param changes

    const apiUrl = new URL(`${API_BASE}/ships`);
    for (const [key, value] of url.searchParams.entries()) {
        apiUrl.searchParams.append(key, value);
    }
    if (!apiUrl.searchParams.has('page')) apiUrl.searchParams.set('page', '0');
    if (!apiUrl.searchParams.has('size')) apiUrl.searchParams.set('size', '50');

    try {
        const response = await fetch(apiUrl.toString());
        if (!response.ok) throw new Error('Failed to fetch ships');
        const data = await response.json();
        return { 
            items: data.items, 
            total: data.total, 
            page: parseInt(data.page), 
            size: parseInt(data.size),
            includeEpic: url.searchParams.get('include_epic') === 'true'
        };
    } catch (e) {
        console.error(e);
        return { items: [], total: 0, page: 0, size: 50, includeEpic: false };
    }
};
