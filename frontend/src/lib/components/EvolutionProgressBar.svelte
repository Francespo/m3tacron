<script lang="ts">
	let { tiers = [] } = $props();

	function getPercentage(current: number, target: number | null) {
		if (!target) return 100; // Full bar for uncapped or just a different style
		return Math.min(100, (current / target) * 100);
	}
</script>

<div class="space-y-8">
	{#each tiers as tier}
		<div class="group">
			<div class="flex justify-between items-end mb-2">
				<div class="flex-1">
					<h3
						class="text-sm font-mono font-bold text-primary uppercase tracking-widest flex items-center gap-2"
					>
						<span class="w-1.5 h-1.5 bg-primary animate-pulse"
						></span>
						{tier.name}
					</h3>
					<p
						class="text-[11px] text-secondary leading-relaxed max-w-md mt-1 italic"
					>
						{tier.description}
					</p>
				</div>
				<div class="text-right pl-4">
					{#if tier.target}
						<div class="text-xs font-mono text-secondary mb-1">
							PROGRESS
						</div>
						<div class="text-lg font-mono font-bold leading-none">
							{getPercentage(tier.current, tier.target).toFixed(
								1,
							)}<span class="text-xs text-secondary/60 ml-0.5"
								>%</span
							>
						</div>
					{/if}
				</div>
			</div>

			{#if tier.target}
				<div class="relative">
					<!-- Background track -->
					<div
						class="h-3 w-full bg-terminal-panel border border-border-dark overflow-hidden"
					>
						<!-- Progress fill -->
						<div
							class="h-full bg-primary relative transition-all duration-1000 ease-out"
							style="width: {getPercentage(
								tier.current,
								tier.target,
							)}%"
						>
							<!-- Scanning line effect -->
							<div
								class="absolute inset-y-0 right-0 w-px bg-white shadow-[0_0_10px_rgba(255,255,255,0.8)] z-10"
							></div>
							<!-- Subtle inner glow -->
							<div
								class="absolute inset-0 bg-gradient-to-r from-white/5 to-white/20"
							></div>
						</div>
					</div>

					<!-- Amount labels -->
					<div class="flex justify-between mt-1.5">
						<span
							class="text-[10px] font-mono text-secondary/60 tracking-tighter uppercase italic"
						>
							Sustainability Goal
						</span>
						<span
							class="text-[10px] font-mono text-primary font-bold"
						>
							{tier.current.toFixed(0)}€
							<span class="text-secondary/40 mx-1">/</span>
							{tier.target.toFixed(0)}€
						</span>
					</div>
				</div>
			{:else}
				<div
					class="mt-2 p-4 border border-border-dark/30 bg-terminal-panel/30 flex items-center justify-between"
				>
					<span
						class="text-xs font-mono text-secondary/60 uppercase tracking-widest"
					>
						Monthly Pot
					</span>
					<div class="text-2xl font-mono font-bold text-primary">
						{tier.current.toFixed(0)}€
						<span
							class="text-[10px] text-secondary/40 font-normal tracking-widest ml-2 block sm:inline"
							>THIS MONTH</span
						>
					</div>
				</div>
			{/if}
		</div>
	{/each}
</div>

<style>
	/* Subtle flicker for the terminal feel */
	@keyframes flicker {
		0% {
			opacity: 0.95;
		}
		5% {
			opacity: 1;
		}
		10% {
			opacity: 0.9;
		}
		15% {
			opacity: 1;
		}
		80% {
			opacity: 1;
		}
		85% {
			opacity: 0.95;
		}
		90% {
			opacity: 1;
		}
		100% {
			opacity: 0.95;
		}
	}

	.animate-pulse {
		animation: flicker 2s infinite;
	}
</style>
