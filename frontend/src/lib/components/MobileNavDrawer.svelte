<script lang="ts">
	/**
	 * MobileNavDrawer — left-edge nav drawer for <md viewports.
	 * Source-of-truth for nav entries is NAV_LINKS in Sidebar.svelte.
	 * Parent should NOT mount this on md+; the desktop Sidebar owns that space.
	 */
	import { page } from "$app/state";
	import { filters } from "$lib/stores/filters.svelte";
	import { NAV_LINKS } from "./Sidebar.svelte";
	import Toggle from "./Toggle.svelte";

	let { open = $bindable(false) }: { open: boolean } = $props();

	let drawerEl: HTMLElement | undefined = $state();
	let closeBtnEl: HTMLButtonElement | undefined = $state();
	let triggerEl: HTMLElement | null = null;
	let previousOverflow = "";
	// Per-instance counter. The spec'd layout opens at most one drawer at a
	// time, so a single counter per component is enough; if that ever changes
	// lift this into a shared module-level helper.
	let scrollLockCount = 0;

	const FOCUSABLE = [
		"a[href]",
		"button:not([disabled])",
		"input:not([disabled])",
		"select:not([disabled])",
		"textarea:not([disabled])",
		"[tabindex]:not([tabindex='-1'])",
	].join(",");
	const getFocusable = (root: HTMLElement) =>
		Array.from(root.querySelectorAll<HTMLElement>(FOCUSABLE)).filter(
			(el) => el.offsetParent !== null,
		);

	$effect(() => {
		if (!open) return;
		scrollLockCount++;
		if (scrollLockCount === 1) {
			previousOverflow = document.body.style.overflow;
			document.body.style.overflow = "hidden";
		}
		triggerEl = (document.activeElement as HTMLElement) ?? null;
		queueMicrotask(() => closeBtnEl?.focus());
		return () => {
			scrollLockCount = Math.max(0, scrollLockCount - 1);
			if (scrollLockCount === 0) document.body.style.overflow = previousOverflow;
			triggerEl?.focus?.();
			triggerEl = null;
		};
	});

	// Auto-close on route change. We track the last pathname and only close
	// when it actually changes — otherwise the effect would re-run whenever
	// `open` itself is mutated, and clobber an open that was just set.
	let lastPath = $state(page.url.pathname);
	$effect(() => {
		const current = page.url.pathname;
		if (current !== lastPath) {
			lastPath = current;
			if (open) open = false;
		}
	});

	function handleKeydown(e: KeyboardEvent) {
		if (!open) return;
		if (e.key === "Escape") {
			e.preventDefault();
			open = false;
			return;
		}
		if (e.key === "Tab" && drawerEl) {
			const focusable = getFocusable(drawerEl);
			if (focusable.length === 0) {
				e.preventDefault();
				return;
			}
			const first = focusable[0];
			const last = focusable[focusable.length - 1];
			const active = document.activeElement as HTMLElement | null;
			if (e.shiftKey && active === first) {
				e.preventDefault();
				last.focus();
			} else if (!e.shiftKey && active === last) {
				e.preventDefault();
				first.focus();
			}
		}
	}
</script>

<svelte:window onkeydown={handleKeydown} />

{#if open}
	<button
		type="button"
		aria-label="Close menu"
		tabindex="-1"
		onclick={() => (open = false)}
		class="fixed inset-0 z-[55] bg-black/60 backdrop-blur-sm cursor-default md:hidden"
	></button>
{/if}

<div
	bind:this={drawerEl}
	role="dialog"
	aria-modal="true"
	aria-label="Navigation"
	aria-hidden={!open}
	class="fixed inset-y-0 left-0 z-[60] w-[min(86vw,320px)] bg-terminal-panel border-r border-[#ffffff14] flex flex-col transform transition-transform duration-200 ease-out md:hidden motion-reduce:transition-none {open
		? 'translate-x-0'
		: '-translate-x-full'}"
	tabindex="-1"
