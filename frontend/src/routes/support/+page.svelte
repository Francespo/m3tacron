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
            Keeping <span class="text-secondary/80">M3taCron</span>
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
                class="text-secondary/80 text-base md:text-lg leading-relaxed mb-6 font-sans italic"
            >
                M3taCron runs on passion, community, and free time, far from the
                Empire's reach and annoying ad networks. This station is free,
                but keeping it alive requires resources. Every donation goes
                straight to covering monthly server costs first, while any
                overflow fuels new development!
            </p>

            <div
                class="flex items-center gap-3 mb-10 py-4 px-5 border border-primary/20 bg-primary/5 rounded-sm"
            >
                <!-- Lucide Heart Icon -->
                <svg
                    xmlns="http://www.w3.org/2000/svg"
                    width="24"
                    height="24"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    stroke-width="2"
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    class="w-5 h-5 text-secondary/80 shrink-0 opacity-80"
                    ><path
                        d="M19 14c1.49-1.46 3-3.21 3-5.5A5.5 5.5 0 0 0 16.5 3c-1.76 0-3 .5-4.5 2-1.5-1.5-2.74-2-4.5-2A5.5 5.5 0 0 0 2 8.5c0 2.3 1.5 4.05 3 5.5l7 7Z"
                    /></svg
                >
                <p
                    class="text-[13px] text-secondary/90 leading-relaxed font-sans self-center"
                >
                    To those who decide to support the project monthly: thank
                    you! As a gesture of gratitude, you'll have a direct channel
                    to discuss new feature requests with me. If they fit the
                    system, I'll make them a priority.
                    <br /><em>May the Force be with you, always.</em>
                </p>
            </div>

            <div class="mb-16 flex justify-center relative group">
                <a
                    href="https://ko-fi.com/m3tacron"
                    target="_blank"
                    rel="noopener noreferrer"
                    class="relative inline-flex px-12 py-6 bg-primary text-terminal-bg font-mono font-bold uppercase tracking-[0.2em] text-lg transition-all hover:scale-[1.02] active:scale-[0.98] overflow-hidden animate-heartbeat hover:![animation-play-state:paused] rounded-xl"
                >
                    <span class="relative z-10 flex items-center gap-4">
                        <svg
                            xmlns="http://www.w3.org/2000/svg"
                            width="24"
                            height="24"
                            viewBox="0 0 24 24"
                            fill="none"
                            stroke="currentColor"
                            stroke-width="2"
                            stroke-linecap="round"
                            stroke-linejoin="round"
                            class="w-6 h-6"
                            ><path
                                d="M19 14c1.49-1.46 3-3.21 3-5.5A5.5 5.5 0 0 0 16.5 3c-1.76 0-3 .5-4.5 2-1.5-1.5-2.74-2-4.5-2A5.5 5.5 0 0 0 2 8.5c0 2.3 1.5 4.05 3 5.5l7 7Z"
                            /><path
                                d="M12 5 9.04 7.96a2.17 2.17 0 0 0 0 3.08v0c.82.82 2.13.85 3 .07l2.07-1.9a2.82 2.82 0 0 1 3.79 0l2.96 2.66"
                            /><path d="m18 15-2-2" /><path
                                d="m15 18-2-2"
                            /></svg
                        >
                        Donate
                    </span>
                    <!-- Hover glow -->
                    <div
                        class="absolute inset-0 bg-white shadow-[0_0_30px_rgba(255,255,255,0.6)] opacity-0 group-hover:opacity-100 transition-opacity duration-300"
                    ></div>
                </a>
            </div>

            <div class="flex flex-col mt-auto pt-10">
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
        <section class="lg:col-span-4 flex flex-col h-full">
            <div class="flex items-center gap-4 mb-8">
                <div
                    class="h-[1px] flex-1 bg-gradient-to-l from-secondary/30 to-transparent"
                ></div>
                <h2
                    class="text-lg font-mono font-bold uppercase tracking-[0.3em] shrink-0 text-secondary"
                >
                    Galactic Patrons
                </h2>
                <div
                    class="h-[1px] flex-1 bg-gradient-to-r from-secondary/30 to-transparent"
                ></div>
            </div>

            <div
                class="space-y-4 overflow-y-auto pr-2 custom-scrollbar flex-1 mb-4"
            >
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
                <div
                    class="text-center shrink-0 border-t border-border-dark/30 pt-6"
                >
                    <p
                        class="text-[9px] text-secondary/30 font-mono tracking-widest uppercase italic max-w-xs mx-auto"
                    >
                        Honoring the galaxy's brightest sparks. Heroes who
                        prefer to stay anonymous are protected by a cloaking
                        device.
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

    @keyframes heartbeat {
        0%,
        100% {
            transform: scale(1);
        }
        50% {
            transform: scale(1.05);
            box-shadow: 0 0 25px rgba(255, 255, 255, 0.4);
        }
    }

    .animate-heartbeat {
        animation: heartbeat 2.5s ease-in-out infinite;
    }
</style>
