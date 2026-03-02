import type { PageLoad } from './$types';
import { API_BASE } from '$lib/api';

export const load: PageLoad = async ({ fetch, url }) => {
    const page = url.searchParams.get('page') || '0';
    const size = url.searchParams.get('size') || '20';
    const sort_metric = url.searchParams.get('sort_metric') || 'Games';
    const sort_direction = url.searchParams.get('sort_direction') || 'desc';

    const params = new URLSearchParams({
        page,
        size,
        sort_metric,
        sort_direction
    });

    try {
        const res = await fetch(`${API_BASE}/lists?${params.toString()}`);
        if (!res.ok) throw new Error('Failed to fetch');
        const data = await res.json();
        return { items: data.items, total: data.total };
    } catch {
        return { items: [], total: 0 };
    }
};
