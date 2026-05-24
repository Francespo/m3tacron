import { resolveBackendApiBase } from '$lib/server/backend-api';

export async function GET({ url, fetch, request }) {
	const source = url.searchParams.get('data_source') || 'xwa';
	const target = new URL(`${resolveBackendApiBase(url)}/meta-snapshot`);
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
