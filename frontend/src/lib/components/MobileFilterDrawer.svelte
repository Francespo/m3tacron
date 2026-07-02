<script lang="ts">
	/**
	 * MobileFilterDrawer — right-edge filter sheet for <lg viewports.
	 *
	 * The body is a snippet so the parent renders any filter content
	 * (faction checkboxes, search inputs, etc). The footer is a snippet with
	 * a sensible default: Reset + Apply. Apply just closes the drawer
	 * because filters are live-applied to the global store — there is no
	 * "draft" state to commit.
	 */
	import type { Snippet } from "svelte";
	import { page } from "$app/state";
	import { filters } from "$lib/stores/filters.svelte";
	import TournamentFilters from "./TournamentFilters.svelte";

	type Props = {
		open: boolean;
		onClose: () => void;
		title?: string;
		activeCount?: number;
		children: Snippet;
		footer?: Snippet;
	};
	let {
		open,
		onClose,
		title = "Filters",
		activeCount = 0,
		children,
		footer,
	}: Props = $props();

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

	// Auto-close on route change. Track the last pathname so the effect
	// doesn't re-fire on every `open` mutation.
	let lastPath = $state(page.url.pathname);
	$effect(() => {
		const current = page.url.pathname;
		if (current !== lastPath) {
			lastPath = current;
			if (open) onClose();
		}
	});

	function handleKeydown(e: KeyboardEvent) {
		if (!open) return;
		if (e.key === "Escape") {
			e.preventDefault();
			onClose();
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
		aria-label="Close filters"
		tabindex="-1"
		onclick={onClose}
		class="fixed inset-0 z-[55] bg-black/60 backdrop-blur-sm cursor-default"
	></button>
{/if}

<div
	bind:this={drawerEl}
	role="dialog"
	aria-modal="true"
	aria-label={title}
	aria-hidden={!open}
	class="fixed inset-y-0 right-0 z-[60] w-[min(92vw,380px)] min-w-0 bg-terminal-panel border-l border-[#ffffff14] flex flex-col transform transition-transform duration-200 ease-out motion-reduce:transition-none {open
		? 'translate-x-0'
		: 'translate-x-full'}"
	tabindex="-1"
>
	<header
		class="flex items-center justify-between h-14 px-4 border-b border-border-dark shrink-0"
	>
		<div class="flex items-center gap-2 min-w-0">
			<h2 class="text-primary font-sans font-medium text-base truncate">
				{title}
			</h2>
			{#if activeCount > 0}
				<span
					class="shrink-0 inline-flex items-center justify-center min-w-5 h-5 px-1.5 rounded-full text-[10px] font-mono font-bold bg-primary text-terminal-bg"
					aria-label="{activeCount} active filters"
				>
					{activeCount}
				</span>
			{/if}
		</div>
		<button
			bind:this={closeBtnEl}
			type="button"
			onclick={onClose}
			aria-label="Close filters"
			class="shrink-0 flex items-center justify-center w-11 h-11 rounded-md text-secondary hover:text-primary hover:bg-[#ffffff08] active:bg-[#ffffff14] transition-colors focus-visible:outline-2 focus-visible:outline-primary focus-visible:outline-offset-2"
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
	</header>

	<!-- Body: TournamentFilters is rendered in a non-scrolling wrapper so
	     its info tooltip (absolutely positioned, extends below the icon)
	     is never clipped by overflow. The page-specific children snippet
	     sits in its own scrollable area below. Bottom safe-area padding
	     on the scroll area keeps the iOS home indicator from covering
	     the last control. -->
	<div class="relative z-50 p-4 pb-0 min-w-0">
		<TournamentFilters />
	</div>
	{#if children}
		<div
			class="flex-1 overflow-x-hidden overflow-y-auto overscroll-contain px-4 pb-[calc(1rem+env(safe-area-inset-bottom))]"
		>
			<div class="h-px bg-border-dark my-4"></div>
			{@render children()}
		</div>
	{/if}

	<!-- Footer: custom snippet wins; otherwise render default Reset + Apply. -->
	{#if footer}
		{@render footer()}
	{:else}
		<footer
			class="shrink-0 grid grid-cols-2 gap-2 p-3 pb-[calc(0.75rem+env(safe-area-inset-bottom))] border-t border-border-dark bg-terminal-bg"
		>
			<button
				type="button"
				onclick={() => filters.resetAll()}
				class="min-h-11 px-4 rounded-md text-sm font-medium font-sans text-primary bg-transparent border border-border-dark hover:bg-[#ffffff08] active:bg-[#ffffff14] transition-colors focus-visible:outline-2 focus-visible:outline-primary focus-visible:outline-offset-2"
			>
				Reset
			</button>
			<button
				type="button"
				onclick={onClose}
				class="min-h-11 px-4 rounded-md text-sm font-medium font-sans text-terminal-bg bg-primary hover:bg-primary/90 active:bg-primary/80 transition-colors focus-visible:outline-2 focus-visible:outline-primary focus-visible:outline-offset-2"
			>
				Apply
			</button>
		</footer>
	{/if}
</div>
