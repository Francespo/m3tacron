import { json } from '@sveltejs/kit';

function normalizeBackendApiBase(raw: string): string {
    const trimmed = String(raw || '').trim().replace(/\/+$/, '');
    return trimmed.endsWith('/api') ? trimmed : `${trimmed}/api`;
}

function previewBackendHost(): string | null {
    // PR-specific backend containers are reachable as `backend-pr-<N>` on the
    // shared coolify network. The generic `backend` alias belongs to the old
    // shared backend, so previews must target their own container.
    // COOLIFY_BRANCH is like `pull/131/head` but Coolify quotes the value
    // (e.g. `"pull/131/head"`), so strip any surrounding quotes first.
    const branch = String(process.env.COOLIFY_BRANCH || '').replace(/^"|"$/g, '');
    const fromBranch = branch.match(/^pull\/(\d+)/);
    if (fromBranch) {
        return `backend-pr-${fromBranch[1]}`;
    }
    return null;
}

function resolveBackendFromRequestHost(url: URL): string | null {
    const host = url.hostname.toLowerCase();

    // Preview deployment - talk directly to this PR's own backend container
    // via docker network (NEVER the shared/generic `backend` alias, which is
    // the old shared backend with a stale schema that lacks total_lists /
    // total_games).
    const previewMatch = host.match(/^(\d+)\.dev\.m3tacron\.com$/);
    if (previewMatch) {
        return `http://backend-pr-${previewMatch[1]}:8888/api`;
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
    // Preview deployments: always use this PR's own backend container.
    if (process.env.ENV_VAR_SOURCE === 'preview' || process.env.COOLIFY_BRANCH?.startsWith('pull/')) {
        const host = previewBackendHost();
        if (host) {
            return `http://${host}:8888/api`;
        }
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
