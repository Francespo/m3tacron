import { json } from '@sveltejs/kit';

function normalizeBackendApiBase(raw: string): string {
    const trimmed = String(raw || '').trim().replace(/\/+$/, '');
    return trimmed.endsWith('/api') ? trimmed : `${trimmed}/api`;
}

function resolveBackendApiBase(): string {
    const envBase = process.env.VITE_API_BASE;

    if (!envBase || envBase.startsWith('/')) {
        return 'http://backend:8888/api';
    }

    try {
        const parsed = new URL(envBase);
        if (parsed.hostname === 'localhost' || parsed.hostname === '127.0.0.1') {
            return 'http://backend:8888/api';
        }
        return normalizeBackendApiBase(envBase);
    } catch {
        return 'http://backend:8888/api';
    }
}

const BACKEND_API_BASE = resolveBackendApiBase();

export async function GET({ url, fetch }) {
    const source = url.searchParams.get('data_source') || 'xwa';
    try {
        const res = await fetch(`${BACKEND_API_BASE}/meta-snapshot?data_source=${source}`);
        if (!res.ok) {
            throw new Error(`Backend error: ${res.status}`);
        }
        const data = await res.json();
        return json(data);
    } catch (e) {
        return json({ error: String(e) }, { status: 500 });
    }
}
