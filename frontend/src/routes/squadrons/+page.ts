import type { PageLoad } from './$types';
import { API_BASE } from '$lib/api';

export const load: PageLoad = async ({ fetch, url }) => {
    url.search; // Force reactivity when any query param changes

    const apiUrl = new URL(`${API_BASE}/squadrons`);
    for (const [key, value] of url.searchParams.entries()) {
        apiUrl.searchParams.append(key, value);
    }
    if (!apiUrl.searchParams.has('page')) apiUrl.searchParams.set('page', '0');
    if (!apiUrl.searchParams.has('size')) apiUrl.searchParams.set('size', '20');

    try {
        const res = await fetch(apiUrl.toString());
        if (!res.ok) throw new Error('Failed to fetch');
        const data = await res.json();
        return { items: data.items, total: data.total };
    } catch {
        return { items: [], total: 0 };
    }
};
