<script lang="ts">
	type Supporter = { name: string; message?: string | null };
	let { supporters = [] }: { supporters: Supporter[] } = $props();
</script>

<div class="flex flex-wrap justify-center gap-3">
	{#each supporters as supporter}
		<div
			class="relative flex min-h-[64px] w-[calc(50%-6px)] flex-col items-center justify-center gap-1.5 overflow-hidden rounded-xl border border-primary/10 bg-black/80 px-4 py-4 text-center backdrop-blur-sm sm:w-[calc(33.333%-8px)] lg:w-[calc(25%-9px)] xl:w-[calc(20%-9.6px)] max-w-[220px] flex-none"
		>
			<span
				class="block w-full truncate text-xs font-mono font-bold uppercase tracking-tight text-primary"
				title={supporter.name}
			>
				{supporter.name}
			</span>
			{#if supporter.message}
				<p
					class="line-clamp-3 w-full text-[11px] italic leading-snug text-white/80"
					title={supporter.message}
				>
					<span class="text-primary/40">"</span>{supporter.message}<span class="text-primary/40">"</span>
				</p>
			{/if}
		</div>
	{:else}
		<div
			class="flex w-full flex-col items-center justify-center rounded-xl border border-dashed border-border-dark/40 bg-terminal-panel/20 py-12"
		>
			<p
				class="mb-2 text-xs font-mono uppercase tracking-[0.3em] text-secondary/40"
			>
				Awaiting the First Heroes
			</p>
			<p class="text-[10px] italic text-secondary/20">
				"Help me, Obi-Wan Kenobi, you are my only hope"
			</p>
		</div>
	{/each}
</div>

<style>
	.flex > div:not(.w-full)::after {
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
