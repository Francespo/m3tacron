<script lang="ts">
	import "../app.css"; // Global Tailwind + Fonts
	import Sidebar from "$lib/components/Sidebar.svelte";
	import { NAV_LINKS } from "$lib/components/Sidebar.svelte";
	import { page } from "$app/stores";
	import type { Snippet } from "svelte";

	let { children }: { children: Snippet } = $props();
	let mobileMenuOpen = $state(false);

	$effect(() => {
		$page.url.pathname;
		mobileMenuOpen = false;
	});

	$effect(() => {
		if (typeof document === "undefined") return;
		document.body.classList.toggle("mobile-menu-open", mobileMenuOpen);
		return () => {
			document.body.classList.remove("mobile-menu-open");
		};
	});

	$effect(() => {
		if (typeof window === "undefined" || !mobileMenuOpen) return;

		const onKeyDown = (event: KeyboardEvent) => {
			if (event.key === "Escape") {
				mobileMenuOpen = false;
			}
		};

		window.addEventListener("keydown", onKeyDown);
		return () => window.removeEventListener("keydown", onKeyDown);
	});
</script>

<div
	class="relative bg-terminal-bg min-h-screen text-primary overflow-x-hidden"
>
	<!-- Desktop Sidebar -->
	<Sidebar />

	<!-- Mobile Header -->
	<header
		class="md:hidden sticky top-0 z-[110] h-14 border-b border-border-dark bg-terminal-panel/95 backdrop-blur px-3"
	>
		<div class="h-full flex items-center justify-between gap-2">
			<button
				type="button"
				onclick={() => (mobileMenuOpen = true)}
				aria-label="Open navigation menu"
				aria-controls="mobile-nav-drawer"
				aria-expanded={mobileMenuOpen}
				class="min-h-11 min-w-11 inline-flex items-center justify-center rounded border border-border-dark text-secondary hover:text-primary hover:bg-white/5"
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
				>
					<path d="M3 6h18"></path>
					<path d="M3 12h18"></path>
					<path d="M3 18h18"></path>
				</svg>
			</button>

			<a
				href="/"
				class="text-primary font-sans font-medium tracking-[0.15em] text-sm"
			>
				M3TACRON
			</a>

			<div class="min-h-11 min-w-11"></div>
		</div>
	</header>

	<!-- Mobile Navigation Drawer -->
	<div
		class="md:hidden fixed inset-0 z-[120] transition-opacity duration-200 {mobileMenuOpen
			? 'pointer-events-auto'
			: 'pointer-events-none'}"
		aria-hidden={!mobileMenuOpen}
	>
		<button
			type="button"
			class="absolute inset-0 bg-black/70 transition-opacity duration-200 {mobileMenuOpen
				? 'opacity-100'
				: 'opacity-0'}"
			onclick={() => (mobileMenuOpen = false)}
			aria-label="Close navigation menu"
		></button>

		<aside
			id="mobile-nav-drawer"
			class="absolute left-0 top-0 h-[100dvh] w-[min(86vw,320px)] bg-terminal-panel border-r border-border-dark transition-transform duration-200 ease-out {mobileMenuOpen
				? 'translate-x-0'
				: '-translate-x-full'}"
		>
			<div class="h-14 border-b border-border-dark px-3 flex items-center justify-between">
				<span class="text-primary font-sans font-medium tracking-[0.15em] text-sm"
					>M3TACRON</span
				>
				<button
					type="button"
					onclick={() => (mobileMenuOpen = false)}
					aria-label="Close navigation menu"
					class="min-h-11 min-w-11 inline-flex items-center justify-center rounded border border-border-dark text-secondary hover:text-primary hover:bg-white/5"
				>
					<svg
						xmlns="http://www.w3.org/2000/svg"
						width="16"
						height="16"
						viewBox="0 0 24 24"
						fill="none"
						stroke="currentColor"
						stroke-width="2"
						stroke-linecap="round"
						stroke-linejoin="round"
					>
						<path d="M18 6 6 18"></path>
						<path d="m6 6 12 12"></path>
					</svg>
				</button>
			</div>

			<nav class="py-2">
				{#each NAV_LINKS as link}
					<a
						href={link.href}
						onclick={() => (mobileMenuOpen = false)}
						aria-current={$page.url.pathname === link.href ? "page" : undefined}
						class="flex items-center min-h-11 px-4 py-2 border-l-2 transition-colors {$page
							.url.pathname === link.href
							? 'bg-[rgba(255,255,255,0.05)] border-primary text-primary'
							: 'border-transparent text-secondary hover:text-primary hover:bg-[rgba(255,255,255,0.03)]'}"
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
						>
							<path d={link.icon}></path>
						</svg>
						<span class="ml-3 text-sm font-medium font-sans truncate"
							>{link.text}</span
						>
					</a>
				{/each}
			</nav>
		</aside>
	</div>

	<!-- Main Content Area -->
	<div
		class="md:ml-[260px] min-h-screen transition-all duration-200 relative"
	>
		<!-- Global glow logic can be ported here eventually, placing a vignette wrapper -->
		<div
			class="absolute top-0 right-0 bottom-0 pointer-events-none opacity-30 bg-gradient-to-l from-blue-900/10 to-transparent w-1/4"
		></div>
		<div
			class="absolute bottom-0 left-0 right-0 pointer-events-none opacity-30 bg-gradient-to-t from-blue-900/10 to-transparent h-1/4"
		></div>

		<!-- Slot renders the specific route +page.svelte -->
		{@render children()}
	</div>
</div>
