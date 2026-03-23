/**
 * Centralized API configuration.
 * Change the base URL here to affect all API calls.
 */
function normalizeApiBase(rawBase: string): string {
	const trimmed = rawBase.replace(/\/+$/, '');
	return trimmed.endsWith('/api') ? trimmed : `${trimmed}/api`;
}

const envApiBase = import.meta.env.VITE_API_BASE as string | undefined;

// Browser requests should target the same host on backend port 8888.
// Server-side requests (inside Docker) should target the backend service directly.
const fallbackBase =
	typeof window !== 'undefined'
		? `${window.location.protocol}//${window.location.hostname}:8888`
		: 'http://backend:8888';

let resolvedBase = envApiBase || fallbackBase;

if (typeof window !== 'undefined' && envApiBase) {
	try {
		const parsed = new URL(envApiBase);
		const isLocalEnvHost = parsed.hostname === 'localhost' || parsed.hostname === '127.0.0.1';
		const isBrowserLocalHost = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';

		if (isLocalEnvHost && !isBrowserLocalHost) {
			resolvedBase = fallbackBase;
		}
	} catch {
		resolvedBase = fallbackBase;
	}
}

export const API_BASE = normalizeApiBase(resolvedBase);
