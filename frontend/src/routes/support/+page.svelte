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
    class="max-w-6xl mx-auto px-6 py-8 lg:py-12 h-screen flex flex-col justify-center overflow-hidden"
>
    <!-- Hero Section -->
    <header class="mb-12 text-center relative">
        <!-- Subtle background element -->
        <div
            class="absolute -top-24 left-1/2 -translate-x-1/2 w-96 h-96 bg-primary/5 blur-[120px] rounded-full -z-10"
        ></div>

        <div
            class="inline-flex items-center gap-2 px-3 py-1 border border-primary/20 bg-primary/5 text-[10px] uppercase tracking-[0.4em] text-secondary/70 mb-8 font-mono"
        >
            <span class="w-1.5 h-1.5 bg-primary rounded-full animate-pulse"
            ></span>
            Community heartbeat
        </div>

        <h1
            class="text-4xl md:text-6xl font-mono font-bold tracking-tighter mb-6 uppercase"
        >
            Keeping <span class="text-secondary/20 font-light italic"
                >M3taCron</span
            >
            Alive
        </h1>

        <p
            class="text-secondary/80 max-w-2xl mx-auto text-sm md:text-base leading-relaxed mb-8 font-sans italic"
        >
            M3taCron is a labor of love for the community. I dedicate a huge
            chunk of my free time to keeping this station fully operational, far
            from the grasp of the Empire (and ad services). Your support helps
            pay for hosting and keeps the hyperspace lanes open. Donating
            Galactic Credits is entirely optional—contribute only if you truly
            want to help fuel the hyperdrive and improve this terminal!
        </p>

        <div class="flex items-center justify-center">
            <a
                href="https://ko-fi.com/m3tacron"
                target="_blank"
                rel="noopener noreferrer"
                class="group relative px-10 py-4 bg-primary text-terminal-bg font-mono font-bold uppercase tracking-[0.2em] text-sm transition-all hover:scale-[1.02] active:scale-[0.98] overflow-hidden"
            >
                <span class="relative z-10 flex items-center gap-3">
                    <span class="text-lg">☕</span>
                    Treat me to a coffee
                </span>
                <!-- Hover glow -->
                <div
                    class="absolute inset-0 bg-white shadow-[0_0_30px_rgba(255,255,255,0.6)] opacity-0 group-hover:opacity-100 transition-opacity duration-300"
                ></div>
            </a>
        </div>
    </header>

    <div
        class="grid grid-cols-1 lg:grid-cols-12 gap-12 lg:gap-16 items-start h-full overflow-hidden"
    >
        <!-- Evolution Fund Column -->
        <section class="lg:col-span-7 flex flex-col h-full">
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
        </section>

        <!-- Hall of Heroes Column -->
        <section class="lg:col-span-5 flex flex-col h-full overflow-hidden">
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
