<script lang="ts">
	let { supporters = [] }: { supporters: { name: string }[] } = $props();
</script>

<div class="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 relative">
	{#each supporters as supporter}
		<div
			class="relative rounded-xl border border-primary/10 bg-black/80 px-4 py-3 text-center backdrop-blur-sm overflow-hidden"
		>
			<span
				class="block truncate text-xs font-mono font-bold uppercase tracking-tight text-primary"
				title={supporter.name}
			>
				{supporter.name}
			</span>
		</div>
	{:else}
		<div
			class="col-span-full flex flex-col items-center justify-center rounded-xl border border-dashed border-border-dark/40 bg-terminal-panel/20 py-16"
		>
			<p
				class="mb-2 text-xs font-mono uppercase tracking-[0.3em] text-secondary/40"
			>
				Awaiting the First Heroes
			</p>
			<p class="text-[10px] italic text-secondary/20">
				The records are empty, but the future is bright.
			</p>
		</div>
	{/each}
</div>

<style>
	/* Subtle scanline overlay for the cards */
	.grid > div:not(.col-span-full)::after {
		content: "";
		position: absolute;
		top: 0;
		left: 0;
		width: 100%;
		height: 100%;
		background: linear-gradient(
				rgba(18, 16, 16, 0) 50%,
				rgba(0, 0, 0, 0.05) 50%
			),
			linear-gradient(
				90deg,
				rgba(255, 0, 0, 0.01),
				rgba(0, 255, 0, 0.005),
				rgba(0, 0, 255, 0.01)
			);
		background-size:
			100% 3px,
			3px 100%;
		pointer-events: none;
		z-index: 5;
		opacity: 0.3;
	}
</style>
