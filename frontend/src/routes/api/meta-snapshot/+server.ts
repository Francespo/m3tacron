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

export async function GET({ url, fetch, request }) {
    const source = url.searchParams.get('data_source') || 'xwa';
    const epic = url.searchParams.get('epic') === 'true';
    const days = url.searchParams.get('days');
    const dateStart = url.searchParams.get('date_start');
    const dateEnd = url.searchParams.get('date_end');
    const timeRange = url.searchParams.get('time_range');
    const backendApiBase = resolveBackendApiBase(url);
    const CACHE_HEADERS = ['etag', 'cache-control', 'last-modified', 'vary'];

    try {
        const params = new URLSearchParams();
        params.set('data_source', source);
        if (epic) params.set('epic', 'true');
        if (days !== null && days !== undefined && days !== '') params.set('days', days);
        if (dateStart) params.set('date_start', dateStart);
        if (dateEnd) params.set('date_end', dateEnd);
        if (timeRange) params.set('time_range', timeRange);

        const upstreamHeaders: Record<string, string> = {};
        const ifNoneMatch = request.headers.get('if-none-match');
        if (ifNoneMatch) upstreamHeaders['if-none-match'] = ifNoneMatch;
        const ifModifiedSince = request.headers.get('if-modified-since');
        if (ifModifiedSince) upstreamHeaders['if-modified-since'] = ifModifiedSince;

        const res = await fetch(`${backendApiBase}/meta-snapshot?${params.toString()}`, {
            headers: upstreamHeaders
        });

        const passthrough = new Headers();
        for (const name of CACHE_HEADERS) {
            const value = res.headers.get(name);
            if (value) passthrough.set(name, value);
        }

        // Revalidated: keep the headers so the browser can reuse the response.
        if (res.status === 304) {
            return new Response(null, { status: 304, headers: passthrough });
        }
        if (!res.ok) {
            throw new Error(`Backend error: ${res.status}`);
        }
        const data = await res.json();
        return json(data, { headers: passthrough });
    } catch (e) {
        return json({ error: String(e) }, { status: 500 });
    }
}
