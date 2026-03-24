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
		const isLocalEnvHost = parsed.hostname === 'localhost' || parsed.hostname === '127.0.0.1';

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

		return normalizeApiBase(envApiBase);
	} catch {
		return fallbackBase;
	}
}

export const API_BASE = resolveApiBase();
