import type { PageLoad } from './$types';
import { API_BASE } from '$lib/api';

export const load: PageLoad = async ({ params, fetch }) => {
    const id = params.id;
    try {
        const res = await fetch(`${API_BASE}/tournaments?size=500`);
        if (!res.ok) throw new Error('Failed to fetch');
        const data = await res.json();
        const tournament = data.items.find((t: any) => String(t.id) === id);
        return { tournament: tournament || null, id };
    } catch {
        return { tournament: null, id };
    }
};
