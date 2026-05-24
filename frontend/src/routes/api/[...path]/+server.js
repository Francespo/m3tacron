import { resolveBackendApiBase } from '$lib/server/backend-api';

/** @type {import('./$types').RequestHandler} */
export async function GET({ params, url }) {
	const path = params.path || '';
	const target = new URL(`${resolveBackendApiBase(url)}/${path}`);

	for (const [key, value] of url.searchParams.entries()) {
		target.searchParams.append(key, value);
	}

	return Response.redirect(target.toString(), 307);
}
