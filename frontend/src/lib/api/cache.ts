/**
 * Client-side GET dedup + short-TTL cache for API calls.
 *
 * Two layers, both keyed by the exact URL string:
 *  1. In-flight dedup: concurrent identical GETs share a single network
 *     request (same URL -> same promise).
 *  2. TTL cache: successful GET responses are memoized for `ttlMs`
 *     (default 30s), bounded to MAX_ENTRIES entries with oldest-first
 *     eviction.
 *
 * Rules:
 *  - Only on the client (`browser`); on the server we plain-fetch.
 *  - Only GET requests with no body. Requests carrying an AbortSignal
 *    bypass both cache and dedup (an abortable request must always hit
 *    the network so it can actually be cancelled).
 *
 * Dependency-free; the parsed JSON is what gets cached (never a Response
 * object, which is single-consumer).
 */
import { browser } from '$app/environment';

const DEFAULT_TTL_MS = 30_000;
const MAX_ENTRIES = 200;

const inFlight = new Map<string, Promise<any>>();
const cache = new Map<string, { value: any; expires: number }>();

function isCacheable(init?: RequestInit): boolean {
    if (init?.signal) return false;
    const method = (init?.method ?? 'GET').toUpperCase();
    if (method !== 'GET') return false;
    return init?.body == null;
}

async function rawFetchJson(url: string, signal?: AbortSignal): Promise<any> {
    const res = await fetch(url, { signal });
    if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(
            `HTTP error! status: ${res.status}, Details: ${errData.error || 'unknown'}`,
        );
    }
    return res.json();
}

function evictOldest(): void {
    const oldest = cache.keys().next().value;
    if (oldest !== undefined) cache.delete(oldest);
}

/**
 * Fetch + parse JSON with in-flight dedup and a short TTL cache.
 *
 * `ttlMs` defaults to 30s. Pass a negative `ttlMs` to read through the
 * cache (skip the TTL) but still re-fetch. Pass an `AbortSignal` to bypass
 * cache/dedup entirely and get a cancellable network request.
 */
export async function cachedFetchJson(
    url: string,
    ttlMs: number = DEFAULT_TTL_MS,
    signal?: AbortSignal,
): Promise<any> {
    // Abortable requests must hit the network; the server has no shared cache.
    if (!browser || signal) {
        return rawFetchJson(url, signal);
    }

    // In-flight dedup: concurrent identical fetches share one request.
    const pending = inFlight.get(url);
    if (pending) return pending;

    const hit = cache.get(url);
    if (hit && hit.expires > Date.now()) return hit.value;

    const request = rawFetchJson(url)
        .then((value) => {
            cache.set(url, { value, expires: Date.now() + ttlMs });
            if (cache.size > MAX_ENTRIES) evictOldest();
            return value;
        })
        .finally(() => {
            inFlight.delete(url);
        });
    inFlight.set(url, request);
    return request;
}

/**
 * Response-style wrapper around `cachedFetchJson` for callers that expect a
 * `Response`. Only GET/no-body/no-signal requests are cached; everything
 * else passes straight through to `fetch`.
 */
export async function cachedFetch(
    url: string,
    init?: RequestInit,
    ttlMs: number = DEFAULT_TTL_MS,
): Promise<Response> {
    if (!browser || !isCacheable(init)) {
        return fetch(url, init);
    }
    const data = await cachedFetchJson(url, ttlMs);
    return new Response(JSON.stringify(data), {
        status: 200,
        headers: { 'content-type': 'application/json' },
    });
}

/** Drop all cached responses and pending in-flight dedup entries. */
export function clearApiCache(): void {
    cache.clear();
    inFlight.clear();
}