>
	<div
		class="flex items-center justify-between gap-3 px-4 py-3 border-b border-border-dark shrink-0"
	>
		<div class="flex flex-col items-start min-w-0">
			<span
				class="text-primary font-mono font-bold uppercase tracking-tighter leading-none text-2xl"
			>
				M3TACRON
			</span>
			<!-- XWA / LEGACY + Epic toggle (consolidated content source controls) -->
			<div class="flex items-center gap-1 mt-1.5">
				<button
					type="button"
					onclick={() => (filters.dataSource = "xwa")}
					aria-pressed={filters.dataSource === "xwa"}
					class="px-2 py-0.5 text-xs font-mono rounded transition-colors {filters.dataSource ===
					'xwa'
						? 'bg-cyan-500/20 text-cyan-400 border border-cyan-500/50'
						: 'bg-transparent text-secondary border border-border-dark hover:text-primary'}"
				>
					XWA
				</button>
				<button
					type="button"
					onclick={() => (filters.dataSource = "legacy")}
					aria-pressed={filters.dataSource === "legacy"}
					class="px-2 py-0.5 text-xs font-mono rounded transition-colors {filters.dataSource ===
					'legacy'
						? 'bg-purple-500/20 text-purple-400 border border-purple-500/50'
						: 'bg-transparent text-secondary border border-border-dark hover:text-primary'}"
				>
					LEGACY
				</button>
				<label
					class="flex items-center gap-1 ml-1 text-xs text-secondary font-mono cursor-pointer hover:text-primary"
				>
					<Toggle
						size="xs"
						ariaLabel="Include epic content"
						checked={filters.includeEpic}
						onchange={(e) => (filters.includeEpic = (e.currentTarget as HTMLInputElement).checked)}
					/>
					Epic
				</label>
			</div>
		</div>
		<button
			bind:this={closeBtnEl}
			type="button"
			onclick={() => (open = false)}
			aria-label="Close menu"
			class="flex items-center justify-center w-11 h-11 rounded-md text-secondary hover:text-primary hover:bg-[#ffffff08] active:bg-[#ffffff14] transition-colors focus-visible:outline-2 focus-visible:outline-primary focus-visible:outline-offset-2 shrink-0"
		>
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
				<line x1="18" y1="6" x2="6" y2="18"></line>
				<line x1="6" y1="6" x2="18" y2="18"></line>
			</svg>
		</button>
	</div>

	<nav class="flex-1 overflow-y-auto py-2" aria-label="Primary">
		{#each NAV_LINKS as link (link.href)}
			{@const active = page.url.pathname === link.href}
			<a
				href={link.href}
				aria-current={active ? "page" : undefined}
				class="flex items-center min-h-11 px-4 w-full border-l-2 transition-colors duration-150 {active
					? 'bg-[rgba(255,255,255,0.05)] border-primary text-primary'
					: 'border-transparent text-secondary hover:bg-[rgba(255,255,255,0.03)] hover:text-primary'}"
			>
				<svg
					xmlns="http://www.w3.org/2000/svg"
					width="18"
					height="18"
					viewBox="0 0 24 24"
					fill="none"
					stroke="currentColor"
					stroke-width="2"
					stroke-linecap="round"
					stroke-linejoin="round"
					class="shrink-0"
					aria-hidden="true"
				>
					<path d={link.icon}></path>
				</svg>
				<span class="ml-3 text-sm font-medium font-sans truncate"
					>{link.label}</span
				>
				{#if active}
					<span class="ml-auto text-primary font-mono text-xs" aria-hidden="true"
						>&lt;</span
					>
				{/if}
			</a>
		{/each}
	</nav>

	<div class="border-t border-border-dark px-4 py-3 shrink-0">
		<p class="text-[10px] font-mono text-[#666] text-center leading-snug">
			Star Wars and all related properties are © & ™ Lucasfilm Ltd. and/or
			The Walt Disney Company. Fan-made, not affiliated.
		</p>
	</div>
</div>
