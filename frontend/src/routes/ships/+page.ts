import type { PageLoad } from './$types';

export const load: PageLoad = ({ url }) => {
    url.search; // Force reactivity when any query param changes

    const page = Number(url.searchParams.get('page') ?? '0');
    const size = Number(url.searchParams.get('size') ?? '50');
    const sort_metric = url.searchParams.get('sort_metric') || 'Popularity';
    const sort_direction = url.searchParams.get('sort_direction') || 'desc';
    const selectedFactions = url.searchParams.getAll('factions');

    return {
        items: [],
        total: 0,
        page,
        size,
        sort_metric,
        sort_direction,
        selectedFactions,
    };
};
