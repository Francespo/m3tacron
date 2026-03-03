import type { PageLoad } from './$types';
import { API_BASE } from '$lib/api';

export const load: PageLoad = async ({ fetch, url }) => {
    url.search; // Force reactivity when any query param changes
    const tab = url.searchParams.get('tab') || 'pilots';

    const endpoint = tab === 'upgrades' ? 'upgrades' : 'pilots';
    const apiUrl = new URL(`${API_BASE}/cards/${endpoint}`);

    for (const [key, value] of url.searchParams.entries()) {
        if (key !== 'tab') apiUrl.searchParams.append(key, value);
    }
    if (!apiUrl.searchParams.has('page')) apiUrl.searchParams.set('page', '0');
    if (!apiUrl.searchParams.has('size')) apiUrl.searchParams.set('size', '20');

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
