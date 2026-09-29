/**
 * First-party, cookie-less page-view tracking.
 *
 * Sends one anonymous event per page view to `POST {API_BASE}/analytics/collect`.
 * Nothing that identifies a person is stored: no IP, no user agent, no cookie,
 * and only the external referrer *host* is reported. The backend flags
 * automated clients and every report separates them from human traffic.
 *
 * Disabled outside the production hosts, when `PUBLIC_ANALYTICS_ENABLED=false`,
 * and when the browser asks not to be tracked (DNT / Global Privacy Control).
 *
 * See docs/ANALYTICS.md.
 */
import { browser } from '$app/environment';
import { env as publicEnv } from '$env/dynamic/public';
import { API_BASE } from '$lib/api';

const DEFAULT_HOSTS = 'm3tacron.com,www.m3tacron.com';
const VISITOR_KEY = 'm3.analytics.visitor';
const SESSION_KEY = 'm3.analytics.session';
const SESSION_IDLE_MS = 30 * 60 * 1000;
const DEDUPE_MS = 1000;

let lastPath = '';
let lastSentAt = 0;

function randomId(): string {
	if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') {
		return crypto.randomUUID();
	}
	return `v-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 12)}`;
}

function allowedHosts(): string[] {
	const raw = publicEnv.PUBLIC_ANALYTICS_HOSTS ?? DEFAULT_HOSTS;
	return raw
		.split(',')
		.map((host) => host.trim().toLowerCase())
		.filter(Boolean);
}

function enabledByEnv(): boolean {
	const raw = String(publicEnv.PUBLIC_ANALYTICS_ENABLED ?? 'true').trim().toLowerCase();
	return !['false', '0', 'off', 'no'].includes(raw);
}

/** True when this browser may send events. Safe to call during SSR. */
export function trackingEnabled(): boolean {
	if (!browser || !enabledByEnv()) return false;
	if (!allowedHosts().includes(window.location.hostname.toLowerCase())) return false;

	const nav = window.navigator as Navigator & { globalPrivacyControl?: boolean };
	if (nav.doNotTrack === '1' || nav.globalPrivacyControl === true) return false;

	return true;
}

function readStorage(storage: Storage, key: string): string | null {
	try {
		return storage.getItem(key);
	} catch {
		return null; // storage blocked (private mode / cookie policy)
	}
}

function writeStorage(storage: Storage, key: string, value: string): void {
	try {
		storage.setItem(key, value);
	} catch {
		/* analytics is best-effort: ignore storage failures */
	}
}

function visitorId(): string {
	let id = readStorage(window.localStorage, VISITOR_KEY);
	if (!id) {
		id = randomId();
		writeStorage(window.localStorage, VISITOR_KEY, id);
	}
	return id;
}

function sessionId(): string {
	const now = Date.now();
	const raw = readStorage(window.sessionStorage, SESSION_KEY);
	if (raw) {
		const [id, seenAt] = raw.split('|');
		if (id && seenAt && now - Number(seenAt) < SESSION_IDLE_MS) {
			writeStorage(window.sessionStorage, SESSION_KEY, `${id}|${now}`);
			return id;
		}
	}

	const id = randomId();
	writeStorage(window.sessionStorage, SESSION_KEY, `${id}|${now}`);
	return id;
}

function externalReferrerHost(): string | null {
	if (!document.referrer) return null;
	try {
		const host = new URL(document.referrer).hostname.toLowerCase();
		return host === window.location.hostname.toLowerCase() ? null : host;
	} catch {
		return null;
	}
}

/** Record one page view. Never throws and never blocks the page. */
export function trackPageView(path: string): void {
	if (!trackingEnabled()) return;

	// `afterNavigate` runs on mount and on every client-side navigation; the
	// dedupe guard keeps a remount of the same route from double-counting.
	const now = Date.now();
	if (path === lastPath && now - lastSentAt < DEDUPE_MS) return;
	lastPath = path;
	lastSentAt = now;

	const body = JSON.stringify({
		path,
		host: window.location.hostname,
		visitor_id: visitorId(),
		session_id: sessionId(),
		referrer_host: externalReferrerHost(),
	});

	void fetch(`${API_BASE}/analytics/collect`, {
		method: 'POST',
		headers: { 'Content-Type': 'application/json' },
		body,
		keepalive: true,
		credentials: 'omit',
		mode: 'cors',
	}).catch(() => {
		/* analytics must never affect the user's page */
	});
}
