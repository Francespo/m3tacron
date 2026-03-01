/**
 * API fetch utilities.
 *
 * Server-side fetches hit the FastAPI backend directly.
 * The base URL is configurable via env var for production.
 */

import type { MetaSnapshotResponse } from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";

/**
 * Fetch the meta snapshot for a given data source.
 *
 * Called from React Server Components — no CORS issues since it runs on
 * the Node.js server, not the browser.
 */
export async function fetchMetaSnapshot(
    dataSource: "xwa" | "legacy" = "xwa"
): Promise<MetaSnapshotResponse> {
    const url = `${API_BASE}/api/meta-snapshot?data_source=${dataSource}`;

    const res = await fetch(url, { next: { revalidate: 300 } });

    if (!res.ok) {
        throw new Error(`fetchMetaSnapshot failed: ${res.status} ${res.statusText}`);
    }

    return res.json() as Promise<MetaSnapshotResponse>;
}
