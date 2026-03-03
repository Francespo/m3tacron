<script>
	/** @type {Array<{name: string, xws: string, faction: string, size: string}>} */
	let ships = $state([]);
	let chassisFilter = $state('');
	let factionFilter = $state('');
	let loading = $state(true);
	let error = $state('');

	// Derived: unique chassis names from loaded ships
	let chassisOptions = $derived(() => {
		const names = [...new Set(ships.map(s => s.name))];
		names.sort();
		return names;
	});

	// Derived: unique factions from loaded ships
	let factionOptions = $derived(() => {
		const names = [...new Set(ships.map(s => s.faction))];
		names.sort();
		return names;
	});

	// Derived: filtered ships
	let filteredShips = $derived(() => {
		return ships.filter(s => {
			if (chassisFilter && s.name !== chassisFilter) return false;
			if (factionFilter && s.faction !== factionFilter) return false;
			return true;
		});
	});

	async function fetchShips() {
		loading = true;
		error = '';
		try {
			const res = await fetch('/api/ships');
			if (!res.ok) throw new Error(`HTTP ${res.status}`);
			ships = await res.json();
		} catch (e) {
			error = e.message || 'Failed to load ships';
		} finally {
			loading = false;
		}
	}

	$effect(() => {
		fetchShips();
	});
</script>

<svelte:head>
	<title>Ships / Chassis – M3taCron</title>
	<meta name="description" content="Browse X-Wing ship chassis data with filtering by chassis and faction." />
</svelte:head>

<main class="ships-page">
	<h1>Ships / Chassis</h1>

	<!-- Filters -->
	<section class="filters">
		<label>
			<span>Chassis</span>
			<select bind:value={chassisFilter}>
				<option value="">All chassis</option>
				{#each chassisOptions() as name}
					<option value={name}>{name}</option>
				{/each}
			</select>
		</label>

		<label>
			<span>Faction</span>
			<select bind:value={factionFilter}>
				<option value="">All factions</option>
				{#each factionOptions() as name}
					<option value={name}>{name}</option>
				{/each}
			</select>
		</label>
	</section>

	<!-- Loading / Error -->
	{#if loading}
		<p class="status-msg">Loading ships…</p>
	{:else if error}
		<p class="status-msg error">Error: {error}</p>
	{:else if filteredShips().length === 0}
		<p class="status-msg">No ships match the current filters.</p>
	{:else}
		<!-- Ship Cards Grid -->
		<section class="card-grid">
			{#each filteredShips() as ship (ship.xws + '-' + ship.faction)}
				<!-- Hover scale is on the OUTER card container, NOT the icon -->
				<div class="ship-card">
					<div class="ship-icon">🚀</div>
					<h2 class="ship-name">{ship.name}</h2>
					<p class="ship-faction">{ship.faction}</p>
					<span class="ship-size">{ship.size}</span>
				</div>
			{/each}
		</section>
	{/if}
</main>

<style>
	/* ── Page Layout ── */
	.ships-page {
		max-width: 1200px;
		margin: 0 auto;
		padding: 2rem 1rem;
		font-family: 'Segoe UI', system-ui, sans-serif;
		color: #e0e0e0;
	}

	h1 {
		font-size: 2rem;
		margin-bottom: 1.5rem;
		color: #ffffff;
	}

	/* ── Filters ── */
	.filters {
		display: flex;
		gap: 1.5rem;
		flex-wrap: wrap;
		margin-bottom: 2rem;
	}

	.filters label {
		display: flex;
		flex-direction: column;
		gap: 0.25rem;
	}

	.filters span {
		font-size: 0.85rem;
		color: #aaa;
		text-transform: uppercase;
		letter-spacing: 0.05em;
	}

	.filters select {
		padding: 0.5rem 0.75rem;
		border-radius: 6px;
		border: 1px solid #444;
		background: #1e1e2e;
		color: #e0e0e0;
		font-size: 0.95rem;
		min-width: 200px;
		cursor: pointer;
	}

	.filters select:focus {
		outline: none;
		border-color: #6c63ff;
		box-shadow: 0 0 0 2px rgba(108, 99, 255, 0.3);
	}

	/* ── Status Messages ── */
	.status-msg {
		text-align: center;
		color: #888;
		padding: 2rem 0;
		font-size: 1.1rem;
	}

	.status-msg.error {
		color: #ff6b6b;
	}

	/* ── Card Grid ── */
	.card-grid {
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
		gap: 1.25rem;
	}

	/*
	 * CRITICAL: The hover:scale effect is on the entire .ship-card container,
	 * NOT on an inner icon or sub-element. This fixes Issue #38.
	 */
	.ship-card {
		background: linear-gradient(145deg, #1e1e2e, #2a2a3e);
		border: 1px solid #333;
		border-radius: 12px;
		padding: 1.5rem 1rem;
		text-align: center;
		cursor: pointer;

		/* Hover transform on the WHOLE card */
		transition: transform 0.2s ease, box-shadow 0.2s ease;
	}

	.ship-card:hover {
		transform: scale(1.06);
		box-shadow: 0 8px 24px rgba(108, 99, 255, 0.25);
		border-color: #6c63ff;
	}

	.ship-icon {
		font-size: 2.5rem;
		margin-bottom: 0.75rem;
	}

	.ship-name {
		font-size: 1rem;
		font-weight: 600;
		color: #ffffff;
		margin: 0 0 0.35rem 0;
	}

	.ship-faction {
		font-size: 0.8rem;
		color: #aaa;
		margin: 0 0 0.5rem 0;
	}

	.ship-size {
		display: inline-block;
		font-size: 0.7rem;
		padding: 0.2rem 0.6rem;
		background: rgba(108, 99, 255, 0.15);
		color: #8b83ff;
		border-radius: 20px;
		text-transform: uppercase;
		letter-spacing: 0.05em;
	}

	/* ── Responsive ── */
	@media (max-width: 600px) {
		.card-grid {
			grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
		}
	}
</style>
