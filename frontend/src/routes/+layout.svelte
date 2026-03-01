<script lang="ts">
	import '../app.css';
	let { children } = $props();
</script>

<div class="flex min-h-screen bg-canvas text-primary font-sans antialiased overflow-x-hidden">
	<!-- Sidebar Placeholder -->
	<aside class="w-[250px] border-r border-border bg-panel shrink-0 flex-col hidden md:flex h-screen sticky top-0">
		<div class="p-6 border-b border-border">
			<h1 class="font-bold text-xl tracking-widest text-primary">M3TACRON</h1>
		</div>
		<nav class="flex-1 p-4 space-y-2 font-mono text-sm">
			<a href="/" class="block px-3 py-2 rounded bg-opacity-10 bg-white text-primary">Dashboard</a>
			<a href="/tournaments" class="block px-3 py-2 rounded text-secondary hover:text-primary hover:bg-white hover:bg-opacity-5">Tournaments</a>
			<a href="/lists" class="block px-3 py-2 rounded text-secondary hover:text-primary hover:bg-white hover:bg-opacity-5">Lists</a>
			<a href="/pilots" class="block px-3 py-2 rounded text-secondary hover:text-primary hover:bg-white hover:bg-opacity-5">Pilots</a>
			<a href="/upgrades" class="block px-3 py-2 rounded text-secondary hover:text-primary hover:bg-white hover:bg-opacity-5">Upgrades</a>
		</nav>
	</aside>

	<!-- Main Content -->
	<main class="flex-1 w-full pl-4 pr-4 sm:px-6 md:px-8 lg:px-10 py-8 pb-[120px]">
		{@render children()}
	</main>
</div>
