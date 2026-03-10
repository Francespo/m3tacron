<script lang="ts">
	let { supporters = [] } = $props();

	function formatDate(dateStr: string) {
		const date = new Date(dateStr);
		return date
			.toLocaleDateString("en-US", {
				year: "numeric",
				month: "short",
				day: "numeric",
			})
			.toUpperCase();
	}
</script>

<div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
	{#each supporters as supporter}
		<div class="relative group">
			<!-- Terminal card border effect -->
			<div
				class="absolute -inset-[0.5px] bg-border-dark group-hover:bg-primary/20 transition-colors duration-300"
			></div>

			<div
				class="relative h-full p-4 bg-terminal-panel/80 backdrop-blur-sm flex flex-col justify-between overflow-hidden"
			>
				<!-- Corner accent -->
				<div
					class="absolute top-0 right-0 w-6 h-6 border-t border-r border-border-dark opacity-40"
				></div>

				<div>
					<div class="flex justify-between items-start mb-3">
						<h4
							class="text-xs font-mono font-bold tracking-tight text-primary uppercase line-clamp-1"
						>
							{supporter.name}
						</h4>
						<span
							class="text-[9px] font-mono text-secondary/50 shrink-0 ml-2"
						>
							{formatDate(supporter.date)}
						</span>
					</div>

					{#if supporter.message}
						<div class="mb-4 relative">
							<span
								class="absolute -left-2 top-0 text-primary/20 text-lg font-serif"
								>"</span
							>
							<p
								class="text-[11px] text-secondary leading-relaxed italic line-clamp-3"
							>
								{supporter.message}
							</p>
							<span
								class="absolute -right-1 bottom-0 text-primary/20 text-lg font-serif"
								>"</span
							>
						</div>
					{:else}
						<div
							class="h-8 flex items-center justify-center border border-dashed border-border-dark/30 mb-4"
						>
							<span
								class="text-[9px] text-secondary/20 font-mono uppercase tracking-[0.2em]"
								>Silent Hero</span
							>
						</div>
					{/if}
				</div>

				<div
					class="pt-3 border-t border-border-dark/50 flex items-center justify-between mt-auto"
				>
					<span
						class="text-[10px] uppercase text-secondary/40 font-mono tracking-widest"
						>Confirmed Contribution</span
					>
					<span class="text-xs font-mono text-primary font-bold">
						{supporter.amount.toFixed(2)}<span
							class="text-[10px] text-secondary/60">€</span
						>
					</span>
				</div>
			</div>
		</div>
	{:else}
		<div
			class="col-span-full py-20 flex flex-col items-center justify-center border border-dashed border-border-dark/40 bg-terminal-panel/20"
		>
			<p
				class="text-xs font-mono text-secondary/40 uppercase tracking-[0.3em] mb-2"
			>
				Awaiting the First Heroes
			</p>
			<p class="text-[10px] text-secondary/20 italic">
				The records are empty, but the future is bright.
			</p>
		</div>
	{/each}
</div>

<style>
	/* Subtle scanline overlay for the cards */
	.relative::after {
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
