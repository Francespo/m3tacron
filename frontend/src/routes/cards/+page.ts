import type { PageLoad } from './$types';
import { API_BASE } from '$lib/api';

export const load: PageLoad = async ({ fetch, url }) => {
    url.search; // Force reactivity when any query param changes
    const tab = url.searchParams.get('tab') || 'pilots';

    const endpoint = tab === 'upgrades' ? 'upgrades' : 'pilots';
    const apiUrl = new URL(`${API_BASE}/cards/${endpoint}`, url.origin);

    for (const [key, value] of url.searchParams.entries()) {
        if (key !== 'tab') apiUrl.searchParams.append(key, value);
    }
    if (!apiUrl.searchParams.has('page')) apiUrl.searchParams.set('page', '0');
    if (!apiUrl.searchParams.has('size')) apiUrl.searchParams.set('size', '20');

    const sort_metric = url.searchParams.get('sort_metric') || 'Popularity';
    const sort_direction = url.searchParams.get('sort_direction') || 'desc';

    const parsePayload = (data: any) => ({
        items: data?.items ?? [],
        total: Number(data?.total ?? 0),
        page: Number(data?.page ?? 0),
        size: Number(data?.size ?? 20),
        sort_metric,
        sort_direction,
    });

    // Return a promise so SvelteKit navigates immediately and streams data in.
    // This prevents navigation from blocking on slow API responses.
    const itemsPromise = fetch(apiUrl.toString())
        .then(async (response) => {
            if (!response.ok) throw new Error(`Failed to fetch cards: ${response.status}`);
            const data = await response.json();
            return parsePayload(data);
        })
        .catch((e) => {
            console.error('Fetch failed:', e);
            return { items: [], total: 0, page: 0, size: 20, sort_metric, sort_direction };
        });

    return { itemsPromise, sort_metric, sort_direction, tab };
};
