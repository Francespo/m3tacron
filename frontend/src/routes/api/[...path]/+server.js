/** @param {*} raw */
function normalizeBackendApiBase(raw) {
	const trimmed = String(raw || '').trim().replace(/\/+$/, '');
	return trimmed.endsWith('/api') ? trimmed : `${trimmed}/api`;
}

function previewBackendHost() {
	const branch = String(process.env.COOLIFY_BRANCH || '').replace(/^"|"$/g, '').trim();
	const fromBranch = branch.match(/^pull\/(\d+)/);
	if (fromBranch) {
		return `backend-pr-${fromBranch[1]}`;
	}
	return null;
}

/** @param {string | undefined} [requestUrl] */
function resolveBackendApiBase(requestUrl) {
	const cleanBranch = String(process.env.COOLIFY_BRANCH || '').replace(/^"|"$/g, '').trim();
	const isPreview = process.env.ENV_VAR_SOURCE === 'preview' || cleanBranch.startsWith('pull/');
	if (isPreview) {
		const host = previewBackendHost();
		if (host) {
			return `http://${host}:8888/api`;
		}
	}

	if (requestUrl) {
		try {
			const host = new URL(requestUrl).hostname.toLowerCase();
			const match = host.match(/^(\d+)\.dev\.m3tacron\.com$/);
			if (match) {
				return `http://backend-pr-${match[1]}:8888/api`;
			}
		} catch {}
	}

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

/**
 * @param {import('./$types').RequestEvent} event
 * @param {string} method
 */
async function proxyToBackend({ params, url, request }, method) {
	const path = params.path || '';
	const backendBase = resolveBackendApiBase(request?.url);
	const target = new URL(`${backendBase}/${path}`);

	for (const [key, value] of url.searchParams.entries()) {
		target.searchParams.append(key, value);
	}

	/** @type {Record<string, string>} */
	const headers = {};
	const contentType = request.headers.get('content-type');
	if (contentType) headers['content-type'] = contentType;
	const accept = request.headers.get('accept');
	if (accept) headers['accept'] = accept;

	/** @type {RequestInit & { duplex?: string }} */
	const init = { method, headers };
	if (method !== 'GET' && method !== 'HEAD') {
		init.body = await request.arrayBuffer();
		// undici fetch needs duplex when streaming
		init.duplex = 'half';
	}
	// Bypass SvelteKit CSRF origin check for trusted webhook callers (Ko-fi posts from ko-fi.com)
	// by forwarding via server-side fetch which is not subject to the check, but SvelteKit
	// still validates the incoming request before we get here. We handle POST separately via
	// the csrf trustedOrigins config (see svelte.config.js).
	const upstream = await fetch(target.toString(), init);

	const body = await upstream.arrayBuffer();
	const responseHeaders = new Headers();
	const upstreamContentType = upstream.headers.get('content-type');
	if (upstreamContentType) responseHeaders.set('content-type', upstreamContentType);

	return new Response(body, {
		status: upstream.status,
		headers: responseHeaders
	});
}

/** @type {import('./$types').RequestHandler} */
export async function GET(event) {
	return proxyToBackend(event, 'GET');
}

/** @type {import('./$types').RequestHandler} */
export async function POST(event) {
	return proxyToBackend(event, 'POST');
}
