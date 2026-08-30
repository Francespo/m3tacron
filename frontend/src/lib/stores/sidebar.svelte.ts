/**
 * Sidebar Collapse Preference.
 *
 * UI-preference store for the desktop navigation sidebar (collapsible rail).
 * Separate from filter preference stores: it controls whether the left nav
 * shows full labels (260px) or icon-only (72px).
 *
 * SSR-safe: localStorage guarded, lazy-loaded on first access.
 */
const STORAGE_KEY = "m3tacron:sidebar:collapsed";

let collapsedById: Record<string, boolean> = $state({});
let loaded = $state(false);

function readSaved(): boolean | null {
	if (typeof localStorage === "undefined") return null;
	try {
		const raw = localStorage.getItem(STORAGE_KEY);
		if (raw === null) return null;
		return raw === "1";
	} catch {
		return null;
	}
}

function ensureLoaded(): void {
	if (loaded) return;
	loaded = true;
	const saved = readSaved();
	collapsedById["sidebar"] = saved ?? false;
}

function isCollapsed(): boolean {
	return collapsedById["sidebar"] ?? false;
}

function setCollapsed(collapsed: boolean): void {
	collapsedById["sidebar"] = collapsed;
	if (typeof localStorage === "undefined") return;
	try {
		localStorage.setItem(STORAGE_KEY, collapsed ? "1" : "0");
	} catch {
		// non-fatal
	}
}

function toggle(): void {
	setCollapsed(!isCollapsed());
}

export const sidebarStore = {
	ensureLoaded,
	isCollapsed,
	setCollapsed,
	toggle,
};
