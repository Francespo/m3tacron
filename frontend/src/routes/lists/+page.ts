import type { PageLoad } from './$types';

export const load: PageLoad = ({ url }) => {
    url.search; // Force reactivity when any query param changes

    const page = Number(url.searchParams.get('page') ?? '0');
    const size = Number(url.searchParams.get('size') ?? '20');
    const min_games = Number(url.searchParams.get('min_games') ?? '3');
    const selectedFactions = url.searchParams.getAll('factions');
    const sort_metric = url.searchParams.get('sort_metric') || 'Games';
    const sort_direction = url.searchParams.get('sort_direction') || 'desc';

    return {
        items: [],
        total: 0,
        page,
        size,
        min_games,
        selectedFactions,
        sort_metric,
        sort_direction,
    };
};
