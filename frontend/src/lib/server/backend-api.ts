function normalizeBackendApiBase(raw: string): string {
	const trimmed = raw.trim().replace(/\/+$/, '');
	return trimmed.endsWith('/api') ? trimmed : `${trimmed}/api`;
}

function isLocalHostname(hostname: string): boolean {
	return (
		hostname === 'localhost' ||
		hostname === '127.0.0.1' ||
		hostname === '0.0.0.0' ||
		/^10\./.test(hostname) ||
		/^127\./.test(hostname) ||
		/^192\.168\./.test(hostname) ||
		/^172\.(1[6-9]|2\d|3[0-1])\./.test(hostname)
	);
}

function resolvePreviewBackendBase(hostname: string): string | null {
	const previewMatch = hostname.match(/^(\d+)\.dev\.m3tacron\.com$/i);
	if (!previewMatch) {
		return null;
	}

	return `https://${previewMatch[1]}.api.dev.m3tacron.com/api`;
}

export function resolveBackendApiBase(requestUrl?: URL): string {
	const envBase = process.env.VITE_API_BASE;

	if (envBase && !envBase.startsWith('/')) {
		try {
			const parsed = new URL(envBase);
			if (!isLocalHostname(parsed.hostname)) {
				return normalizeBackendApiBase(envBase);
			}
		} catch {
			// Ignore malformed env values and fall back to request-derived hosts.
		}
	}

	if (requestUrl) {
		const previewBase = resolvePreviewBackendBase(requestUrl.hostname);
		if (previewBase) {
			return previewBase;
		}
	}

	return 'http://backend:8888/api';
}
