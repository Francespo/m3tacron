import useSWR from 'swr';
import { PaginatedResponse, TournamentRow, ListData, ShipStat, PilotStat, UpgradeStat, MetaSnapshotResponse } from './types';

const fetcher = async (url: string) => {
    const res = await fetch(url);
    if (!res.ok) {
        throw new Error('An error occurred while fetching the data.');
    }
    return res.json();
};

export function useMeta(dataSource: string = "xwa") {
    const { data, error, isLoading } = useSWR<MetaSnapshotResponse>(
        `/api/meta-snapshot?data_source=${dataSource}`,
        fetcher,
        { keepPreviousData: true }
    );
    return { data, error, isLoading };
}

export function useTournaments(params: URLSearchParams) {
    const { data, error, isLoading } = useSWR<PaginatedResponse<TournamentRow>>(
        `/api/tournaments?${params.toString()}`,
        fetcher,
        { keepPreviousData: true }
    );
    return { data, error, isLoading };
}

export function useLists(params: URLSearchParams) {
    const { data, error, isLoading } = useSWR<PaginatedResponse<ListData>>(
        `/api/lists?${params.toString()}`,
        fetcher,
        { keepPreviousData: true }
    );
    return { data, error, isLoading };
}

export function useShips(params: URLSearchParams) {
    const { data, error, isLoading } = useSWR<PaginatedResponse<ShipStat>>(
        `/api/ships?${params.toString()}`,
        fetcher,
        { keepPreviousData: true }
    );
    return { data, error, isLoading };
}

export function useCards<T extends PilotStat | UpgradeStat>(
    tab: "pilots" | "upgrades",
    params: URLSearchParams
) {
    const { data, error, isLoading } = useSWR<PaginatedResponse<T>>(
        `/api/cards/${tab}?${params.toString()}`,
        fetcher,
        { keepPreviousData: true }
    );
    return { data, error, isLoading };
}



export function useSquadrons(params: URLSearchParams) {
    const { data, error, isLoading } = useSWR<any>(
        `/api/squadrons?${params.toString()}`,
        fetcher,
        { keepPreviousData: true }
    );
    return { data, error, isLoading };
}
