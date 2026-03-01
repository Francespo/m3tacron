import type { PageLoad } from './$types';

export const load: PageLoad = async ({ fetch }) => {
    // Start with standard 'xwa'
    try {
        const res = await fetch('http://localhost:8000/api/meta-snapshot?data_source=xwa');
        if (!res.ok) {
            console.error('Failed to fetch from backend', res.statusText);
            return { error: 'Failed to connect to API', data: null };
        }
        const data = await res.json();
        return { data };
    } catch (err) {
        console.error('Fetch exception:', err);
        return { error: 'Could not reach backend API', data: null };
    }
};
