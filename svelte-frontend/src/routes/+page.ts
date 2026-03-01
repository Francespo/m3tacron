import type { PageLoad } from './$types';

export const load: PageLoad = async ({ fetch }) => {
    try {
        const res = await fetch('http://127.0.0.1:8000/api/meta-snapshot');
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
