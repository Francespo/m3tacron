<script lang="ts">
  import { onMount } from "svelte";
  import HallOfHeroes from "$lib/components/HallOfHeroes.svelte";
  import { API_BASE } from "$lib/api";
  import { cachedFetchJson } from "$lib/api/cache";

  let supporters: { name: string; amount: number; date: string; message?: string | null }[] = $state([]);
  let loading = $state(true);
  const SUPPORTER_THRESHOLD = 3;

  // Dev-only preview to demo the threshold states on this stack
  type PreviewMode = "live" | "empty" | "below" | "above";
  let previewMode: PreviewMode = $state("live");
  const previewData: Record<Exclude<PreviewMode, "live">, typeof supporters> = {
    empty: [],
    below: [
      { name: "Wedge Antilles", amount: 5, date: new Date().toISOString(), message: "Thanks for the site!" },
      { name: "Hera Syndulla", amount: 10, date: new Date().toISOString(), message: null },
    ],
    above: [
      { name: "Wedge Antilles", amount: 5, date: new Date().toISOString(), message: "Thanks for keeping the station alive!" },
      { name: "Hera Syndulla", amount: 10, date: new Date().toISOString(), message: null },
      { name: "Cassian Andor", amount: 20, date: new Date().toISOString(), message: "For the Rebellion" },
      { name: "Ahsoka Tano", amount: 15, date: new Date().toISOString(), message: "May the Force be with this project" },
      { name: "K-2SO", amount: 3, date: new Date().toISOString(), message: null },
    ],
  };

  let displaySupporters = $derived(
    previewMode === "live" ? supporters : previewData[previewMode],
  );
  let showSupporters = $derived(displaySupporters.length >= SUPPORTER_THRESHOLD);

  async function fetchData() {
    try {
      const data = await cachedFetchJson(`${API_BASE}/support/supporters`);
      supporters = Array.isArray(data) ? data : [];
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
  <title>Support M3taCron</title>
</svelte:head>

<div
  class="mx-auto flex min-h-screen max-w-7xl flex-col gap-6 px-6 py-8 lg:py-8"
>
  <!-- Dev preview toggle (only shown when ?preview=1) -->
  {#if typeof window !== "undefined" && new URLSearchParams(window.location.search).get("preview") === "1"}
    <div class="shrink-0 flex justify-center gap-2 text-[10px] font-mono">
      {#each [["live", "Live"], ["empty", "0 — empty"], ["below", "2 — below"], ["above", "5 — above"]] as [mode, label]}
        <button
          type="button"
          onclick={() => (previewMode = mode as PreviewMode)}
          class="px-2 py-1 rounded border transition-colors {previewMode === mode
            ? 'bg-primary text-terminal-bg border-primary'
            : 'bg-transparent text-secondary border-border-dark hover:border-primary/40'}"
        >{label}</button>
      {/each}
      <span class="ml-2 self-center text-secondary/40">threshold = {SUPPORTER_THRESHOLD}</span>
    </div>
  {/if}

  <!-- Header Section -->
    <header class="shrink-0 text-center">
    <h1
      class="text-4xl font-mono font-bold uppercase tracking-tighter leading-none md:text-5xl lg:text-5xl xl:text-6xl"
    >
      Keeping <span class="text-secondary/80">M3taCron</span>
      Alive
    </h1>
  </header>

  <div class="flex flex-col gap-10">
    <!-- Main donation block: centered, full width -->
    <section class="mx-auto w-full max-w-3xl flex flex-col items-center">
      <p
        class="mb-4 text-center font-sans text-base italic leading-relaxed text-secondary/80 md:mb-6"
      >
        I build M3taCron with passion in my spare time, far from the
        Empire's reach and annoying ad networks. The station is free to use.
        Keeping the lights on and the droids working still takes resources, and
        a little help goes a long way.
      </p>

      <div
        class="mb-8 flex w-full flex-col items-center gap-2 rounded-sm border border-primary/20 bg-primary/5 px-5 py-4 text-center"
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
        <p class="text-[13px] text-secondary/90 leading-relaxed font-sans">
          If you choose to support the project, thank you. It means a lot and
          helps keep the station running. You can share your name to appear
          among the supporters, or stay anonymous behind a cloaking device.
          <br /><em>May the Force be with you, always.</em>
        </p>
      </div>

      <div class="mb-2 flex justify-center relative group">
        <a
          href="https://ko-fi.com/francespo"
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
              /><path d="m18 15-2-2" /><path d="m15 18-2-2" /></svg
            >
            Donate
          </span>
          <!-- Hover glow -->
          <div
            class="absolute inset-0 bg-white shadow-[0_0_30px_rgba(255,255,255,0.6)] opacity-0 group-hover:opacity-100 transition-opacity duration-300"
          ></div>
        </a>
      </div>
    </section>

    <!-- Galactic Patrons: below the donation, only after threshold -->
    {#if loading || showSupporters}
      <section class="flex flex-col">
        <div class="mb-6 flex items-center gap-4">
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

        <div class="space-y-4">
          {#if loading && previewMode === "live"}
            <div class="grid grid-cols-1 gap-4 opacity-10 sm:grid-cols-2 lg:grid-cols-3">
              {#each Array(6) as _}
                <div
                  class="h-20 bg-terminal-panel border border-border-dark"
                ></div>
              {/each}
            </div>
          {:else}
            <HallOfHeroes supporters={displaySupporters} />
          {/if}
        </div>
      </section>
    {/if}
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
