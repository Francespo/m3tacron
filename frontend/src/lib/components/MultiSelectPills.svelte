<script lang="ts">
    import FilterAnyAllToggle from "./FilterAnyAllToggle.svelte";

    let {
        label,
        options,
        selected = $bindable<string[]>([]),
        mode = $bindable<'any' | 'all'>('any'),
        placeholder = "Select…",
        showMode = true,
        iconTypeFor = undefined as ((v: string) => string) | undefined,
        extra = undefined as any,
    }: {
        label: string;
        options: string[];
        selected?: string[];
        mode?: 'any' | 'all';
        placeholder?: string;
        showMode?: boolean;
        iconTypeFor?: (v: string) => string;
        extra?: import("svelte").Snippet;
    } = $props();

    let search = $state("");
    let open = $state(false);

    let filtered = $derived(
        search
            ? options.filter((o) => o.toLowerCase().includes(search.toLowerCase()))
            : options
    );

    function toggle(opt: string) {
        if (selected.includes(opt)) selected = selected.filter((s) => s !== opt);
        else selected = [...selected, opt];
    }
</script>

<div class="space-y-2">
    <div class="flex items-center justify-between gap-2 flex-wrap">
        <span class="text-[10px] font-bold tracking-widest uppercase font-mono text-secondary/80 flex items-center gap-1.5">
            {label}
            {#if selected.length > 0}
                <span class="min-w-5 h-5 px-1 rounded-full bg-primary text-black text-[10px] font-mono font-bold inline-flex items-center justify-center">{selected.length}</span>
            {/if}
        </span>
        {#if showMode && selected.length > 1}
            <FilterAnyAllToggle bind:value={mode} />
        {:else if extra}
            {@render extra()}
        {/if}
    </div>

    {#if selected.length > 0}
        <div class="flex flex-wrap gap-1.5">
            {#each selected as s}
                <span class="inline-flex items-center gap-1 pl-2 pr-1 py-0.5 rounded-full bg-white/[0.08] border border-white/10 text-[11px] font-mono text-primary">
                    {#if iconTypeFor}
                        <i class="xwing-miniatures-font xwing-miniatures-font-{iconTypeFor(s)} text-[13px] leading-none text-secondary" aria-hidden="true"></i>
                    {/if}
                    {s}
                    <button type="button" onclick={() => toggle(s)} class="w-4 h-4 rounded-full hover:bg-white/15 inline-flex items-center justify-center" aria-label={`Remove ${s}`}>
                        <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 6 6 18"/><path d="m6 6 12 12"/></svg>
                    </button>
                </span>
            {/each}
        </div>
    {/if}

    <div class="relative">
        <input
            type="text"
            placeholder={placeholder}
            class="w-full bg-black border border-border-dark rounded-md px-2 py-1.5 text-xs font-mono text-primary placeholder:text-secondary/40 focus:border-primary focus:outline-none pr-7"
            bind:value={search}
            onfocus={() => (open = true)}
            onblur={() => setTimeout(() => (open = false), 120)}
        />
        <button type="button" class="absolute right-1 top-1/2 -translate-y-1/2 w-6 h-6 rounded inline-flex items-center justify-center text-secondary hover:text-primary" onclick={() => (open = !open)} aria-label="Toggle options">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="transition-transform {open ? 'rotate-180' : ''}"><path d="m6 9 6 6 6-6"/></svg>
        </button>
        {#if open && filtered.length > 0}
            <div class="absolute z-[80] mt-1 w-full max-h-[180px] overflow-y-auto rounded-md border border-border-dark bg-terminal-panel shadow-xl">
                {#each filtered as opt}
                    {@const sel = selected.includes(opt)}
                    <button
                        type="button"
                        onmousedown={(e) => { e.preventDefault(); toggle(opt); }}
                        class="w-full text-left px-2 py-1.5 text-xs font-mono hover:bg-white/[0.06] flex items-center gap-2 {sel ? 'text-primary bg-white/[0.04]' : 'text-secondary'}"
                    >
                        {#if iconTypeFor}
                            <i class="xwing-miniatures-font xwing-miniatures-font-{iconTypeFor(opt)} text-[13px] leading-none shrink-0" aria-hidden="true"></i>
                        {/if}
                        <span class="flex-1">{opt}</span>
                        {#if sel}<svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" class="shrink-0"><path d="M5 12 10 17 19 7"/></svg>{/if}
                    </button>
                {/each}
            </div>
        {/if}
    </div>
</div>
