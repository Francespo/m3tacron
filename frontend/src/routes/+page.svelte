<script lang="ts">
	let { data } = $props();
	let snapshot = data.data;

    import { Chart as ChartJS, Title, Tooltip, Legend, BarElement, CategoryScale, LinearScale, ArcElement } from 'chart.js';
    import { Bar, Pie } from 'svelte-chartjs';

    ChartJS.register(Title, Tooltip, Legend, BarElement, CategoryScale, LinearScale, ArcElement);

    // We can use the CSS variables defined in app.css or inline. Using hex directly for Chart.js
    const getFactionColor = (xws: string) => {
        const colors: Record<string, string> = {
            "rebelalliance": "#FF3333",
            "galacticempire": "#2979FF",
            "scumandvillainy": "#006400",
            "resistance": "#FF8C00",
            "firstorder": "#800020",
            "galacticrepublic": "#E6D690",
            "separatistalliance": "#607D8B",
            "unknown": "#666666"
        };
        return colors[xws] || colors["unknown"];
    };

    let popularityData = { labels: [], datasets: [] };
    let winRateData = { labels: [], datasets: [] };
    let distributionData = { labels: [], datasets: [] };

    let barOptions = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: { display: false },
            tooltip: {
                backgroundColor: '#0A0A0A',
                titleColor: '#FFFFFF',
                bodyColor: '#FFFFFF',
                borderColor: '#333333',
                borderWidth: 1,
                titleFont: { family: 'Inter' },
                bodyFont: { family: 'JetBrains Mono' }
            }
        },
        scales: {
            y: { beginAtZero: true, grid: { color: '#222' }, ticks: { color: '#aaa', font: { family: 'JetBrains Mono', size: 10 } } },
            x: { grid: { display: false }, ticks: { color: '#aaa', font: { family: 'Inter', size: 11 } } }
        }
    };

    let pieOptions = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: { display: false },
            tooltip: {
                backgroundColor: '#0A0A0A',
                titleColor: '#FFFFFF',
                bodyColor: '#FFFFFF',
                borderColor: '#333333',
                borderWidth: 1,
                titleFont: { family: 'Inter' },
                bodyFont: { family: 'JetBrains Mono' },
                callbacks: {
                    label: function(context: any) {
                        let label = context.label || '';
                        if (label) { label += ': '; }
                        if (context.parsed !== null) { label += context.parsed + ' games'; }
                        return label;
                    }
                }
            }
        }
    };

    // Calculate max values to normalize heights for bar charts
    let maxPopularity = 1;
    let maxWinRate = 100;
    
    // Prepare chart data reactively
    $effect(() => {
        if (snapshot?.factions) {
            maxPopularity = Math.max(...snapshot.factions.map(f => f.popularity), 1);
            
            popularityData = {
                labels: snapshot.factions.map(f => f.name),
                datasets: [{
                    label: 'Lists',
                    data: snapshot.factions.map(f => f.popularity),
                    backgroundColor: snapshot.factions.map(f => getFactionColor(f.xws)),
                    borderRadius: 4
                }]
            };

            winRateData = {
                labels: snapshot.factions.map(f => f.name),
                datasets: [{
                    label: 'Win Rate %',
                    data: snapshot.factions.map(f => f.win_rate),
                    backgroundColor: snapshot.factions.map(f => getFactionColor(f.xws)),
                    borderRadius: 4
                }]
            };

            distributionData = {
                labels: snapshot.faction_distribution.map(d => d.real_name || d.name),
                datasets: [{
                    data: snapshot.faction_distribution.map(d => d.games),
                    backgroundColor: snapshot.faction_distribution.map(d => getFactionColor(d.xws)),
                    borderWidth: 0
                }]
            };
        }
    });

</script>

