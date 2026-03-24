import type { PageLoad } from './$types';
import { API_BASE } from '$lib/api';

export const load: PageLoad = async ({ fetch, url }) => {
    url.search; // Force reactivity when any query param changes

    const apiUrl = new URL(`${API_BASE}/lists`, url.origin);
    for (const [key, value] of url.searchParams.entries()) {
        apiUrl.searchParams.append(key, value);
    }
    if (!apiUrl.searchParams.has('page')) apiUrl.searchParams.set('page', '0');
    if (!apiUrl.searchParams.has('size')) apiUrl.searchParams.set('size', '20');

    const sort_metric = url.searchParams.get('sort_metric') || 'Games';
    const sort_direction = url.searchParams.get('sort_direction') || 'desc';

    const parsePayload = (data: any) => ({
        items: data?.items ?? [],
        total: Number(data?.total ?? 0),
        page: Number(data?.page ?? 0),
        size: Number(data?.size ?? 20),
        sort_metric,
        sort_direction,
    });

    try {
        const response = await fetch(apiUrl.toString());
        if (!response.ok) throw new Error(`Failed to fetch lists: ${response.status}`);
        const data = await response.json();
        return parsePayload(data);
    } catch (e) {
        console.error('Primary lists fetch failed, retrying same-origin /api:', e);

        try {
            const fallbackUrl = new URL('/api/lists', url.origin);
            for (const [key, value] of url.searchParams.entries()) {
                fallbackUrl.searchParams.append(key, value);
            }
            if (!fallbackUrl.searchParams.has('page')) fallbackUrl.searchParams.set('page', '0');
            if (!fallbackUrl.searchParams.has('size')) fallbackUrl.searchParams.set('size', '20');

            const fallbackResponse = await fetch(fallbackUrl.toString());
            if (!fallbackResponse.ok) throw new Error(`Fallback failed: ${fallbackResponse.status}`);
            const fallbackData = await fallbackResponse.json();
            return parsePayload(fallbackData);
        } catch (fallbackError) {
            console.error('Fallback lists fetch failed:', fallbackError);
            return { items: [], total: 0, page: 0, size: 20, sort_metric, sort_direction };
        }
    }
};
