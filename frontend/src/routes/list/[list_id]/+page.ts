import type { PageLoad } from './$types';
import { API_BASE } from '$lib/api';
import { browser } from '$app/environment';
import { filters } from '$lib/stores/filters.svelte';

export const load: PageLoad = async ({ params, fetch, url }) => {
    const listId = params.list_id;
    const ds = url.searchParams.get('data_source') || (browser ? filters.dataSource : 'xwa');

    // Return a promise so SvelteKit navigates immediately and streams data in.
    // This prevents navigation from blocking on slow API responses.
    const statsPromise = fetch(
        `${API_BASE}/list/${encodeURIComponent(listId)}/stats?data_source=${ds}`,
    )
        .then((res) => (res.ok ? res.json() : null))
        .catch(() => null);

    return {
        listId,
        statsPromise,
    };
};
