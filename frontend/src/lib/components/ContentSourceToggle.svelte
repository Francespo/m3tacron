<script lang="ts">
  import { filters } from "$lib/stores/filters.svelte";

  function setSource(src: "xwa" | "legacy") {
    filters.dataSource = src;
  }
</script>

<div class="w-full space-y-2">
  <span class="text-xs font-bold tracking-widest text-primary font-mono">
    GAME CONTENT SOURCE
  </span>

  <!-- Segmented Control -->
  <div
    class="flex w-full bg-black border border-border-dark rounded-md overflow-hidden"
  >
    <button
      class="flex-1 min-h-11 py-1.5 text-xs font-mono text-center transition-colors {filters.dataSource ===
      'xwa'
        ? 'bg-[#ffffff14] text-primary font-bold'
        : 'text-secondary hover:text-primary'}"
      onclick={() => setSource("xwa")}
    >
      XWA
    </button>
    <button
      class="flex-1 min-h-11 py-1.5 text-xs font-mono text-center transition-colors {filters.dataSource ===
      'legacy'
        ? 'bg-[#ffffff14] text-primary font-bold'
        : 'text-secondary hover:text-primary'}"
      onclick={() => setSource("legacy")}
    >
      Legacy
    </button>
  </div>

  <!-- Epic Checkbox -->
  <label
    class="flex items-center gap-2 py-1.5 min-h-11 cursor-pointer text-sm text-secondary hover:text-primary transition-colors"
  >
    <input
      type="checkbox"
      class="rounded border-border-dark bg-black accent-primary w-4 h-4"
      bind:checked={filters.includeEpic}
    />
    <span class="font-mono text-xs">Include Epic Content</span>
  </label>
</div>
