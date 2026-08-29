<svelte:head>
	<title>About - M3tacron</title>
</svelte:head>

<div class="mx-auto flex min-h-screen max-w-3xl flex-col gap-6 px-6 py-8">
	<!-- Header -->
	<header>
		<h1
			class="text-3xl font-mono font-bold uppercase tracking-tighter text-primary md:text-4xl"
		>
			About
		</h1>
		<p class="mt-2 font-sans text-sm leading-relaxed text-secondary">
			M3tacron brings X-Wing tournament results together in one place, so you
			can see what is working in the meta at a glance.
		</p>
	</header>

	<!-- 1 - Data and sources -->
	<section
		class="rounded-lg border border-border-dark bg-terminal-panel p-5 shadow-[inset_0_1px_0_rgba(255,255,255,0.03)]"
	>
		<h2
			class="mb-3 font-mono text-xs font-bold uppercase tracking-widest text-primary"
		>
			Data and sources
		</h2>
		<p class="font-sans text-sm leading-relaxed text-secondary">
			Data comes from <span class="text-primary">ListFortress</span>,
			<span class="text-primary">Longshanks</span> and
			<span class="text-primary">Rollbetter</span>. Recent tournaments are added
			automatically every day.
		</p>
		<p class="mt-3 font-sans text-sm leading-relaxed text-secondary">
			The toggle at the top left switches between
			<span class="rounded border border-border-dark bg-white/5 px-1.5 py-0.5 font-mono text-[11px] text-primary">XWA</span>
			and
			<span class="rounded border border-border-dark bg-white/5 px-1.5 py-0.5 font-mono text-[11px] text-primary">Legacy</span>. It changes what you see across the site: XWA
			shows cards legal in XWA and Legacy shows cards legal in Legacy,
			including the latest releases for both. Each choice also
			automatically filters the dataset to only tournaments in the selected
			format.
		</p>
	</section>

	<!-- 2 - How to use (textual, no nested capsules) -->
	<section
		id="how-to-use"
		class="rounded-lg border border-border-dark bg-terminal-panel shadow-[inset_0_1px_0_rgba(255,255,255,0.03)]"
	>
		<div class="p-5 pb-4">
			<h2
				class="font-mono text-xs font-bold uppercase tracking-widest text-primary"
			>
				How to use
			</h2>
		</div>

		<!-- Dashboard -->
		<div class="border-t border-border-dark px-5 py-4">
			<div class="mb-1">
				<a href="/" class="font-mono text-xs font-bold uppercase tracking-wider text-primary underline decoration-white/20 underline-offset-2 hover:decoration-white/40">Dashboard</a>
			</div>
			<p class="font-sans text-xs leading-relaxed text-secondary">
				The landing page and a quick overview of the meta. It gives you an
				immediate read on what is popular and what is performing well.
			</p>
		</div>

		<!-- Tournaments -->
		<div class="border-t border-border-dark px-5 py-4">
			<div class="mb-1">
				<a href="/tournaments" class="font-mono text-xs font-bold uppercase tracking-wider text-primary underline decoration-white/20 underline-offset-2 hover:decoration-white/40">Tournaments</a>
			</div>
			<p class="font-sans text-xs leading-relaxed text-secondary">
				A browser for every tournament recorded online. Find events by date,
				location or format and open any of them for its results.
			</p>
		</div>

		<!-- Squadrons, Lists, Ships and Cards - parent -->
		<div class="border-t border-border-dark px-5 pt-5 pb-3">
			<h3 class="mb-2 font-mono text-xs font-bold uppercase tracking-wider text-primary">
				<a href="/squadrons" class="underline decoration-white/20 underline-offset-2 hover:decoration-white/40 hover:text-white">Squadrons</a>, <a href="/lists" class="underline decoration-white/20 underline-offset-2 hover:decoration-white/40 hover:text-white">Lists</a>, <a href="/ships" class="underline decoration-white/20 underline-offset-2 hover:decoration-white/40 hover:text-white">Ships</a> and <a href="/cards" class="underline decoration-white/20 underline-offset-2 hover:decoration-white/40 hover:text-white">Cards</a>
			</h3>
			<p class="font-sans text-xs leading-relaxed text-secondary">
				Two layers of filters control what you see. Dataset filters decide
				which tournaments count. Page filters decide which rows stay on
				screen. These four pages share the same structure: a floating dataset
				control, a collapsible page-specific bar, and a small sort control.
			</p>
		</div>

		<!-- Children - indented with left border for hierarchy, no capsules -->
		<div class="px-5 pb-5">
			<div class="ml-2 border-l border-white/10 pl-5 space-y-5">
				<!-- Dataset filters -->
				<div>
					<div class="mb-1 flex items-center gap-2">
						<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="text-secondary shrink-0" aria-hidden="true"><polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3" /></svg>
						<span class="font-mono text-xs font-bold uppercase tracking-wider text-primary">Dataset filters</span>
					</div>
					<p class="font-sans text-xs leading-relaxed text-secondary">
						A floating
						<span class="rounded border border-border-dark bg-white/5 px-1.5 py-0.5 font-mono text-[11px] text-primary">Dataset filters</span>
						button sits at the bottom right. Open it to filter the tournaments
						used as input: by date range, location, format or source. The stats
						on the page are then computed only from the tournaments you kept, so
						you can narrow the view to a region, a period, a single format, or
						just a few events. Active dataset filters show a count on the button
						and as chips you can remove one by one.
					</p>
				</div>

				<!-- Page filters -->
				<div>
					<div class="mb-1 flex items-center gap-2">
						<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="text-secondary shrink-0" aria-hidden="true"><path d="M3 6h18M7 12h10M10 18h4" /></svg>
						<span class="font-mono text-xs font-bold uppercase tracking-wider text-primary">Page filters</span>
					</div>
					<p class="font-sans text-xs leading-relaxed text-secondary">
						Each of these pages has its own collapsible filter bar at the top.
						It narrows only the results on that page, for example by faction,
						ship, pilot or card stats, without changing the dataset underneath.
						The bar stays collapsed by default to keep the view tidy. Active
						page filters also appear as chips with a clear-all option.
					</p>
				</div>

				<!-- Sort results -->
				<div>
					<div class="mb-1 flex items-center gap-2">
						<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="text-secondary shrink-0" aria-hidden="true"><path d="M12 5v14M19 12l-7 7-7-7" /></svg>
						<span class="font-mono text-xs font-bold uppercase tracking-wider text-primary">Sort results</span>
					</div>
					<p class="font-sans text-xs leading-relaxed text-secondary">
						Next to the page title you will find a small sort control. Pick
						the metric, like games, win rate or lists, and flip the
						direction. The list reorders in place so you can scan for the most
						played or the best performing entries first.
					</p>
				</div>
			</div>
		</div>
	</section>

	<!-- 3 - Notes and support -->
	<section
		class="rounded-lg border border-border-dark bg-terminal-panel p-5 shadow-[inset_0_1px_0_rgba(255,255,255,0.03)]"
	>
		<h2
			class="mb-3 font-mono text-xs font-bold uppercase tracking-widest text-primary"
		>
			Notes and support
		</h2>
		<p class="font-sans text-sm leading-relaxed text-secondary">
			Unofficial fan project. Star Wars is &copy; and &trade; Lucasfilm Ltd. and
			Disney. This site is not affiliated or sponsored. Made with &hearts; by
			<span class="text-primary">Francespo</span>.
		</p>
		<div class="mt-4 flex flex-wrap gap-2">
			<a
				href="/support"
				class="inline-flex items-center gap-2 rounded border border-primary/20 bg-primary px-4 py-2 font-mono text-xs font-bold uppercase tracking-wider text-terminal-bg transition-colors hover:bg-white"
			>
				Support the project
			</a>
			<a
				href="https://github.com/Francespo/m3tacron"
				target="_blank"
				rel="noopener noreferrer"
				class="inline-flex items-center gap-2 rounded border border-border-dark bg-white/[0.03] px-4 py-2 font-mono text-xs font-bold uppercase tracking-wider text-secondary transition-colors hover:bg-white/[0.06] hover:text-primary"
			>
				GitHub
				<svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="shrink-0"><path d="M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4" /><polyline points="10 17 15 12 10 7" /><line x1="15" y1="12" x2="3" y2="12" /></svg>
			</a>
		</div>
	</section>

	<p
		class="text-center font-mono text-[11px] leading-relaxed text-secondary/50"
	>
		Copy kept intentionally short. We can refine it line by line whenever you
		like.
	</p>
</div>