{#if data.error}
	<div class="terminal-panel flex items-center justify-center h-48 border-red-800 bg-red-900/20">
		<p class="font-mono text-red-500">ERROR: {data.error}</p>
	</div>
{:else if !snapshot}
	<div class="flex items-center justify-center h-64">
		<p class="font-mono text-secondary animate-pulse">Loading mainframe data...</p>
	</div>
{:else}
	<div class="w-full max-w-[1400px] mx-auto flex flex-col gap-8">
		<!-- Header -->
		<div class="flex flex-col md:flex-row justify-between items-start md:items-end gap-4 w-full">
			<div class="flex flex-col gap-2">
				<h1 class="text-4xl md:text-5xl font-medium tracking-[0.08em] text-primary">META SNAPSHOT</h1>
				<div class="flex flex-wrap items-center gap-2 mt-2">
					<span class="px-2 py-1 bg-white/10 rounded text-xs font-mono">{snapshot.last_sync}</span>
					<span class="text-xs text-secondary font-mono">RANGE: {snapshot.date_range}</span>
				</div>
			</div>
			
			<div class="flex flex-col items-start gap-1">
				<span class="text-xs font-bold text-secondary font-mono">GAME SOURCE</span>
				<div class="flex bg-panel border border-border p-1 rounded-md">
					<button class="px-3 py-1 text-sm bg-white/10 text-primary rounded shadow-sm">XWA</button>
					<button class="px-3 py-1 text-sm text-secondary hover:text-primary rounded">Legacy</button>
				</div>
			</div>
		</div>

		<!-- Stat Cards -->
		<div class="grid grid-cols-1 md:grid-cols-3 gap-4 w-full">
			<div class="terminal-panel flex items-center gap-4">
				<div class="w-12 h-12 flex items-center justify-center rounded bg-white/5 border border-border text-secondary">
					<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M3 5V19A9 3 0 0 0 21 19V5"/><path d="M3 12A9 3 0 0 0 21 12"/></svg>
				</div>
				<div class="flex flex-col">
					<span class="text-xs text-secondary tracking-wider font-bold">RECENT TOURNAMENTS</span>
					<span class="text-3xl font-mono">{snapshot.total_tournaments}</span>
					<span class="text-[10px] text-secondary mt-1">Last 90 Days</span>
				</div>
			</div>
			<div class="terminal-panel flex items-center gap-4">
				<div class="w-12 h-12 flex items-center justify-center rounded bg-white/5 border border-border text-secondary">
					<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>
				</div>
				<div class="flex flex-col">
					<span class="text-xs text-secondary tracking-wider font-bold">RECENT LISTS</span>
					<span class="text-3xl font-mono">{snapshot.total_players}</span>
					<span class="text-[10px] text-secondary mt-1">Last 90 Days</span>
				</div>
			</div>
			<div class="terminal-panel flex items-center gap-4">
				<div class="w-12 h-12 flex items-center justify-center rounded bg-white/5 border border-border text-secondary">
					<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="12 2 2 7 12 12 22 7 12 2"/><polyline points="2 17 12 22 22 17"/><polyline points="2 12 12 17 22 12"/></svg>
				</div>
				<div class="flex flex-col">
					<span class="text-xs text-secondary tracking-wider font-bold">ACTIVE FACTIONS</span>
					<span class="text-3xl font-mono">{snapshot.factions.length}</span>
				</div>
			</div>
		</div>

		<!-- Chart.js Charts Section -->
		<div class="grid grid-cols-1 md:grid-cols-3 gap-4 w-full">
			<!-- Popularity Bar Chart -->
			<div class="terminal-panel flex flex-col gap-4 min-h-64">
				<h2 class="font-bold font-mono text-sm tracking-wider">POPULARITY</h2>
				<div class="flex-1 w-full h-[250px] relative">
					{#if popularityData.labels.length > 0}
                        <Bar data={popularityData} options={barOptions} />
                    {/if}
				</div>
			</div>

			<!-- Win Rates Bar Chart -->
			<div class="terminal-panel flex flex-col gap-4 min-h-64">
				<h2 class="font-bold font-mono text-sm tracking-wider">WIN RATES (%)</h2>
				<div class="flex-1 w-full h-[250px] relative">
					{#if winRateData.labels.length > 0}
                        <Bar data={winRateData} options={barOptions} />
                    {/if}
				</div>
			</div>

			<!-- Distribution Pie Chart -->
			<div class="terminal-panel flex flex-col gap-4 min-h-64">
				<h2 class="font-bold font-mono text-sm tracking-wider">GAME DISTRIBUTION</h2>
				<div class="flex-1 flex flex-col items-center w-full relative">
                    <div class="h-[180px] w-full relative mb-4">
					    {#if distributionData.labels.length > 0}
                            <Pie data={distributionData} options={pieOptions} />
                        {/if}
                    </div>
                    
                    <!-- Legend below pie chart -->
                    <div class="flex flex-wrap items-center justify-center gap-x-4 gap-y-2">
                        {#each snapshot.faction_distribution as dist}
                            <div class="flex items-center gap-1">
                                <span style="color: {getFactionColor(dist.xws)}; font-family: var(--font-xwing);">{dist.icon_char}</span>
                                <span class="text-xs text-secondary font-mono">{dist.percentage}%</span>
                            </div>
                        {/each}
                    </div>
				</div>
			</div>
		</div>
		
		<!-- Lists -->
		<div class="grid grid-cols-1 lg:grid-cols-2 gap-6 w-full">
			<div class="terminal-panel flex flex-col gap-4">
				<h2 class="font-bold flex items-center gap-2">
					<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="12 2 2 7 12 12 22 7 12 2"/><polyline points="2 17 12 22 22 17"/><polyline points="2 12 12 17 22 12"/></svg>
					TOP SQUAD LISTS
				</h2>
				<div class="flex flex-col gap-0 border border-border rounded-md bg-canvas">
					{#each snapshot.lists.slice(0, 5) as item}
						<div class="flex border-b border-border last:border-b-0 hover:bg-white/5 p-3">
							<!-- Simple representation for now -->
							<div class="flex flex-col w-full">
								<div class="flex justify-between w-full">
									<span class="font-bold">{item.faction}</span>
									<span class="font-mono bg-white/10 px-2 rounded">{item.count} Lists</span>
								</div>
								<div class="flex gap-2 flex-wrap text-sm text-secondary font-mono mt-2">
									{#each item.pilots as pilot}
										<span>{pilot.name}</span>
									{/each}
								</div>
							</div>
						</div>
					{/each}
				</div>
			</div>
			<div class="terminal-panel flex flex-col gap-4">
				<h2 class="font-bold flex items-center gap-2">
					<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
					TOP PILOTS
				</h2>
				<div class="flex flex-col gap-0 border border-border rounded-[6px] bg-canvas">
					{#each snapshot.pilots.slice(0, 5) as item, i}
						<div class="flex items-center gap-4 border-b border-border last:border-b-0 p-3">
							<span class="text-secondary font-mono w-4">{i + 1}</span>
							<div class="flex-1 flex flex-col">
								<span class="font-bold">{item.name}</span>
								<span class="text-xs text-secondary font-mono">{item.ship}</span>
							</div>
							<div class="flex flex-col items-end text-sm font-mono">
								<span>{item.popularity} Lists</span>
								<span class="text-xs text-secondary">{item.win_rate}% WR</span>
							</div>
						</div>
					{/each}
				</div>
			</div>
		</div>

	</div>
{/if}
