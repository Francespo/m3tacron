<script lang="ts">
    let { label = "Loading data" }: { label?: string } = $props();
</script>

<div class="flex flex-col items-center justify-center py-10 gap-4" role="status" aria-label={label} aria-live="polite">
    <div class="relative w-[72px] h-[72px] flex items-center justify-center">
        <!-- subtle outer ring -->
        <div class="absolute inset-0 rounded-full border border-white/[0.08]"></div>
        <!-- spinning arc -->
        <div class="absolute inset-0 rounded-full border-2 border-transparent border-t-white/70 border-r-white/20 animate-spin" style="animation-duration: 0.9s;"></div>
        <!-- ship silhouette - bobbing -->
        <i class="xwing-miniatures-ship xwing-miniatures-ship-xwing text-[22px] leading-none text-white/85 ship-bob" aria-hidden="true"></i>
    </div>
    <!-- fake progress shimmer bar -->
    <div class="w-28 h-1 rounded-full bg-white/[0.06] overflow-hidden">
        <div class="h-full w-1/2 bg-gradient-to-r from-transparent via-white/50 to-transparent shimmer"></div>
    </div>
</div>

<style>
    @keyframes ship-bob {
        0%, 100% { transform: translateY(0); }
        50% { transform: translateY(-3px); }
    }
    .ship-bob {
        animation: ship-bob 1.6s ease-in-out infinite;
    }
    @keyframes shimmer {
        0% { transform: translateX(-100%); }
        100% { transform: translateX(220%); }
    }
    .shimmer {
        animation: shimmer 1.2s ease-in-out infinite;
    }
    @media (prefers-reduced-motion: reduce) {
        .ship-bob, .shimmer, .animate-spin {
            animation: none !important;
        }
    }
</style>
