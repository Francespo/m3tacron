<script lang="ts">
	type Supporter = { name: string; message?: string | null; isMonthly?: boolean };
	let { supporters = [] }: { supporters: Supporter[] } = $props();
</script>

<div class="flex flex-wrap justify-center gap-3">
	{#each supporters as supporter}
		<div
			class="relative flex min-h-[64px] w-[calc(50%-6px)] flex-col items-center justify-center gap-1.5 overflow-hidden rounded-xl border bg-black/80 px-4 py-4 text-center backdrop-blur-sm sm:w-[calc(33.333%-8px)] lg:w-[calc(25%-9px)] xl:w-[calc(20%-9.6px)] max-w-[220px] flex-none {supporter.isMonthly
				? 'border-amber-400/30 shadow-[0_0_12px_rgba(251,191,36,0.15)]'
				: 'border-primary/10'}"
			title={supporter.isMonthly ? `${supporter.name} — monthly supporter` : supporter.name}
		>
			{#if supporter.isMonthly}
				<!-- Small Rebel starbird-inspired star in the corner for monthly supporters -->
				<span
					class="absolute right-1.5 top-1.5 leading-none text-amber-400/90"
					aria-label="Monthly supporter"
					title="Monthly supporter"
				>
					<svg
						xmlns="http://www.w3.org/2000/svg"
						width="11"
						height="11"
						viewBox="0 0 24 24"
						fill="currentColor"
						stroke="none"
						class="drop-shadow-[0_0_4px_rgba(251,191,36,0.6)]"
						><path d="M12 2l2.4 7.2H22l-6.2 4.5 2.4 7.3L12 16.9 5.8 21l2.4-7.3L2 9.2h7.6z" /></svg
					>
				</span>
			{/if}
			<span
				class="block w-full truncate text-xs font-mono font-bold uppercase tracking-tight {supporter.isMonthly
					? 'text-amber-300'
					: 'text-primary'}"
			>
				{supporter.name}
			</span>
			{#if supporter.isMonthly}
				<span class="text-[8px] font-mono uppercase tracking-[0.2em] text-amber-400/70">monthly</span>
			{/if}
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
