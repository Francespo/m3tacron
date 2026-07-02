/** @param {*} raw */
function normalizeBackendApiBase(raw) {
	const trimmed = String(raw || '').trim().replace(/\/+$/, '');
	return trimmed.endsWith('/api') ? trimmed : `${trimmed}/api`;
}

function resolvePreviewBackendApiBase(requestUrl) {
	try {
		const host = new URL(requestUrl).hostname;
		const match = host.match(/^(\d+)\.dev\.m3tacron\.com$/);
		if (match) {
			return `https://${match[1]}.api.dev.m3tacron.com/api`;
		}
	} catch {
		// Fall through to the default proxy target.
	}

	return 'http://backend:8888/api';
}

function resolveBackendApiBase() {
	const envBase = process.env.VITE_API_BASE;

	if (!envBase || envBase.startsWith('/')) {
		return null;
	}

	try {
		const parsed = new URL(envBase);
		if (parsed.hostname === 'localhost' || parsed.hostname === '127.0.0.1') {
			return null;
		}
		return normalizeBackendApiBase(envBase);
	} catch {
		return null;
	}
}

/** @type {import('./$types').RequestHandler} */
export async function GET({ params, url, fetch, request }) {
	const path = params.path || '';
	const backendBase = resolveBackendApiBase() || resolvePreviewBackendApiBase(request.url);
	const target = new URL(`${backendBase}/${path}`);

	for (const [key, value] of url.searchParams.entries()) {
		target.searchParams.append(key, value);
	}

	const upstream = await fetch(target.toString(), {
		method: 'GET',
		headers: {
			accept: request.headers.get('accept') || 'application/json'
		}
	});

	const body = await upstream.arrayBuffer();
	const headers = new Headers();
	const contentType = upstream.headers.get('content-type');
	if (contentType) headers.set('content-type', contentType);

	return new Response(body, {
		status: upstream.status,
		headers
	});
}
