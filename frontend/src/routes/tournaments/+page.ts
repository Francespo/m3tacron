import type { PageLoad } from './$types';
import { API_BASE } from '$lib/api';

export const load: PageLoad = async ({ fetch, url }) => {
    url.search; // Force reactivity when any query param changes
    const search = url.searchParams.get('search') || '';

    const apiUrl = new URL(`${API_BASE}/tournaments`, url.origin);
    for (const [key, value] of url.searchParams.entries()) {
        apiUrl.searchParams.append(key, value);
    }
    if (!apiUrl.searchParams.has('page')) apiUrl.searchParams.set('page', '0');
    if (!apiUrl.searchParams.has('size')) apiUrl.searchParams.set('size', '20');

    // Return a promise so SvelteKit navigates immediately and streams data in.
    // This prevents navigation from blocking on slow API responses.
    const itemsPromise = fetch(apiUrl.toString())
        .then(async (response) => {
            if (!response.ok) throw new Error(`Failed to fetch tournaments: ${response.status}`);
            const data = await response.json();
            return {
                items: data?.items ?? [],
                total: Number(data?.total ?? 0),
                page: parseInt(data?.page) || 0,
                size: parseInt(data?.size) || 20,
                search,
            };
        })
        .catch((e) => {
            console.error('Fetch failed:', e);
            return { items: [], total: 0, page: 0, size: 20, search };
        });

    return { itemsPromise, search };
};
