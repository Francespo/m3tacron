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
	class="relative bg-terminal-bg min-h-screen text-primary overflow-x-hidden"
>
	<!-- Desktop Sidebar (md+) -->
	<Sidebar />

	<!-- Mobile chrome (<md). Both are md:hidden internally, so mounting
	     them unconditionally is safe; the desktop sidebar is unaffected. -->
	<MobileTopBar onOpenNav={() => (navOpen = true)} />
	<MobileNavDrawer bind:open={navOpen} />

	<!-- Main Content Area -->
	<div
		class="md:ml-[260px] min-h-screen transition-all duration-200 relative"
	>
		<!-- Global glow logic can be ported here eventually, placing a vignette wrapper -->
		<div
			class="absolute top-0 right-0 bottom-0 pointer-events-none opacity-30 bg-gradient-to-l from-blue-900/10 to-transparent w-1/4"
		></div>
		<div
			class="absolute bottom-0 left-0 right-0 pointer-events-none opacity-30 bg-gradient-to-t from-blue-900/10 to-transparent h-1/4"
		></div>

		<!-- Slot renders the specific route +page.svelte -->
		{@render children()}
	</div>
</div>
