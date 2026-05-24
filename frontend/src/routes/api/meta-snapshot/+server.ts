import { resolveBackendApiBase } from '$lib/server/backend-api';

export async function GET({ url }) {
	try {
		const source = url.searchParams.get('data_source') || 'xwa';
		const target = new URL(`${resolveBackendApiBase(url)}/meta-snapshot`);
		target.searchParams.set('data_source', source);

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
