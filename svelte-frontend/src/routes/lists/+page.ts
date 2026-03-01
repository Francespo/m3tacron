import type { PageLoad } from './$types';

export const load: PageLoad = async ({ fetch, url }) => {
    const page = url.searchParams.get('page') || '0';
    const size = url.searchParams.get('size') || '20';
    const sort_metric = url.searchParams.get('sort_metric') || 'Games';
    const sort_direction = url.searchParams.get('sort_direction') || 'desc';

    const apiUrl = new URL('http://127.0.0.1:8000/api/lists');
    apiUrl.searchParams.set('page', page);
    apiUrl.searchParams.set('size', size);
    apiUrl.searchParams.set('sort_metric', sort_metric);
    apiUrl.searchParams.set('sort_direction', sort_direction);

    const factions = url.searchParams.getAll('factions');
    factions.forEach(f => apiUrl.searchParams.append('factions', f));

    try {
        const response = await fetch(apiUrl.toString());
        if (!response.ok) throw new Error('Failed to fetch lists');
        const data = await response.json();
        return { lists: data.items, total: data.total, page: parseInt(data.page), size: parseInt(data.size), sort_metric, sort_direction };
    } catch (e) {
        console.error(e);
        return { lists: [], total: 0, page: 0, size: 20, sort_metric, sort_direction };
    }
};
