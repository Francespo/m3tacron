import type { Handle } from '@sveltejs/kit';

const WEBHOOK_PREFIX = '/api/support/webhook/';

const FORM_CONTENT_TYPES = new Set([
	'application/x-www-form-urlencoded',
	'multipart/form-data',
	'text/plain'
]);

function isFormContentType(request: Request): boolean {
	const ct = request.headers.get('content-type')?.split(';', 1)[0].trim().toLowerCase() ?? '';
	if (FORM_CONTENT_TYPES.has(ct)) return true;
	// SvelteKit's BINARY_FORM_CONTENT_TYPE = application/octet-stream (devalue binary)
	return ct === 'application/octet-stream';
}

function isAllowedOrigin(requestOrigin: string, trustedPatterns: string[]): boolean {
	// Exact match including scheme + host + port
	if (trustedPatterns.includes(requestOrigin)) return true;
	// Wildcard patterns like https://*.ko-fi.com or http://localhost:*
	for (const pattern of trustedPatterns) {
		if (!pattern.includes('*')) continue;
		// Escape regex meta chars except *, then replace * with .*
		const escaped = pattern.replace(/[.+?^${}()|[\]\\]/g, '\\$&');
		const regexStr = '^' + escaped.replace(/\*/g, '.*') + '$';
		try {
			if (new RegExp(regexStr).test(requestOrigin)) return true;
		} catch {
			// ignore bad pattern
		}
	}
	return false;
}

const TRUSTED_ORIGINS: string[] = [
	'http://server-francesco:*',
	'http://100.69.158.7:*',
	'http://localhost:*',
	'http://127.0.0.1:*',
	'https://ko-fi.com',
	'https://*.ko-fi.com',
	'https://m3tacron.com',
	'https://*.m3tacron.com'
];

function csrfForbidden(request: Request, url: URL): boolean {
	const method = request.method;
	if (method !== 'POST' && method !== 'PUT' && method !== 'PATCH' && method !== 'DELETE') return false;
	if (!isFormContentType(request)) return false;
	const requestOrigin = request.headers.get('origin');
	if (requestOrigin === url.origin) return false;
	if (!requestOrigin) return true;
	return !isAllowedOrigin(requestOrigin, TRUSTED_ORIGINS);
}

export const handle: Handle = async ({ event, resolve }) => {
	// Ko-fi webhook: bypass CSRF and proxy directly to the backend.
	// Ko-fi sends a server-to-server POST with no Origin header as
	// application/x-www-form-urlencoded; verification_token in the JSON
	// payload authenticates the request, so the browser CSRF check does
	// not apply. We handle this BEFORE any CSRF logic so the request
	// does not 403 inside SvelteKit's built-in check (which is disabled
	// in svelte.config.js and re-implemented below).
	if (event.url.pathname.startsWith(WEBHOOK_PREFIX)) {
		const backendBase =
			process.env.ENV_VAR_SOURCE === 'preview' ||
			(String(process.env.COOLIFY_BRANCH || '').startsWith('pull/') ||
				String(process.env.COOLIFY_BRANCH || '').startsWith('"pull/'))
				? (() => {
						const branch = String(process.env.COOLIFY_BRANCH || '').replace(/^"|"$/g, '');
						const m = branch.match(/^pull\/(\d+)/);
						if (m) return `http://backend-pr-${m[1]}:8888/api`;
						const host = event.url.hostname;
						const hm = host.match(/^(\d+)\.dev\.m3tacron\.com$/);
						if (hm) return `http://backend-pr-${hm[1]}:8888/api`;
						return 'http://backend:8888/api';
					})()
				: 'http://backend:8888/api';

		const target = `${backendBase}${event.url.pathname.replace(/^\/api\//, '/')}${event.url.search}`;
		const headers: Record<string, string> = {};
		const ct = event.request.headers.get('content-type');
		if (ct) headers['content-type'] = ct;
		const accept = event.request.headers.get('accept');
		if (accept) headers['accept'] = accept;

		const init: RequestInit & { duplex?: string } = {
			method: event.request.method,
			headers
		};
		if (event.request.method !== 'GET' && event.request.method !== 'HEAD') {
			init.body = await event.request.arrayBuffer();
			(init as unknown as { duplex: string }).duplex = 'half';
		}

		const upstream = await fetch(target, init);
		const body = await upstream.arrayBuffer();
		const resHeaders = new Headers();
		const uct = upstream.headers.get('content-type');
		if (uct) resHeaders.set('content-type', uct);
		return new Response(body, { status: upstream.status, headers: resHeaders });
	}

	// Re-implement SvelteKit's built-in CSRF check (disabled in svelte.config.js)
	// for every other route. Logic mirrors @sveltejs/kit runtime: form POST
	// with missing or non-trusted Origin is forbidden.
	if (csrfForbidden(event.request, event.url)) {
		const msg = `Cross-site ${event.request.method} form submissions are forbidden`;
		if (event.request.headers.get('accept') === 'application/json') {
			return new Response(JSON.stringify({ message: msg }), {
				status: 403,
				headers: { 'content-type': 'application/json' }
			});
		}
		return new Response(msg, {
			status: 403,
			headers: { 'content-type': 'text/plain' }
		});
	}

	return resolve(event);
};
