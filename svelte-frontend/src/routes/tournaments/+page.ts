import type { PageLoad } from './$types';

export const load: PageLoad = async ({ fetch, url }) => {
    const page = url.searchParams.get('page') || '0';
    const size = url.searchParams.get('size') || '10';
    const search = url.searchParams.get('search') || '';

    // fetch API
    const apiUrl = new URL('http://127.0.0.1:8000/api/tournaments');
    apiUrl.searchParams.set('page', page);
    apiUrl.searchParams.set('size', size);
    if (search) apiUrl.searchParams.set('search', search);

    // Any formats, continents, etc.
    const formats = url.searchParams.getAll('formats');
    formats.forEach(f => apiUrl.searchParams.append('formats', f));

    try {
        const response = await fetch(apiUrl.toString());
        if (!response.ok) throw new Error('Failed to fetch tournaments');
        const data = await response.json();

        return {
            tournaments: data.items,
            total: data.total,
            page: parseInt(data.page),
            size: parseInt(data.size),
            search
        };
    } catch (e) {
        console.error(e);
        return {
            tournaments: [],
            total: 0,
            page: 0,
            size: 10,
            search
        }
    }
};
