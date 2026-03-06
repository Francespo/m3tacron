import { json } from '@sveltejs/kit';
import { API_BASE } from '$lib/api';

export async function GET({ url, fetch }) {
    const source = url.searchParams.get('data_source') || 'xwa';
    try {
        const res = await fetch(`${API_BASE}/meta-snapshot?data_source=${source}`);
        if (!res.ok) {
            throw new Error(`Backend error: ${res.status}`);
        }
        const data = await res.json();
        return json(data);
    } catch (e) {
        return json({ error: String(e) }, { status: 500 });
    }
}
