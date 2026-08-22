import type { PageLoad } from './$types';
import { API_BASE } from '$lib/api';

export const load: PageLoad = async ({ params, fetch }) => {
    const id = params.id;

    // Return a promise so SvelteKit navigates immediately and streams data in.
    // This prevents navigation from blocking on slow API responses.
    const detailPromise = fetch(`${API_BASE}/tournaments/${id}`)
        .then(async (res) => {
            if (!res.ok) throw new Error('Failed to fetch');
            return res.json();
        })
        .catch(() => null);

    return { detailPromise, id };
};
