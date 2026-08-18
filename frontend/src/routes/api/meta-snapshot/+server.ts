import { json } from '@sveltejs/kit';

function normalizeBackendApiBase(raw: string): string {
    const trimmed = String(raw || '').trim().replace(/\/+$/, '');
    return trimmed.endsWith('/api') ? trimmed : `${trimmed}/api`;
}

function resolveBackendFromRequestHost(url: URL): string | null {
    const host = url.hostname.toLowerCase();

    // Preview deployment - talk directly to local backend container via docker network
    const previewMatch = host.match(/^(\d+)\.dev\.m3tacron\.com$/);
    if (previewMatch) {
        return 'http://backend:8888/api';
    }

    // Shared dev domain.
    if (host === 'dev.m3tacron.com') {
        return `https://api.dev.m3tacron.com/api`;
    }

    // Production domains.
    if (host === 'm3tacron.com' || host === 'www.m3tacron.com') {
        return `https://api.m3tacron.com/api`;
    }

    return null;
}

function resolveBackendApiBase(url: URL): string {
    // Preview deployments: always use internal Docker network to reach backend
    if (process.env.ENV_VAR_SOURCE === 'preview' || process.env.COOLIFY_BRANCH?.startsWith('pull/')) {
        return 'http://backend:8888/api';
    }

    const fromHost = resolveBackendFromRequestHost(url);
    if (fromHost) {
        return fromHost;
    }

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

export async function GET({ url, fetch }) {
    const source = url.searchParams.get('data_source') || 'xwa';
    const epic = url.searchParams.get('epic') === 'true';
    const backendApiBase = resolveBackendApiBase(url);

    try {
        const epicQuery = epic ? '&epic=true' : '';
        const res = await fetch(`${backendApiBase}/meta-snapshot?data_source=${source}${epicQuery}`);
        if (!res.ok) {
            throw new Error(`Backend error: ${res.status}`);
        }
        const data = await res.json();
        return json(data);
    } catch (e) {
        return json({ error: String(e) }, { status: 500 });
    }
}
