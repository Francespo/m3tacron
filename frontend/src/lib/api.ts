/**
 * Centralized API configuration.
 * Change the base URL here to affect all API calls.
 */
function normalizeApiBase(rawBase: string): string {
	const trimmed = rawBase.trim().replace(/\/+$/, '');

	if (!trimmed || trimmed === '/') {
		return '/api';
	}

	if (trimmed === '/api' || trimmed.endsWith('/api')) {
		return trimmed;
	}

	if (trimmed.startsWith('/')) {
		return `${trimmed}/api`;
	}

	return `${trimmed}/api`;
}

const envApiBase = import.meta.env.VITE_API_BASE as string | undefined;
const fallbackBase = '/api';

function isPrivateIp(hostname: string): boolean {
	return (
		/^10\./.test(hostname) ||
		/^127\./.test(hostname) ||
		/^192\.168\./.test(hostname) ||
		/^172\.(1[6-9]|2\d|3[0-1])\./.test(hostname)
	);
}

function isLikelyInternalHost(hostname: string): boolean {
	const host = hostname.toLowerCase();

	if (host === 'localhost' || host === '127.0.0.1' || host === '0.0.0.0') {
		return true;
	}

	if (isPrivateIp(host)) {
		return true;
	}

	// Docker/Kubernetes service names are often bare hosts without dots.
	if (!host.includes('.')) {
		return true;
	}

	return false;
}

function resolveApiBase(): string {
	if (!envApiBase) {
		return fallbackBase;
	}

	// Allow path-style overrides like "/backend".
	if (envApiBase.startsWith('/')) {
		return normalizeApiBase(envApiBase);
	}

	try {
		const parsed = new URL(envApiBase);
		const envHost = parsed.hostname.toLowerCase();
		const isLocalEnvHost = envHost === 'localhost' || envHost === '127.0.0.1';

		// In deployed environments, localhost targets are almost always invalid.
		if (isLocalEnvHost) {
			if (typeof window === 'undefined') {
				return fallbackBase;
			}

			const isBrowserLocalHost =
				window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
			if (!isBrowserLocalHost) {
				return fallbackBase;
			}
		}

		if (typeof window !== 'undefined') {
			const browserHost = window.location.hostname.toLowerCase();

			// If env points to an internal-only host that differs from the public browser host,
			// use same-origin /api so reverse-proxy routing keeps working.
			if (envHost !== browserHost && isLikelyInternalHost(envHost)) {
				return fallbackBase;
			}
		}

		return normalizeApiBase(envApiBase);
	} catch {
		return fallbackBase;
	}
}

export const API_BASE = resolveApiBase();
