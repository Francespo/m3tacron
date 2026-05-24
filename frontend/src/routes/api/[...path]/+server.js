import { resolveBackendApiBase } from '$lib/server/backend-api';

/** @type {import('./$types').RequestHandler} */
export async function GET({ params, url, fetch, request }) {
	const path = params.path || '';
	const target = new URL(`${resolveBackendApiBase(url)}/${path}`);

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
