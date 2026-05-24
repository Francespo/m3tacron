import { resolveBackendApiBase } from '$lib/server/backend-api';

/** @type {import('./$types').RequestHandler} */
export async function GET({ params, url }) {
	try {
		const path = params.path || '';
		const target = new URL(`${resolveBackendApiBase(url)}/${path}`);

		for (const [key, value] of url.searchParams.entries()) {
			target.searchParams.append(key, value);
		}

		return Response.redirect(target.toString(), 307);
	} catch (error) {
		return new Response(
			JSON.stringify({
				error: error instanceof Error ? error.message : String(error)
			}),
			{
				status: 500,
				headers: {
					'content-type': 'application/json'
				}
			}
		);
	}
}
