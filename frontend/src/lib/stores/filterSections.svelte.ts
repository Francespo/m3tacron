/**
 * Filter Section Collapse State.
 *
 * UI-preference store backing the collapsible filter sections rendered by
 * `FilterSection.svelte`. Deliberately separate from `filters.svelte.ts`:
 * collapse state is a UI preference, not a filter value, so it never
 * round-trips through the URL and never affects data fetching.
 *
 * A section is identified by a stable string id so the same section can be
 * mounted in multiple DOM regions (e.g. the desktop `FilterPanel` sidebar
 * and the mobile filter drawer) and share one persisted preference.
 *
 * Unlike `filters.svelte.ts` (which is kept pure so it never causes
 * navigation), this store is allowed localStorage side effects — it is
 * UI-preference state. It must NOT import `$app/navigation` and never
 * triggers navigation.
 *
 * SSR-safety: production builds run SSR, so every localStorage access is
 * guarded by `typeof localStorage === "undefined"`; per-id reads are lazy
 * (first access), so sections never visited don't touch storage.
 */

const STORAGE_PREFIX = "m3tacron:filterSection:";

/** id -> whether the section is collapsed. Absent = not loaded yet. */
let collapsedById = $state<Record<string, boolean>>({});

/** ids whose saved preference has already been loaded (non-reactive). */
const loadedIds = new Set<string>();

function storageKey(id: string): string {
    return `${STORAGE_PREFIX}${id}:collapsed`;
}

/** Lazy, SSR-safe read of the persisted preference for one section id. */
function readSaved(id: string): boolean | null {
    if (typeof localStorage === "undefined") return null;
    try {
        const raw = localStorage.getItem(storageKey(id));
        if (raw === null) return null;
        return raw === "1";
    } catch (e) {
        console.warn(`Failed to read filter section preference "${id}"`, e);
        return null;
    }
}

/**
 * Load the saved preference for `id` into the reactive map exactly once.
 * `defaultOpen` seeds the in-memory value when no saved preference exists.
 *
 * IMPORTANT: this writes to the reactive `collapsedById` map and MUST be
 * called outside reactive contexts ($derived / $effect / template
 * expressions) — i.e. at component init. Writing state during a `$derived`
 * evaluation triggers Svelte's `state_unsafe_mutation` guard.
 */
function ensureLoaded(id: string, defaultOpen: boolean): void {
    if (loadedIds.has(id)) return;
    loadedIds.add(id);
    const saved = readSaved(id);
    collapsedById[id] = saved ?? !defaultOpen;
}

/**
 * Read-only collapsed-state lookup. Never writes, so it is safe inside
 * `$derived`. Callers must call `ensureLoaded` first (component init) so
 * the saved preference is already in the reactive map.
 */
function isCollapsed(id: string): boolean {
    return collapsedById[id] ?? false;
}

function setCollapsed(id: string, collapsed: boolean): void {
    collapsedById[id] = collapsed;
    if (typeof localStorage === "undefined") return;
    try {
        localStorage.setItem(storageKey(id), collapsed ? "1" : "0");
    } catch (e) {
        console.warn(`Failed to save filter section preference "${id}"`, e);
    }
}

function toggle(id: string): void {
    setCollapsed(id, !isCollapsed(id));
}

/**
 * Deterministic slug for section ids: lowercase, spaces/non-alphanumerics
 * become dashes, leading/trailing dashes trimmed (e.g. "List filters" ->
 * "list-filters"). Shared by `FilterPanel` and `MobileFilterDrawer` so both
 * derive identical ids from the same `pageFilterTitle`.
 */
export function slugify(label: string): string {
    return label
        .toLowerCase()
        .replace(/[^a-z0-9]+/g, "-")
        .replace(/^-+|-+$/g, "");
}

export const filterSections = {
    ensureLoaded,
    isCollapsed,
    setCollapsed,
    toggle,
};
