import { goto } from "$app/navigation";

type QuerySyncOptions = {
    delayMs?: number;
};

export function createQuerySync(getCurrentQuery: () => string, defaultDelayMs = 250) {
    let timer: ReturnType<typeof setTimeout> | null = null;

    function clear() {
        if (timer) {
            clearTimeout(timer);
            timer = null;
        }
    }

    function schedule(params: URLSearchParams, options: QuerySyncOptions = {}) {
        const delayMs = options.delayMs ?? defaultDelayMs;
        const nextQuery = params.toString();

        if (nextQuery === getCurrentQuery()) {
            clear();
            return;
        }

        clear();
        timer = setTimeout(() => {
            if (nextQuery === getCurrentQuery()) {
                return;
            }

            void goto(`?${nextQuery}`, {
                keepFocus: true,
                noScroll: true,
                replaceState: true,
            });
        }, delayMs);
    }

    return { schedule, clear };
}
