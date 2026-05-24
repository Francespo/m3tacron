function normalizeBackendApiBase(raw: string | undefined) {
	const trimmed = String(raw || '').trim().replace(/\/+$/, '');
	return trimmed.endsWith('/api') ? trimmed : `${trimmed}/api`;
}

function resolveBackendApiBase() {
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

export async function GET({ url, fetch, request }) {
	const source = url.searchParams.get('data_source') || 'xwa';
	const target = new URL(`${BACKEND_API_BASE}/meta-snapshot`);
	target.searchParams.set('data_source', source);

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
