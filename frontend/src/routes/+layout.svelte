<script lang="ts">
	import "../app.css"; // Global Tailwind + Fonts
	import Sidebar from "$lib/components/Sidebar.svelte";
	import MobileTopBar from "$lib/components/MobileTopBar.svelte";
	import MobileNavDrawer from "$lib/components/MobileNavDrawer.svelte";
	import type { Snippet } from "svelte";
	import { page } from "$app/state";
	import { onNavigate } from "$app/navigation";
	import { filters } from "$lib/stores/filters.svelte";
	import { clearPendingSync } from "$lib/sync/urlSync.svelte";

	let { children }: { children: Snippet } = $props();

	// Mobile-only nav drawer state. Bound to MobileTopBar's hamburger (open)
	// and to MobileNavDrawer's own close handlers (escape / backdrop / route
	// change). The drawer also auto-closes on route change internally, so
	// this stays consistent with that.
	let navOpen = $state(false);

	// Client-only hydration: read filter state from the URL on first
	// client mount. $effect does not run during SSR, so the server
	// renders with the store's default values (no cross-request
	// contamination from a module-level $state singleton).
	$effect(() => {
		filters.applyFromSearchParams(page.url.searchParams);
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
	     and from the outer page. md:ml-[260px] keeps it clear of the
	     desktop sidebar. -->
	<div
		class="md:ml-[260px] flex-1 overflow-y-auto transition-all duration-200 relative overflow-x-hidden"
	>
		<!-- Slot renders the specific route +page.svelte -->
		{@render children()}
	</div>
</div>
