import type { PageLoad } from './$types';

export const load: PageLoad = async ({ fetch, url }) => {
    const page = url.searchParams.get('page') || '0';
    const size = url.searchParams.get('size') || '20';
    const tab = url.searchParams.get('tab') || 'pilots';

    const endpoint = tab === 'upgrades' ? 'upgrades' : 'pilots';
    const apiUrl = new URL(`http://127.0.0.1:8000/api/cards/${endpoint}`);
    apiUrl.searchParams.set('page', page);
    apiUrl.searchParams.set('size', size);

    try {
        const response = await fetch(apiUrl.toString());
        if (!response.ok) throw new Error('Failed to fetch cards');
        const data = await response.json();
        return { cards: data.items, total: data.total, page: parseInt(data.page), size: parseInt(data.size), tab };
    } catch (e) {
        console.error(e);
        return { cards: [], total: 0, page: 0, size: 20, tab };
    }
};
