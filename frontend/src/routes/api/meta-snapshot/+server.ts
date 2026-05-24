import { resolveBackendApiBase } from '$lib/server/backend-api';

export async function GET({ url }) {
	const source = url.searchParams.get('data_source') || 'xwa';
	const target = new URL(`${resolveBackendApiBase(url)}/meta-snapshot`);
	target.searchParams.set('data_source', source);

	return Response.redirect(target.toString(), 307);
}
