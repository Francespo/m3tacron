import type { PageLoad } from './$types';
import { API_BASE } from '$lib/api';

export const load: PageLoad = async ({ fetch, url }) => {
    const page = url.searchParams.get('page') || '0';
    const size = url.searchParams.get('size') || '20';
    const tab = url.searchParams.get('tab') || 'pilots';

    const endpoint = tab === 'upgrades' ? 'upgrades' : 'pilots';
    const apiUrl = new URL(`${API_BASE}/cards/${endpoint}`);
    apiUrl.searchParams.set('page', page);
    apiUrl.searchParams.set('size', size);

    try {
        const response = await fetch(apiUrl.toString());
        if (!response.ok) throw new Error('Failed to fetch cards');
        const data = await response.json();
        return { items: data.items, total: data.total, page: parseInt(data.page), size: parseInt(data.size), tab };
    } catch (e) {
        console.error(e);
        return { items: [], total: 0, page: 0, size: 20, tab };
    }
};
