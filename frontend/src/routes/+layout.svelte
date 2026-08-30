<script lang="ts">
	import "../app.css"; // Global Tailwind + Fonts
	import Sidebar from "$lib/components/Sidebar.svelte";
	import MobileTopBar from "$lib/components/MobileTopBar.svelte";
	import MobileNavDrawer from "$lib/components/MobileNavDrawer.svelte";
	import PendingIndicator from "$lib/components/PendingIndicator.svelte";
	import { untrack, type Snippet } from "svelte";
	import { page } from "$app/state";
	import {
		onNavigate,
		beforeNavigate,
		afterNavigate,
	} from "$app/navigation";
	import { filters } from "$lib/stores/filters.svelte";
	import { sidebarStore } from "$lib/stores/sidebar.svelte";
	import { clearPendingSync } from "$lib/sync/urlSync.svelte";

	let { children }: { children: Snippet } = $props();

	// Global navigation progress: a thin bar across the top of the viewport
	// that appears only when a navigation actually takes noticeable time
	// (sidebar links, pagination, tab switches, filter-driven `goto`s) and
	// hides the moment the new route is interactive. Fast navigations finish
	// before the show-delay elapses, so the bar never flashes for them. On
	// streamed loads the navigation completes as soon as the page shell is
	// ready, so the route's own PendingIndicator keeps the "still updating"
	// state visible after this bar hides.
	const SHOW_DELAY_MS = 350;
	let navActive = $state(false);
	let navShowTimer: ReturnType<typeof setTimeout> | null = null;
	let navSafetyTimer: ReturnType<typeof setTimeout> | null = null;

	beforeNavigate(() => {
		// Reset any previous timer
		if (navShowTimer !== null) clearTimeout(navShowTimer);
		if (navSafetyTimer !== null) clearTimeout(navSafetyTimer);

		// Arm the show timer — if navigation finishes before 350ms,
		// afterNavigate will cancel this and the bar will never render.
		navShowTimer = setTimeout(() => {
			navActive = true;
			navShowTimer = null;
		}, SHOW_DELAY_MS);

		// Safety cap: if an upstream endpoint hangs indefinitely, drop the
		// progress bar after 8 seconds so the UI never looks permanently
		// stuck.
		navSafetyTimer = setTimeout(() => {
			navActive = false;
			navSafetyTimer = null;
		}, 8000);
	});

	afterNavigate(() => {
		// Navigation finished. Fast routes clear the pending timer and
		// never show it, and slow ones disappear the moment the route is
		// ready (the page-level pending indicators cover any still-streaming
		// loads after this bar hides).
		if (navShowTimer !== null) {
			clearTimeout(navShowTimer);
			navShowTimer = null;
		}
		if (navSafetyTimer !== null) {
			clearTimeout(navSafetyTimer);
			navSafetyTimer = null;
		}
		navActive = false;

		// Every route change must land at the top — scroll is per-page,
		// not global. Without this the main column keeps its scrollTop
		// across navigations (e.g. 80% down on /lists → click a list →
		// /list/[id] already 80% down).
		requestAnimationFrame(() => {
			const scroller = document.querySelector(
				".flex-1.overflow-y-auto",
			) as HTMLElement | null;
			if (scroller) scroller.scrollTop = 0;
			window.scrollTo({ top: 0, left: 0, behavior: "instant" as ScrollBehavior });
			document.documentElement.scrollTop = 0;
			document.body.scrollTop = 0;
		});
	});

	// Mobile-only nav drawer state. Bound to MobileTopBar's hamburger (open)
	// and to MobileNavDrawer's own close handlers (escape / backdrop / route
	// change). The drawer also auto-closes on route change internally, so
	// this stays consistent with that.
	let navOpen = $state(false);

	// Sidebar collapse is a persisted UI preference — hydrate from localStorage
	// once on client mount (SSR-safe: $effect doesn't run on server).
	$effect(() => {
		sidebarStore.ensureLoaded();
	});
	let sidebarCollapsed = $derived(sidebarStore.isCollapsed());

	// Client-only hydration: read filter state from the URL on first
	// client mount. $effect does not run during SSR, so the server
	// renders with the store's default values (no cross-request
	// contamination from a module-level $state singleton).
	$effect(() => {
		const searchParams = page.url.searchParams;
		untrack(() => {
			filters.applyFromSearchParams(searchParams);
		});
	});

	// Cancel any pending debounced URL sync when the user navigates
	// away. Without this, a fast route-switch with a pending 250ms
	// timer would fire goto() to the OLD route, polluting the URL.
	onNavigate(() => {
		clearPendingSync();
	});
</script>

<div
	class="relative bg-terminal-bg h-screen text-primary overflow-hidden flex flex-col"
>
	<!-- Global navigation progress bar: instant feedback for every route
	     change, regardless of how slow the backend query is. -->
	{#if navActive}
		<div class="fixed inset-x-0 top-0 z-[200] h-0.5">
			<PendingIndicator active label="Loading" />
		</div>
	{/if}

	<!-- Desktop Sidebar (md+). Rendered as a fixed-positioned component
	     (see Sidebar.svelte) so it never scrolls with the page. -->
	<Sidebar />

	<!-- Mobile chrome (<md). Both are md:hidden internally, so mounting
	     them unconditionally is safe; the desktop sidebar is unaffected.
	     The flex column above lets the MobileTopBar claim its natural
	     height on small viewports and the main content fill the rest. -->
	<MobileTopBar onOpenNav={() => (navOpen = true)} />
	<MobileNavDrawer bind:open={navOpen} />

	<!-- Main Content Area. flex-1 + overflow-y-auto gives this column its
	     own independent scroll, decoupled from the (already fixed) sidebar
	     and from the outer page. The left margin tracks the sidebar width
	     (260px expanded, 72px collapsed) so the content reflows. -->
	<div
		class="flex-1 overflow-y-auto transition-all duration-200 relative overflow-x-hidden {sidebarCollapsed ? 'md:ml-[72px]' : 'md:ml-[260px]'}"
	>
		<!-- Slot renders the specific route +page.svelte -->
		{@render children()}
	</div>
</div>
