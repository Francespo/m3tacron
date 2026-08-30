<script lang="ts">
	/**
	 * MobileTopBar
	 *
	 * Sticky top chrome for <md viewports. Sits above page content, below the
	 * nav/filter drawers (which are z-60). The desktop sidebar (z-100, hidden
	 * on <md) is unaffected by this component.
	 */
	let { onOpenNav }: { onOpenNav: () => void } = $props();
</script>

<header
	class="sticky top-0 z-50 w-full bg-terminal-panel/95 backdrop-blur-md border-b border-[#ffffff14] md:hidden"
>
	<div class="flex items-center h-14 px-2.5 gap-2">
		<button
			type="button"
			onclick={onOpenNav}
			aria-label="Open navigation menu"
			class="shrink-0 flex items-center justify-center w-10 h-10 rounded-md text-primary hover:bg-[#ffffff08] active:bg-[#ffffff14] transition-colors focus-visible:outline-2 focus-visible:outline-primary focus-visible:outline-offset-2"
		>
			<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="18" x2="21" y2="18"/></svg>
		</button>

		<a href="/" class="flex-1 min-w-0 text-center text-primary font-sans font-bold tracking-[0.12em] text-[17px] sm:text-xl truncate focus-visible:outline-2 focus-visible:outline-primary focus-visible:outline-offset-2 rounded-sm">M3TACRON</a>

		<span class="shrink-0 w-10" aria-hidden="true"></span>
	</div>
</header>
