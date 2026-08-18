import type { PageLoad } from './$types';
import { API_BASE } from '$lib/api';

export const load: PageLoad = async ({ fetch, url }) => {
    url.search; // Force reactivity when any query param changes

    const apiUrl = new URL(`${API_BASE}/ships`, url.origin);
    for (const [key, value] of url.searchParams.entries()) {
        apiUrl.searchParams.append(key, value);
    }
    if (!apiUrl.searchParams.has('page')) apiUrl.searchParams.set('page', '0');
    if (!apiUrl.searchParams.has('size')) apiUrl.searchParams.set('size', '200');

    const sort_metric = url.searchParams.get('sort_metric') || 'Lists';
    const sort_direction = url.searchParams.get('sort_direction') || 'desc';

    const parsePayload = (data: any) => ({
        items: data?.items ?? [],
        total: Number(data?.total ?? 0),
        page: Number(data?.page ?? 0),
        size: Number(data?.size ?? 50),
        sort_metric,
        sort_direction,
    });

    // Return a promise so SvelteKit navigates immediately and streams data in.
    // This prevents navigation from blocking on slow API responses.
    const itemsPromise = fetch(apiUrl.toString())
        .then(async (response) => {
            if (!response.ok) throw new Error(`Failed to fetch ships: ${response.status}`);
            const data = await response.json();
            return parsePayload(data);
        })
        .catch((e) => {
            console.error('Fetch failed:', e);
            return { items: [], total: 0, page: 0, size: 50, sort_metric, sort_direction };
        });

    // Raw API ships list for client-side merging with xwingData.
    //
    // The merge needs EVERY ship's stats: toggling "Include Epic" must make
    // Huge ships appear/disappear in the client-side grid, and the merge
    // zeroes any ship missing from this lookup. The URL carries the UI's own
    // page/size (50 per page), so forwarding those would truncate the stats
    // lookup to a single page — ships on other pages would render as 0-stat
    // duplicates and Epic ships would sink out of the grid. Fetch the full
    // list (backend cap is size=200) and paginate the grid client-side.
    const mergeApiUrl = new URL(`${API_BASE}/ships`, url.origin);
    for (const [key, value] of url.searchParams.entries()) {
        mergeApiUrl.searchParams.append(key, value);
    }
    mergeApiUrl.searchParams.set('page', '0');
    mergeApiUrl.searchParams.set('size', '200');
    const apiShipsPromise = fetch(mergeApiUrl.toString())
        .then(async (response) => {
            if (!response.ok) return [];
            const data = await response.json();
            return data?.items ?? [];
        })
        .catch((e) => {
            console.error('Fetch failed:', e);
            return [];
        });

    return { itemsPromise, apiShipsPromise, sort_metric, sort_direction };
};
