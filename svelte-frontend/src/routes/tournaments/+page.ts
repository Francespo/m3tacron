import type { PageLoad } from './$types';
import { API_BASE } from '$lib/api';

export const load: PageLoad = async ({ fetch, url }) => {
    const page = url.searchParams.get('page') || '0';
    const size = url.searchParams.get('size') || '20';
    const search = url.searchParams.get('search') || '';

    const apiUrl = new URL(`${API_BASE}/tournaments`);
    apiUrl.searchParams.set('page', page);
    apiUrl.searchParams.set('size', size);
    if (search) apiUrl.searchParams.set('search', search);

    const formats = url.searchParams.getAll('formats');
    formats.forEach(f => apiUrl.searchParams.append('formats', f));

    try {
        const response = await fetch(apiUrl.toString());
        if (!response.ok) throw new Error('Failed to fetch tournaments');
        const data = await response.json();
        return {
            items: data.items,
            total: data.total,
            page: parseInt(data.page),
            size: parseInt(data.size),
            search
        };
    } catch (e) {
        console.error(e);
        return { items: [], total: 0, page: 0, size: 20, search };
    }
};
