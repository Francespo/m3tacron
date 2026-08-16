import type { PageLoad } from './$types';
import { API_BASE } from '$lib/api';

export const load: PageLoad = async ({ params, fetch, url }) => {
    const listId = params.list_id;
    const ds = url.searchParams.get('data_source') || 'xwa';

    const res = await fetch(`${API_BASE}/list/${encodeURIComponent(listId)}/stats?data_source=${ds}`);
    let stats = null;

    if (res.ok) {
        stats = await res.json();
    }

    return {
        listId,
        stats
    };
};
