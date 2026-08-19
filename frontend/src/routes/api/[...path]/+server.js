/** @param {*} raw */
function normalizeBackendApiBase(raw) {
	const trimmed = String(raw || '').trim().replace(/\/+$/, '');
	return trimmed.endsWith('/api') ? trimmed : `${trimmed}/api`;
}

function previewBackendHost() {
	// PR-specific backend containers are reachable as `backend-pr-<N>` on the
	// shared coolify network. The generic `backend` alias belongs to the old
	// shared backend, so previews must target their own container.
	// COOLIFY_BRANCH is like `pull/131/head` but Coolify quotes the value
	// (e.g. `"pull/131/head"`), so strip any surrounding quotes first.
	const branch = String(process.env.COOLIFY_BRANCH || '').replace(/^"|"$/g, '');
	const fromBranch = branch.match(/^pull\/(\d+)/);
	if (fromBranch) {
		return `backend-pr-${fromBranch[1]}`;
	}
	return null;
}

function resolvePreviewBackendApiBase(requestUrl) {
	try {
		const host = new URL(requestUrl).hostname;
		const match = host.match(/^(\d+)\.dev\.m3tacron\.com$/);
		if (match) {
			// Preview deployment - talk directly to local backend container via docker network
			return `http://backend-pr-${match[1]}:8888/api`;
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
	// Preview deployments: always use internal Docker network to reach backend
	const isPreview = process.env.ENV_VAR_SOURCE === 'preview' || (process.env.COOLIFY_BRANCH || '').startsWith('pull/');
	const previewHost = isPreview ? previewBackendHost() : null;
	const backendBase = previewHost ? `http://${previewHost}:8888/api` : (resolveBackendApiBase() || resolvePreviewBackendApiBase(request.url));
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
