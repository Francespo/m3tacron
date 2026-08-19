import { goto } from '$app/navigation';
import { page } from '$app/state';
import { filters } from '$lib/stores/filters.svelte';
import { clearPendingSync, resolvePendingSync } from '$lib/sync/urlSync.svelte';

export async function setDataSource(value: 'xwa' | 'legacy') {
    clearPendingSync();
    filters.dataSource = value;
    const next = new URL(page.url);
    if (value === 'xwa') {
        next.searchParams.delete('data_source');
        next.searchParams.delete('formats');
        next.searchParams.append('formats', 'xwa');
    } else {
        next.searchParams.set('data_source', 'legacy');
        next.searchParams.delete('formats');
        next.searchParams.append('formats', 'legacy_x2po');
    }

    resolvePendingSync();
    await goto(next.pathname + next.search, {
        replaceState: true,
        keepFocus: true,
        noScroll: true,
    });
}

export async function setIncludeEpic(value: boolean) {
    clearPendingSync();
    filters.includeEpic = value;
    const next = new URL(page.url);
    if (value) {
        next.searchParams.set('epic', 'true');
    } else {
        next.searchParams.delete('epic');
    }
    resolvePendingSync();
    await goto(next.pathname + next.search, {
        replaceState: true,
        keepFocus: true,
        noScroll: true,
    });
}
