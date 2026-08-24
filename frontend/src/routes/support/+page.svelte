<script lang="ts">
  import { onMount } from "svelte";
  import HallOfHeroes from "$lib/components/HallOfHeroes.svelte";
  import { API_BASE } from "$lib/api";
  import { cachedFetchJson } from "$lib/api/cache";

  let supporters: { name: string; message?: string | null }[] = $state([]);
  let loading = $state(true);

  // Dev-only preview to demo the empty vs populated states on this stack
  // Messages are shown only if you approve them; preview shows both with and without
  type PreviewMode = "live" | "empty" | "below" | "above";
  let previewMode: PreviewMode = $state("live");
  const previewData: Record<Exclude<PreviewMode, "live">, typeof supporters> = {
    empty: [],
    below: [
      { name: "Wedge Antilles", message: "Thanks for the site!" },
      { name: "Hera Syndulla", message: null },
    ],
    above: [
      { name: "Wedge Antilles", message: "Thanks for keeping the droids working!" },
      { name: "Hera Syndulla", message: null },
      { name: "Cassian Andor", message: "For the Rebellion" },
      { name: "Ahsoka Tano", message: "May the Force be with this project" },
      { name: "K-2SO", message: null },
    ],
  };

  let displaySupporters = $derived(
    previewMode === "live" ? supporters : previewData[previewMode],
  );

  // Ko-fi overlay popup preview (?popup=1): Donate opens a themed Ko-fi overlay instead of navigating away
  let kofiReady = $state(false);
  let kofiLoading = $state(false);
  function loadKofiOverlay(): Promise<void> {
    if (kofiReady) return Promise.resolve();
    if (kofiLoading) return new Promise<void>((resolve) => {
      const i = setInterval(() => {
        if (kofiReady) { clearInterval(i); resolve(); }
      }, 100);
    });
    kofiLoading = true;
    return new Promise<void>((resolve, reject) => {
      const script = document.createElement("script");
      script.src = "https://storage.ko-fi.com/cdn/scripts/overlay-widget.js";
      script.async = true;
      script.onload = () => { kofiReady = true; kofiLoading = false; resolve(); };
      script.onerror = () => { kofiLoading = false; reject(new Error("Ko-fi overlay failed to load")); };
      document.body.appendChild(script);
    });
  }

  function openKofiPopup(e: MouseEvent) {
    const params = new URLSearchParams(window.location.search);
    if (params.get("popup") !== "1") return; // let normal link navigation happen
    e.preventDefault();
    loadKofiOverlay().then(() => {
      const w = window as unknown as { kofiWidgetOverlay?: { draw: (id: string, opts: Record<string, string>) => void } };
      if (!w.kofiWidgetOverlay) return;
      // Draw themed overlay; button colors match site primary
      w.kofiWidgetOverlay.draw("francespo", {
        type: "floating-chat",
        "floating-chat.donateButton.text": "Support M3taCron",
        "floating-chat.donateButton.background-color": "#e5c07a",
        "floating-chat.donateButton.text-color": "#0a0a0a",
      });
      // The widget injects a floating container; trigger its click to open immediately
      setTimeout(() => {
        const btn = document.querySelector<HTMLElement>(".floatingchat-container-wrap [role='button'], .floatingchat-container-wrap button, #kofi-wo-container button");
        if (btn) btn.click();
        else {
          // Fallback: trigger the floating button if selector differs
          const alt = document.querySelector<HTMLElement>("[id*='kofi'] button, .kofi-button");
          if (alt) alt.click();
        }
      }, 300);
    }).catch(() => {
      window.open("https://ko-fi.com/francespo", "_blank", "noopener");
    });
  }

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
    // Preload overlay script in popup preview so first click is instant
    if (typeof window !== "undefined" && new URLSearchParams(window.location.search).get("popup") === "1") {
      loadKofiOverlay().catch(() => {});
    }
  });
</script>

<svelte:head>
  <title>Support M3taCron</title>
</svelte:head>

<div
  class="mx-auto flex min-h-screen max-w-7xl flex-col gap-6 px-6 py-8 lg:py-8"
>
  <!-- Dev preview toggles (only shown when ?preview=1, ?embed=1 or ?popup=1) -->
  {#if typeof window !== "undefined" && (new URLSearchParams(window.location.search).get("preview") === "1" || new URLSearchParams(window.location.search).get("embed") === "1" || new URLSearchParams(window.location.search).get("popup") === "1")}
    <div class="shrink-0 flex flex-wrap justify-center gap-2 text-[10px] font-mono">
      {#each [["live", "Live"], ["empty", "0 — empty"], ["below", "2 — below"], ["above", "5 — above"]] as [mode, label]}
        <button
          type="button"
          onclick={() => (previewMode = mode as PreviewMode)}
          class="px-2 py-1 rounded border transition-colors {previewMode === mode
            ? 'bg-primary text-terminal-bg border-primary'
            : 'bg-transparent text-secondary border-border-dark hover:border-primary/40'}"
        >{label}</button>
      {/each}
      <span class="ml-2 self-center text-secondary/40">preview</span>
      {#if typeof window !== "undefined" && new URLSearchParams(window.location.search).get("embed") === "1"}
        <span class="ml-2 self-center rounded bg-secondary/20 px-2 py-0.5 text-secondary">embed preview active</span>
      {/if}
      {#if typeof window !== "undefined" && new URLSearchParams(window.location.search).get("popup") === "1"}
        <span class="ml-2 self-center rounded bg-primary/20 px-2 py-0.5 text-primary">popup preview active — Donate opens themed Ko-fi overlay</span>
      {/if}
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
        Empire's reach and annoying ad networks. It is free to use, but keeping
        the lights on and the droids working costs credits, if you use it often
        and find it useful, a little help goes a long way.
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
          helps keep the website running. You can share your name to appear
          among the supporters, or stay anonymous behind a cloaking device.
          <br /><em>May the Force be with you, always.</em>
        </p>
      </div>

      <div class="mb-2 flex justify-center relative group">
        <a
          href="https://ko-fi.com/francespo"
          target="_blank"
          rel="noopener noreferrer"
          onclick={openKofiPopup}
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

      {#if typeof window !== "undefined" && new URLSearchParams(window.location.search).get("embed") === "1"}
        <div class="mt-8 w-full flex flex-col gap-2">
          <p class="text-center text-[10px] font-mono uppercase tracking-widest text-secondary/40">Inline Ko-fi widget preview (embed=1)</p>
          <div class="overflow-hidden rounded-xl border border-primary/20 bg-primary/5 p-2">
            <iframe
              src="https://ko-fi.com/francespo/?hidefeed=true&widget=true&embed=true"
              style="border:none;width:100%;padding:0;background:transparent;display:block;"
              height="712"
              title="Support on Ko-fi"
              loading="lazy"
            ></iframe>
          </div>
          <p class="text-center text-[10px] font-mono text-secondary/30">Compare with the Donate button above. The iframe is light-themed and cannot be recolored.</p>
        </div>
      {/if}
    </section>

    <!-- Galactic Patrons: always below donation so placement is clear -->
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
          <div class="grid grid-cols-2 gap-3 opacity-10 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5">
            {#each Array(6) as _}
              <div
                class="h-14 rounded-xl border border-border-dark bg-terminal-panel"
              ></div>
            {/each}
          </div>
        {:else}
          <HallOfHeroes supporters={displaySupporters} />
        {/if}
      </div>
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
