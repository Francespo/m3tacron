import type { PageLoad } from './$types';

export const load: PageLoad = async ({ fetch, url }) => {
    const page = url.searchParams.get('page') || '0';
    const size = url.searchParams.get('size') || '20';

    const apiUrl = new URL('http://127.0.0.1:8000/api/ships');
    apiUrl.searchParams.set('page', page);
    apiUrl.searchParams.set('size', size);

    try {
        const response = await fetch(apiUrl.toString());
        if (!response.ok) throw new Error('Failed to fetch ships');
        const data = await response.json();
        return { ships: data.items, total: data.total, page: parseInt(data.page), size: parseInt(data.size) };
    } catch (e) {
        console.error(e);
        return { ships: [], total: 0, page: 0, size: 20 };
    }
};
