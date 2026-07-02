<!--
    FactionIcon — canonical X-Wing-font faction glyph with a clean
    fallback for "unknown" factions.

    API:
      • faction    – XWS faction id (e.g. "rebelalliance", "unknown")
      • size       – optional "xs" (10px) / "sm" (14px) / "md" (18px) /
                     "lg" (24px) / "xl" (text-5xl md:text-6xl, list
                     detail hero) / "xxl" (text-7xl, squadron detail
                     hero). Defaults to "sm".
      • className  – optional additional classes (e.g. "drop-shadow-sm")
-->
<script lang="ts">
    import { getFactionChar, getFactionColor } from "$lib/data/factions";

    let {
        faction,
        size = "sm",
        className = "",
    }: {
        faction: string;
        size?: "xs" | "sm" | "md" | "lg" | "xl" | "xxl";
        className?: string;
    } = $props();

    const sizeClass = $derived(
        size === "xs"
            ? "text-[10px]"
            : size === "sm"
              ? "text-sm"
              : size === "md"
                ? "text-lg"
                : size === "lg"
                  ? "text-2xl"
                  : size === "xl"
                    ? "text-5xl md:text-6xl"
                    : "text-7xl",
    );

    const isUnknown = $derived(!faction || faction === "unknown");
    const char = $derived(isUnknown ? "?" : getFactionChar(faction));
    const color = $derived(getFactionColor(faction));
</script>

{#if isUnknown}
    <!-- Unknown faction: plain "?" in sans-serif, grey. NOT in the X-Wing
         font (which would render "?" as a geometric/rocket glyph). -->
    <span
        class="font-sans font-bold {sizeClass} {className}"
        style="color: {color};"
        aria-label="Unknown faction"
        title="Unknown faction"
    >
        ?
    </span>
{:else}
    <!-- Known faction: X-Wing font glyph, colored. -->
    <span
        class="font-xwing {sizeClass} {className}"
        style="color: {color};"
        aria-label={faction}
        title={faction}
    >
        {char}
    </span>
{/if}
