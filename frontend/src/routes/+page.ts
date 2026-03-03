import type { PageLoad } from './$types';
import { API_BASE } from '$lib/api';

export const load: PageLoad = async ({ fetch }) => {
    try {
        const res = await fetch(`${API_BASE}/meta-snapshot`);
        if (!res.ok) {
            console.error(`Failed to fetch: ${res.status}`);
            return { data: null };
        }
        const data = await res.json();
        return { data };
    } catch (e) {
        console.error(e);
        return { data: null };
    }
};
