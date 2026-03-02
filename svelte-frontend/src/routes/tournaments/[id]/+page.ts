import type { PageLoad } from './$types';
import { API_BASE } from '$lib/api';

export const load: PageLoad = async ({ params, fetch }) => {
    const id = params.id;
    try {
        const res = await fetch(`${API_BASE}/tournaments/${id}`);
        if (!res.ok) throw new Error('Failed to fetch');
        const data = await res.json();
        return { detail: data, id };
    } catch {
        return { detail: null, id };
    }
};
