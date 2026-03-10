<script lang="ts">
    import { onMount } from "svelte";
    import EvolutionProgressBar from "$lib/components/EvolutionProgressBar.svelte";
    import HallOfHeroes from "$lib/components/HallOfHeroes.svelte";
    import { API_BASE } from "$lib/api";

    let fundStatus = $state({ total_raised: 0, tiers: [] });
    let supporters = $state([]);
    let loading = $state(true);

    async function fetchData() {
        try {
            const [statusRes, supportersRes] = await Promise.all([
                fetch(`${API_BASE}/support/fund-status`),
                fetch(`${API_BASE}/support/supporters`),
            ]);
            fundStatus = await statusRes.json();
            supporters = await supportersRes.json();
        } catch (e) {
            console.error("Failed to fetch support data", e);
        } finally {
            loading = false;
        }
    }

    onMount(() => {
        fetchData();
    });
</script>

<svelte:head>
    <title>Support M3taCron | Maintenance & Evolution</title>
</svelte:head>

<div
    class="max-w-7xl mx-auto px-6 py-8 lg:py-12 h-screen flex flex-col overflow-hidden gap-8"
>
    <!-- Header Section -->
    <header class="text-center shrink-0">
        <h1
            class="text-4xl md:text-6xl font-mono font-bold tracking-tighter uppercase"
        >
            Keeping <span class="text-secondary/20 font-light italic"
                >M3taCron</span
            >
            Alive
        </h1>
    </header>

    <div
        class="grid grid-cols-1 lg:grid-cols-12 gap-12 lg:gap-16 items-start flex-1 overflow-hidden"
    >
        <!-- Left Column (2/3) -->
        <section
            class="lg:col-span-8 flex flex-col h-full overflow-y-auto pr-4 custom-scrollbar"
        >
            <p
                class="text-secondary/80 text-base md:text-lg leading-relaxed mb-10 font-sans italic"
            >
                M3taCron is a labor of love for the community. I dedicate a huge
                chunk of my free time to keeping this station fully operational,
                far from the grasp of the Empire (and ad services). Your support
                helps pay for hosting and keeps the hyperspace lanes open.
                Donating Galactic Credits is entirely optional—contribute only
                if you truly want to help fuel the hyperdrive and improve this
                terminal!
            </p>

            <div class="mb-16 flex justify-start">
                <a
                    href="https://ko-fi.com/m3tacron"
                    target="_blank"
                    rel="noopener noreferrer"
                    class="group relative inline-flex px-12 py-6 bg-primary text-terminal-bg font-mono font-bold uppercase tracking-[0.2em] text-lg transition-all hover:scale-[1.02] active:scale-[0.98] overflow-hidden"
                >
                    <span class="relative z-10 flex items-center gap-4">
                        <span class="text-2xl">☕</span>
                        Treat me to a coffee
                    </span>
                    <!-- Hover glow -->
                    <div
                        class="absolute inset-0 bg-white shadow-[0_0_30px_rgba(255,255,255,0.6)] opacity-0 group-hover:opacity-100 transition-opacity duration-300"
                    ></div>
                </a>
            </div>

            <div class="flex flex-col">
                <div class="flex items-center gap-4 mb-8">
                    <h2
                        class="text-lg font-mono font-bold uppercase tracking-[0.3em] shrink-0"
                    >
                        Community Fund
                    </h2>
                    <div
                        class="h-[1px] flex-1 bg-gradient-to-r from-border-dark to-transparent"
                    ></div>
                </div>

                {#if loading}
                    <div class="space-y-12 opacity-20">
                        {#each Array(3) as _}
                            <div class="space-y-4">
                                <div class="flex justify-between">
                                    <div
                                        class="h-4 w-32 bg-secondary/20 rounded"
                                    ></div>
                                    <div
                                        class="h-4 w-16 bg-secondary/20 rounded"
                                    ></div>
                                </div>
                                <div
                                    class="h-3 w-full bg-terminal-panel border border-border-dark"
                                ></div>
                            </div>
                        {/each}
                    </div>
                {:else}
                    <EvolutionProgressBar tiers={fundStatus.tiers} />
                {/if}
            </div>
        </section>

        <!-- Right Column (1/3) -->
        <section class="lg:col-span-4 flex flex-col h-full overflow-hidden">
            <div class="flex items-center gap-4 mb-8">
                <h2
                    class="text-lg font-mono font-bold uppercase tracking-[0.3em] shrink-0 text-secondary"
                >
                    Hall of Heroes
                </h2>
                <div
                    class="h-[1px] flex-1 bg-gradient-to-r from-border-dark to-transparent"
                ></div>
            </div>

            <div class="space-y-4 overflow-y-auto pr-2 custom-scrollbar flex-1">
                {#if loading}
                    <div class="space-y-4 opacity-10">
                        {#each Array(6) as _}
                            <div
                                class="h-20 bg-terminal-panel border border-border-dark"
                            ></div>
                        {/each}
                    </div>
                {:else}
                    <HallOfHeroes {supporters} />
                {/if}
            </div>

            {#if !loading && supporters.length > 0}
                <div class="mt-8 text-center shrink-0">
                    <p
                        class="text-[9px] text-secondary/30 font-mono tracking-widest uppercase italic max-w-xs mx-auto"
                    >
                        Recognizing the most recent champions. Anonymous
                        donations are encrypted and hidden from the terminal.
                    </p>
                </div>
            {/if}
        </section>
    </div>
</div>

<style>
    /* Global background scanner effect footprint is kept, animation removed */
    :global(body) {
        background-image: radial-gradient(
                circle at 50% 0%,
                rgba(255, 255, 255, 0.02) 0%,
                transparent 50%
            ),
            linear-gradient(rgba(10, 10, 10, 1) 0%, rgba(0, 0, 0, 1) 100%);
    }
</style>
