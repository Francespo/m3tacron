<svelte:head>
	<title>About - M3tacron</title>
</svelte:head>

<div class="mx-auto flex min-h-screen max-w-3xl flex-col gap-10 px-6 py-8">
	<header class="space-y-3">
		<h1 class="text-3xl font-mono font-bold uppercase tracking-tighter text-primary md:text-4xl">What is M3tacron?</h1>
		<p class="font-sans text-sm leading-relaxed text-secondary">M3tacron brings X-Wing tournament results together in one place, so you can see what is working in the meta at a glance.</p>
	</header>

	<!-- Data and sources - editorial, no capsule -->
	<section class="space-y-3">
		<h2 class="text-3xl font-mono font-bold uppercase tracking-tighter text-primary md:text-4xl">Data and sources</h2>
		<p class="font-sans text-sm leading-relaxed text-secondary">Data comes from <span class="text-primary">ListFortress</span>, <span class="text-primary">Longshanks</span> and <span class="text-primary">Rollbetter</span>. Recent tournaments are added automatically every day.</p>
		<p class="font-sans text-sm leading-relaxed text-secondary">You can use the selector at the top left to switch modes.</p>
		<div class="space-y-3 border-l-2 border-white/10 pl-4">
			<div class="flex items-center gap-3">
				<span class="inline-flex w-[72px] shrink-0 items-center justify-center rounded-md border border-amber-500/30 bg-amber-500/20 px-2 py-1 font-mono text-xs font-bold text-amber-400">XWA</span>
				<p class="font-sans text-xs leading-relaxed text-secondary">Shows cards legal in XWA and automatically filters the dataset to only XWA tournaments.</p>
			</div>
			<div class="flex items-center gap-3">
				<span class="inline-flex w-[72px] shrink-0 items-center justify-center rounded-md border border-violet-500/30 bg-violet-500/20 px-2 py-1 font-mono text-xs font-bold uppercase text-violet-400">LEGACY</span>
				<p class="font-sans text-xs leading-relaxed text-secondary">Shows cards legal in Legacy and automatically filters the dataset to only Legacy X2PO tournaments.</p>
			</div>
		</div>
	</section>

	<!-- How to use - editorial -->
	<section class="space-y-3">
		<h2 class="text-3xl font-mono font-bold uppercase tracking-tighter text-primary md:text-4xl">How to use</h2>

		<div class="grid grid-cols-1 gap-6 sm:grid-cols-2">
			<div class="space-y-1">
				<a href="/" class="font-mono text-sm font-bold uppercase tracking-wider text-primary underline decoration-white/20 underline-offset-2 hover:decoration-white/40">Dashboard</a>
				<p class="font-sans text-sm leading-relaxed text-secondary">The landing page and a quick overview of the meta. It gives you an immediate read on what is popular and what is performing well.</p>
			</div>
			<div class="space-y-1">
				<a href="/tournaments" class="font-mono text-sm font-bold uppercase tracking-wider text-primary underline decoration-white/20 underline-offset-2 hover:decoration-white/40">Tournaments</a>
				<p class="font-sans text-sm leading-relaxed text-secondary">A browser for every tournament recorded online. Find events by date, location or format and open any of them for its results.</p>
			</div>
		</div>

		<div class="space-y-1">
				<h3 class="mb-2 font-mono text-sm font-bold uppercase tracking-wider text-primary">
				<a href="/squadrons" class="underline decoration-white/20 underline-offset-2 hover:decoration-white/40">Squadrons</a>, <a href="/lists" class="underline decoration-white/20 underline-offset-2 hover:decoration-white/40">Lists</a>, <a href="/ships" class="underline decoration-white/20 underline-offset-2 hover:decoration-white/40">Ships</a> and <a href="/cards" class="underline decoration-white/20 underline-offset-2 hover:decoration-white/40">Cards</a>
			</h3>
			<p class="mb-4 font-sans text-sm leading-relaxed text-secondary">Same data, four views. Choose which tournaments to include, then narrow what you see on the page.</p>

			<div class="space-y-4">
				<div class="flex gap-3">
					<div class="mt-0.5 h-6 w-0.5 shrink-0 rounded-full bg-white/15"></div>
					<div>
						<div class="flex items-center gap-2">
							<svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="text-secondary shrink-0" aria-hidden="true"><polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3" /></svg>
							<span class="font-mono text-xs font-bold uppercase tracking-wider text-primary">Dataset filters</span>
						</div>
						<p class="mt-1 font-sans text-sm leading-relaxed text-secondary">A floating <span class="rounded border border-border-dark bg-white/5 px-1.5 py-0.5 font-mono text-[11px] text-primary">Dataset filters</span> button at the bottom right. Open it to filter the tournaments used as input: by date range, location, format or source.</p>
					</div>
				</div>
				<div class="flex gap-3">
					<div class="mt-0.5 h-6 w-0.5 shrink-0 rounded-full bg-white/15"></div>
					<div>
						<div class="flex items-center gap-2">
							<svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="text-secondary shrink-0" aria-hidden="true"><path d="M3 6h18M7 12h10M10 18h4" /></svg>
							<span class="font-mono text-xs font-bold uppercase tracking-wider text-primary">Page filters</span>
						</div>
						<p class="mt-1 font-sans text-sm leading-relaxed text-secondary">Each page has its own collapsible filter bar at the top. It narrows only the results on that page, for example by faction, ship, pilot or card stats.</p>
					</div>
				</div>
				<div class="flex gap-3">
					<div class="mt-0.5 h-6 w-0.5 shrink-0 rounded-full bg-white/15"></div>
					<div>
						<div class="flex items-center gap-2">
							<svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="text-secondary shrink-0" aria-hidden="true"><path d="M12 5v14M19 12l-7 7-7-7" /></svg>
							<span class="font-mono text-xs font-bold uppercase tracking-wider text-primary">Sort results</span>
						</div>
						<p class="mt-1 font-sans text-sm leading-relaxed text-secondary">Small control near the page title. Pick the metric and flip the direction to find the most played or best performing entries first.</p>
					</div>
				</div>
			</div>
		</div>
	</section>

	<section class="space-y-3">
		<h2 class="text-3xl font-mono font-bold uppercase tracking-tighter text-primary md:text-4xl">Notes and support</h2>
		<p class="font-sans text-sm leading-relaxed text-secondary">Unofficial fan project. Star Wars is &copy; and &trade; Lucasfilm Ltd. and Disney. This site is not affiliated or sponsored. Made with &hearts; by <span class="text-primary">Francespo</span>.</p>
		<div class="mt-4 flex flex-wrap gap-2">
			<a href="/support" class="inline-flex items-center gap-2 rounded border border-primary/20 bg-primary px-4 py-2 font-mono text-xs font-bold uppercase tracking-wider text-terminal-bg hover:bg-white">Support the project</a>
			<a href="https://github.com/Francespo/m3tacron" target="_blank" rel="noopener noreferrer" class="inline-flex items-center gap-2 rounded border border-border-dark bg-white/[0.03] px-4 py-2 font-mono text-xs font-bold uppercase tracking-wider text-secondary hover:bg-white/[0.06] hover:text-primary">GitHub</a>
		</div>
	</section>
</div>
