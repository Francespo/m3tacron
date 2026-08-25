import { API_BASE } from '$lib/api';

export async function load({ fetch }) {
	try {
		const res = await fetch(`${API_BASE}/support/supporters`);
		if (!res.ok) throw new Error(`supporters ${res.status}`);
		const supporters = await res.json();
		return { supporters: Array.isArray(supporters) ? supporters : [] };
	} catch (e) {
		console.error('Failed to fetch support data', e);
		return { supporters: [] };
	}
}
