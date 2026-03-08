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

<div class="max-w-6xl mx-auto px-6 py-12 lg:py-24">
    <!-- Hero Section -->
    <header class="mb-24 text-center relative">
        <!-- Subtle background element -->
        <div
            class="absolute -top-24 left-1/2 -translate-x-1/2 w-96 h-96 bg-primary/5 blur-[120px] rounded-full -z-10"
        ></div>

        <div
            class="inline-flex items-center gap-2 px-3 py-1 border border-primary/20 bg-primary/5 text-[10px] uppercase tracking-[0.4em] text-secondary/70 mb-8 font-mono"
        >
            <span class="w-1.5 h-1.5 bg-primary rounded-full animate-pulse"
            ></span>
            Project Sustainability Protocol
        </div>

        <h1
            class="text-5xl md:text-7xl font-mono font-bold tracking-tighter mb-8 uppercase"
        >
            Support <span class="text-secondary/20 font-light italic">the</span>
            Evolution
        </h1>

        <p
            class="text-secondary/80 max-w-2xl mx-auto text-sm md:text-lg leading-relaxed mb-12 font-sans"
        >
            M3taCron is built by the community, for the community. We are 100%
            independent, ad-free, and open-source. Your contributions directly
            fund our infrastructure and new feature development.
        </p>

        <div
            class="flex flex-col sm:flex-row items-center justify-center gap-8"
        >
            <a
                href="https://ko-fi.com/m3tacron"
                target="_blank"
                rel="noopener noreferrer"
                class="group relative px-12 py-5 bg-primary text-terminal-bg font-mono font-bold uppercase tracking-[0.2em] text-sm transition-all hover:scale-[1.02] active:scale-[0.98] overflow-hidden"
            >
                <span class="relative z-10 flex items-center gap-3">
                    <span class="text-lg">☕</span>
                    Contribute via Ko-fi
                </span>
                <!-- Hover glow -->
                <div
                    class="absolute inset-0 bg-white shadow-[0_0_30px_rgba(255,255,255,0.6)] opacity-0 group-hover:opacity-100 transition-opacity duration-300"
                ></div>
            </a>

            <div class="text-left py-2 pl-8 border-l border-border-dark">
                <div
                    class="text-[10px] text-secondary/40 uppercase tracking-[0.3em] mb-1 font-mono"
                >
                    Current Standing
                </div>
                <div
                    class="text-3xl font-mono font-bold tracking-tighter text-primary flex items-baseline gap-2"
                >
                    ${fundStatus.total_raised.toFixed(0)}
                    <span
                        class="text-xs text-secondary/40 italic font-normal uppercase tracking-widest"
                        >Total Raised</span
                    >
                </div>
            </div>
        </div>
    </header>

    <div class="grid grid-cols-1 lg:grid-cols-12 gap-16 lg:gap-24 items-start">
        <!-- Evolution Fund Column -->
        <section class="lg:col-span-7">
            <div class="flex items-center gap-6 mb-12">
                <h2
                    class="text-xl font-mono font-bold uppercase tracking-[0.3em] shrink-0"
                >
                    Evolution Fund
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

            <!-- Why Support box -->
            <div class="mt-16 relative overflow-hidden">
                <div class="absolute inset-0 bg-terminal-panel/30 -z-10"></div>
                <div
                    class="absolute top-0 left-0 w-1 h-full bg-primary/20"
                ></div>

                <div class="p-8 border border-border-dark/50">
                    <h4
                        class="text-xs font-mono font-bold uppercase text-primary/80 mb-6 tracking-[0.4em] flex items-center gap-3"
                    >
                        <span class="text-primary tracking-tighter">[!]</span>
                        Why Support M3taCron?
                    </h4>

                    <div class="grid grid-cols-1 md:grid-cols-2 gap-8">
                        <div class="space-y-2">
                            <span
                                class="text-[10px] font-mono text-primary/40 uppercase tracking-widest block"
                                >01 / Transparency</span
                            >
                            <p
                                class="text-[11px] text-secondary leading-relaxed"
                            >
                                Every contribution is tracked and accounted for.
                                We show exactly how the funds are distributed
                                across hosting and development.
                            </p>
                        </div>
                        <div class="space-y-2">
                            <span
                                class="text-[10px] font-mono text-primary/40 uppercase tracking-widest block"
                                >02 / Independence</span
                            >
                            <p
                                class="text-[11px] text-secondary leading-relaxed"
                            >
                                No ads, no trackers, no selling data. Community
                                support ensures M3taCron remains a tool for
                                players, not for profit.
                            </p>
                        </div>
                        <div class="space-y-2">
                            <span
                                class="text-[10px] font-mono text-primary/40 uppercase tracking-widest block"
                                >03 / Longevity</span
                            >
                            <p
                                class="text-[11px] text-secondary leading-relaxed"
                            >
                                Funding base infrastructure ensures M3taCron
                                stays online for years to come, preserving the
                                history of X-Wing competition.
                            </p>
                        </div>
                        <div class="space-y-2">
                            <span
                                class="text-[10px] font-mono text-primary/40 uppercase tracking-widest block"
                                >04 / Development</span
                            >
                            <p
                                class="text-[11px] text-secondary leading-relaxed"
                            >
                                Reaching milestones unlocks complex new features
                                like automated discord alerts, better analytics,
                                and deeper list insights.
                            </p>
                        </div>
                    </div>
                </div>
            </div>
        </section>

        <!-- Hall of Heroes Column -->
        <section class="lg:col-span-5">
            <div class="flex items-center gap-6 mb-12">
                <h2
                    class="text-xl font-mono font-bold uppercase tracking-[0.3em] shrink-0 text-secondary"
                >
                    Hall of Heroes
                </h2>
                <div
                    class="h-[1px] flex-1 bg-gradient-to-r from-border-dark to-transparent"
                ></div>
            </div>

            <div class="space-y-6">
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
                <div class="mt-12 text-center">
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
    /* Background scanner effect */
    :global(body) {
        background-image: radial-gradient(
                circle at 50% 0%,
                rgba(255, 255, 255, 0.02) 0%,
                transparent 50%
            ),
            linear-gradient(rgba(10, 10, 10, 1) 0%, rgba(0, 0, 0, 1) 100%);
    }

    /* Subtle shimmer for the hero section */
    header::before {
        content: "";
        position: absolute;
        top: -50%;
        left: -50%;
        width: 200%;
        height: 200%;
        background: radial-gradient(
            circle at center,
            rgba(255, 255, 255, 0.01) 0%,
            transparent 70%
        );
        pointer-events: none;
        animation: drift 20s linear infinite;
    }

    @keyframes drift {
        from {
            transform: translate(-10%, -10%) rotate(0deg);
        }
        to {
            transform: translate(10%, 10%) rotate(360deg);
        }
    }
</style>
