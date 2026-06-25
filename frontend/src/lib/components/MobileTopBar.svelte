<script lang="ts">
	/**
	 * MobileTopBar
	 *
	 * Sticky top chrome for <md viewports. Sits above page content, below the
	 * nav/filter drawers (which are z-60). The desktop sidebar (z-100, hidden
	 * on <md) is unaffected by this component.
	 *
	 * The right side deliberately stays empty for now: the Game Content Source
	 * toggle (XWA / Legacy + Epic) is rendered inside MobileFilterDrawer on
	 * small screens. Putting it here would clutter the always-visible chrome
	 * and duplicate the "Filters" entry point. If a future feature needs a
	 * persistent right-side action, slot it in here.
	 */
	let { onOpenNav }: { onOpenNav: () => void } = $props();
</script>

<header
	class="sticky top-0 z-50 w-full bg-terminal-panel/95 backdrop-blur-md border-b border-[#ffffff14] md:hidden"
>
	<div class="flex items-center h-14 px-3 gap-2">
		<!-- Hamburger: 44x44 hit target, the icon itself is 20x14. -->
		<button
			type="button"
			onclick={onOpenNav}
			aria-label="Open navigation menu"
			class="shrink-0 flex items-center justify-center w-11 h-11 rounded-md text-primary hover:bg-[#ffffff08] active:bg-[#ffffff14] transition-colors focus-visible:outline-2 focus-visible:outline-primary focus-visible:outline-offset-2"
		>
			<svg
				xmlns="http://www.w3.org/2000/svg"
				width="22"
				height="22"
				viewBox="0 0 24 24"
				fill="none"
				stroke="currentColor"
				stroke-width="2"
				stroke-linecap="round"
				stroke-linejoin="round"
				aria-hidden="true"
			>
				<line x1="3" y1="6" x2="21" y2="6"></line>
				<line x1="3" y1="12" x2="21" y2="12"></line>
				<line x1="3" y1="18" x2="21" y2="18"></line>
			</svg>
		</button>

		<!-- Brand wordmark, centered. Uses the same tracking/size as the
		     desktop sidebar so the brand reads identically across surfaces. -->
		<a
			href="/"
			class="flex-1 text-center text-primary font-sans font-medium tracking-[0.15em] text-xl truncate focus-visible:outline-2 focus-visible:outline-primary focus-visible:outline-offset-2 rounded-sm"
		>
			M3TACRON
		</a>

		<!-- Right-side balance spacer — keeps the wordmark visually centered. -->
		<div class="shrink-0 w-11 h-11" aria-hidden="true"></div>
	</div>
</header>
