<script lang="ts">
	import { page } from "$app/stores";

	// Sidebar Links
	const links = [
		{
			text: "DASHBOARD",
			href: "/",
			icon: "M20 16V7a2 2 0 0 0-2-2H6a2 2 0 0 0-2 2v9m16 0H4m16 0 1.28 2.55a1 1 0 0 1-.9 1.45H3.62a1 1 0 0 1-.9-1.45L4 16",
		},
		{
			text: "TOURNAMENTS",
			href: "/tournaments",
			icon: "M6 9H4.5a2.5 2.5 0 0 1 0-5H6M18 9h1.5a2.5 2.5 0 0 0 0-5H18M4 22h16M10 14.66V17c0 .55-.47.98-.97 1.21C7.85 18.75 7 20.24 7 22M14 14.66V17c0 .55.47.98.97 1.21C16.15 18.75 17 20.24 17 22M18 2H6v7a6 6 0 0 0 12 0V2Z",
		},
		{
			text: "SQUADRONS",
			href: "/squadrons",
			icon: "M14.5 4h5v5M19.5 4l-5 5M4.5 20h5v-5M9.5 15l-5 5M14.5 20h5v-5M19.5 20l-5-5M4.5 4h5v5M9.5 9l-5-5",
		},
		{
			text: "LISTS",
			href: "/lists",
			icon: "M8 6h13M8 12h13M8 18h13M3 6h.01M3 12h.01M3 18h.01",
		},
		{
			text: "SHIPS",
			href: "/ships",
			icon: "M4.5 16.5c-1.5 1.26-2 5-2 5s3.74-.5 5-2c.71-.84.7-2.13-.09-2.91a2.18 2.18 0 0 0-2.91-.09zM12 15l-3-3a22 22 0 0 1 2-3.95A12.88 12.88 0 0 1 22 2c0 2.72-.78 7.5-6 11a22.35 22.35 0 0 1-4 2zM9 12H4s.55-3.03 2-4c1.62-1.08 5 0 5 0M12 15v5s3.03-.55 4-2c1.08-1.62 0-5 0-5",
		},
		{
			text: "CARDS",
			href: "/cards",
			icon: "M19 17V5a2 2 0 0 0-2-2H4M8 21h12a2 2 0 0 1-2-2V5a2 2 0 0 0-2-2H4a2 2 0 0 0-2 2v12c0 1.1.9 2 2 2h2M8 21a2 2 0 0 1-2-2v-3h4v3a2 2 0 0 1-2 2Z",
		},
		{
			text: "SUPPORT & EVOLUTION",
			href: "/support",
			icon: "M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z",
		},
	];

	let collapsed = false; // Hardcode for now, can be toggled later
</script>

<div
	class="fixed left-0 top-0 h-screen bg-terminal-panel border-r border-[#ffffff14] flex flex-col z-[100] transition-all duration-200 {collapsed
		? 'w-[60px]'
		: 'w-[260px]'} hidden md:flex"
>
	<!-- Header / Brand -->
	<div class="border-b border-border-dark w-full px-4 py-6">
		<div class="flex flex-col {collapsed ? 'items-center' : 'items-start'}">
			<span
				class="text-primary font-sans font-medium tracking-[0.15em] {collapsed
					? 'text-lg'
					: 'text-xl'}"
			>
				{collapsed ? "M3" : "M3TACRON"}
			</span>
			{#if !collapsed}
				<span class="text-secondary font-mono text-xs">v2.0.0</span>
			{/if}
		</div>
	</div>

	<!-- Navigation -->
	<div class="flex flex-col w-full py-2">
		{#each links as link}
			<a
				href={link.href}
				class="flex items-center py-2 px-4 w-full border-l-2 transition-all duration-200 {$page
					.url.pathname === link.href
					? 'bg-[rgba(255,255,255,0.05)] border-primary text-primary'
					: 'border-transparent text-secondary hover:bg-[rgba(255,255,255,0.03)] hover:text-primary'} {collapsed
					? 'justify-center'
					: 'justify-start'}"
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

				{#if !collapsed}
					<span class="ml-3 text-sm font-medium font-sans truncate"
						>{link.text}</span
					>
					{#if $page.url.pathname === link.href}
						<span class="ml-auto text-primary font-mono">&lt;</span>
					{/if}
				{/if}
			</a>
		{/each}
	</div>

	<div class="grow"></div>

	<!-- Footer -->
	{#if !collapsed}
		<div
			class="border-t border-border-dark w-full p-4 flex flex-col items-center gap-1"
		>
			<span class="text-secondary font-sans text-xs font-bold"
				>M3taCron Analytics</span
			>
			<span
				class="text-secondary font-sans text-xs flex items-center gap-1"
				>Made with <span class="text-red-500">❤️</span> by Francespo</span
			>

			<div class="w-full h-px bg-white/5 my-2"></div>

			<p
				class="text-[#555555] font-sans text-[10px] text-center leading-tight"
			>
				Star Wars and all related properties are © & ™ Lucasfilm Ltd.
				and/or The Walt Disney Company. This fan-created site is for
				informational purposes only and is not affiliated with, endorsed
				by, or sponsored by Lucasfilm Ltd. or The Walt Disney Company.
			</p>
		</div>
	{/if}
</div>
