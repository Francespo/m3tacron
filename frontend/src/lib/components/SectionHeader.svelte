<script lang="ts">
    /**
     * Standard section header: uppercase title with a bottom border,
     * optional count chip and optional small subtitle.
     */
    let {
        title,
        count = undefined as number | string | undefined,
        subtitle = undefined as string | undefined,
    }: {
        title: string;
        count?: number | string;
        subtitle?: string;
    } = $props();
</script>

<h2
    class="text-xl font-sans font-bold text-primary uppercase tracking-wider border-b border-border-dark pb-2 mb-4 flex items-baseline gap-2"
>
    <span>{title}</span>
    {#if count !== undefined}
        <span class="text-secondary text-base font-normal">({count})</span>
    {/if}
    {#if subtitle}
        <span class="text-secondary text-sm font-normal normal-case ml-2"
            >{subtitle}</span
        >
    {/if}
</h2>
