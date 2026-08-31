import { json } from '@sveltejs/kit';

function normalizeBackendApiBase(raw: string): string {
    const trimmed = String(raw || '').trim().replace(/\/+$/, '');
    return trimmed.endsWith('/api') ? trimmed : `${trimmed}/api`;
}

function previewBackendHost(): string | null {
    const branch = String(process.env.COOLIFY_BRANCH || '').replace(/^"|"$/g, '').trim();
    const fromBranch = branch.match(/^pull\/(\d+)/);
    if (fromBranch) {
        return `backend-pr-${fromBranch[1]}`;
    }
    return null;
}

function resolveBackendApiBase(url: URL): string {
    const cleanBranch = String(process.env.COOLIFY_BRANCH || '').replace(/^"|"$/g, '').trim();
    const isPreview = process.env.ENV_VAR_SOURCE === 'preview' || cleanBranch.startsWith('pull/');
    if (isPreview) {
        const host = previewBackendHost();
        if (host) {
            return `http://${host}:8888/api`;
        }
    }

    try {
        const host = url.hostname.toLowerCase();
        const previewMatch = host.match(/^(\d+)\.dev\.m3tacron\.com$/);
        if (previewMatch) {
            return `http://backend-pr-${previewMatch[1]}:8888/api`;
        }
    } catch {}

    const envBase = process.env.VITE_API_BASE;
    if (envBase && !envBase.startsWith('/')) {
        try {
            const parsed = new URL(envBase);
            if (parsed.hostname !== 'localhost' && parsed.hostname !== '127.0.0.1') {
                return normalizeBackendApiBase(envBase);
            }
        } catch {}
    }

    return 'http://backend:8888/api';
}

export async function GET({ url, fetch }) {
    const source = url.searchParams.get('data_source') || 'xwa';
    const epic = url.searchParams.get('epic') === 'true';
    const days = url.searchParams.get('days');
    const dateStart = url.searchParams.get('date_start');
    const dateEnd = url.searchParams.get('date_end');
    const backendApiBase = resolveBackendApiBase(url);

    try {
        const params = new URLSearchParams();
        params.set('data_source', source);
        if (epic) params.set('epic', 'true');
        if (days !== null && days !== undefined && days !== '') params.set('days', days);
        if (dateStart) params.set('date_start', dateStart);
        if (dateEnd) params.set('date_end', dateEnd);

        const res = await fetch(`${backendApiBase}/meta-snapshot?${params.toString()}`);
        if (!res.ok) {
            throw new Error(`Backend error: ${res.status}`);
        }
        const data = await res.json();
        return json(data);
    } catch (e) {
        return json({ error: String(e) }, { status: 500 });
    }
}
