<script lang="ts">
	/**
	 * MobileFilterTrigger
	 *
	 * Floating Action Button that opens MobileFilterDrawer. Visible <lg,
	 * hidden lg+ (the desktop FilterPanel takes over there). Parent is
	 * responsible for mounting it only on <lg and wiring onClick to its
	 * own open state.
	 *
	 * Note for integrators: this FAB is `fixed bottom-4 right-4`, so any
	 * page-level content that extends to the bottom of the viewport
	 * should add `pb-20` (or similar) to its main scroll container,
	 * otherwise the last list rows will be obscured by the button.
	 */
	type Props = {
		activeCount: number;
		onClick: () => void;
	};

	let { activeCount, onClick }: Props = $props();
</script>

<button
	type="button"
	onclick={onClick}
	aria-label="Open filters{activeCount > 0 ? ` (${activeCount} active)` : ''}"
	class="fixed bottom-4 right-4 z-[45] flex items-center gap-2 h-12 pl-3 pr-4 rounded-full bg-terminal-panel border border-primary/40 text-primary shadow-lg shadow-black/60 hover:bg-[#ffffff08] hover:border-primary active:bg-[#ffffff14] transition-colors focus-visible:outline-2 focus-visible:outline-primary focus-visible:outline-offset-2 lg:hidden"
>
	<!-- Filter icon (3 lines, tapering — the standard "funnel" mark, drawn
	     in strokes only so it matches the other UI icons). -->
	<svg
		xmlns="http://www.w3.org/2000/svg"
		width="20"
		height="20"
		viewBox="0 0 24 24"
		fill="none"
		stroke="currentColor"
		stroke-width="2"
		stroke-linecap="round"
		stroke-linejoin="round"
		aria-hidden="true"
	>
		<polygon points="3 4 21 4 14 12.5 14 19 10 21 10 12.5 3 4"></polygon>
	</svg>

	<span class="text-sm font-medium font-sans">Filters</span>

	{#if activeCount > 0}
		<span
			class="shrink-0 inline-flex items-center justify-center min-w-5 h-5 px-1.5 rounded-full text-[10px] font-mono font-bold bg-rebel text-primary"
			aria-hidden="true"
		>
			{activeCount}
		</span>
	{/if}
</button>
