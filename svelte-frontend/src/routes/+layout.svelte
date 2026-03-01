<script lang="ts">
	import "../app.css"; // Global Tailwind + Fonts
	import Sidebar from "$lib/components/Sidebar.svelte";
	import type { Snippet } from 'svelte';

	let { children }: { children: Snippet } = $props();
</script>

<div
	class="relative bg-terminal-bg min-h-screen text-primary overflow-x-hidden"
>
	<!-- Desktop Sidebar -->
	<Sidebar />

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
