import type { Handle } from '@sveltejs/kit';

// Bypass SvelteKit's CSRF origin check for the Ko-fi webhook.
// Ko-fi sends a server-to-server POST with no Origin/Sec-Fetch-Site,
// so kit.csrf.checkOrigin would block it even though verification_token
// already authenticates the request. We proxy it directly to the backend
// without going through SvelteKit's CSRF-protected resolve().
export const handle: Handle = async ({ event, resolve }) => {
	if (event.url.pathname.startsWith('/api/support/webhook/')) {
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

	return resolve(event);
};
