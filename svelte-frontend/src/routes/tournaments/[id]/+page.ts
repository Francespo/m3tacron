import type { PageLoad } from './$types';

export const load: PageLoad = async ({ params, fetch }) => {
    const id = params.id;
    try {
        // Fetch all tournaments to find the specific one
        const res = await fetch(`http://127.0.0.1:8000/api/tournaments?size=500`);
        if (!res.ok) throw new Error('Failed to fetch');
        const data = await res.json();
        const tournament = data.items.find((t: any) => String(t.id) === id);
        return { tournament: tournament || null, id };
    } catch {
        return { tournament: null, id };
    }
};
