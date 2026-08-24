<script lang="ts">
  import { onMount } from "svelte";
  import HallOfHeroes from "$lib/components/HallOfHeroes.svelte";
  import { API_BASE } from "$lib/api";
  import { cachedFetchJson } from "$lib/api/cache";

  let supporters: { name: string; message?: string | null; isMonthly?: boolean }[] = $state([]);
  let loading = $state(true);

  let displaySupporters = $derived(supporters);

  // Ko-fi modal: Donate opens an on-site themed window (single click)
  // No floating button in the corner, no double click. Clearly Ko-fi inside, but framed by your site.
  let showKofiModal = $state(false);
  let savedBodyOverflow = "";
  let savedHtmlOverflow = "";
  function openKofiModal(e: MouseEvent) {
    e.preventDefault();
    showKofiModal = true;
    if (typeof document !== "undefined") {
      savedBodyOverflow = document.body.style.overflow;
      savedHtmlOverflow = document.documentElement.style.overflow;
      document.body.style.overflow = "hidden";
      document.documentElement.style.overflow = "hidden";
    }
  }
  function closeKofiModal() {
    showKofiModal = false;
    if (typeof document !== "undefined") {
      document.body.style.overflow = savedBodyOverflow;
      document.documentElement.style.overflow = savedHtmlOverflow;
    }
  }
  function onModalKeydown(e: KeyboardEvent) {
    if (e.key === "Escape") closeKofiModal();
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
  });
</script>

<svelte:head>
  <title>Support M3taCron</title>
</svelte:head>

<div
  class="mx-auto flex min-h-screen max-w-7xl flex-col gap-6 px-6 py-8 lg:py-8"
>

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
          If you choose to support the project, thank you. It means a lot for me
          and helps keep the website running. You can share your name to appear
          among the supporters, or stay anonymous behind a cloaking device.
          <br /><em>May the Force be with you, always.</em>
        </p>
      </div>

      <div class="mb-2 flex justify-center relative group">
        <button
          type="button"
          onclick={openKofiModal}
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
        </button>
      </div>
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
        {#if loading}
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

  {#if showKofiModal}
    <!-- svelte-ignore a11y_click_events_have_key_events -->
    <!-- svelte-ignore a11y_no_static_element_interactions -->
    <div
      class="fixed inset-0 z-[200] flex flex-col bg-black/80 backdrop-blur-sm overscroll-contain touch-manipulation"
      onclick={closeKofiModal}
      onkeydown={onModalKeydown}
      role="dialog"
      aria-modal="true"
      aria-label="Support on Ko-fi"
      tabindex="-1"
    >
      <div
        class="flex min-h-0 w-full flex-1 flex-col overflow-hidden bg-[#111] sm:mx-auto sm:my-4 sm:max-h-[min(92dvh,860px)] sm:max-w-[560px] sm:rounded-2xl sm:border sm:border-primary/20 sm:shadow-[0_0_40px_rgba(0,0,0,0.8)]"
        onclick={(e) => e.stopPropagation()}
      >
        <div class="flex shrink-0 items-center justify-between border-b border-border-dark/50 bg-[#111] px-4 py-3">
          <span class="text-xs font-mono uppercase tracking-[0.2em] text-secondary">Support on Ko-fi</span>
          <button
            type="button"
            onclick={closeKofiModal}
            class="rounded p-1 text-secondary hover:bg-white/10 hover:text-primary"
            aria-label="Close"
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 6 6 18"/><path d="m6 6 12 12"/></svg>
          </button>
        </div>
        <div class="min-h-0 flex-1 overflow-y-auto overscroll-contain bg-white touch-manipulation [-webkit-overflow-scrolling:touch]">
          <iframe
            src="https://ko-fi.com/francespo/?hidefeed=true&widget=true&embed=true"
            style="border:none;width:100%;display:block;background:white;min-height:560px;"
            height="760"
            title="Support on Ko-fi"
            loading="eager"
            allow="payment *; storage-access *; clipboard-write *; fullscreen *"
            scrolling="no"
            referrerpolicy="strict-origin-when-cross-origin"
          ></iframe>
        </div>
        <div class="shrink-0 border-t border-border-dark/30 bg-black/60 px-4 py-2 text-center">
          <p class="text-[9px] font-mono text-secondary/40">Monthly support needs a free Ko-fi account to renew. One-time tips work as guest.</p>
          <a href="https://ko-fi.com/francespo" target="_blank" rel="noopener noreferrer" class="text-[10px] font-mono text-secondary/40 hover:text-primary">Open in Ko-fi instead</a>
        </div>
      </div>
    </div>
  {/if}
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
