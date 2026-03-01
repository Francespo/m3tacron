"use client";

/**
 * DashboardRankings — client wrapper that handles sorting for all
 * ranking sections. Receives pre-fetched data from the Server Component.
 */

import type { ListData, ShipStat, PilotStat, UpgradeStat } from "@/lib/types";
import RankingPanel from "./RankingPanel";
import TopItemRow from "./TopItemRow";
import TopListRow from "./TopListRow";

interface DashboardRankingsProps {
    lists: ListData[];
    ships: ShipStat[];
    pilots: PilotStat[];
    upgrades: UpgradeStat[];
}

/** Sort helper: returns a sorted copy of the array by the given key. */
function sortedBy<T extends Record<string, unknown>>(
    items: T[],
    key: "popularity" | "win_rate"
): T[] {
    return [...items].sort((a, b) => {
        const av = Number(a[key]) || 0;
        const bv = Number(b[key]) || 0;
        return bv - av;
    });
}

/** Sort ListData objects (which have different field names). */
function sortedLists(items: ListData[], key: "popularity" | "win_rate"): ListData[] {
    return [...items].sort((a, b) => {
        const av = key === "popularity" ? a.count : a.win_rate;
        const bv = key === "popularity" ? b.count : b.win_rate;
        return bv - av;
    });
}

export default function DashboardRankings({
    lists,
    ships,
    pilots,
    upgrades,
}: DashboardRankingsProps) {
    return (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 w-full">
            {/* Column 1: Lists + Ships */}
            <div className="flex flex-col gap-6">
                {/* Top Squad Lists */}
                <RankingPanel title="TOP SQUAD LISTS">
                    {(sort) => {
                        const sorted = sortedLists(lists, sort);
                        return sorted.slice(0, 5).map((l, i) => (
                            <TopListRow
                                key={i}
                                list={l}
                                value={
                                    sort === "win_rate"
                                        ? `${l.win_rate}%`
                                        : `${l.count}`
                                }
                            />
                        ));
                    }}
                </RankingPanel>

                {/* Top Chassis */}
                <RankingPanel title="TOP CHASSIS">
                    {(sort) => {
                        const sorted = sortedBy(ships, sort);
                        return sorted.slice(0, 5).map((s, i) => (
                            <TopItemRow
                                key={i}
                                rank={i + 1}
                                name={s.ship_name}
                                value={`${s.popularity} Lists`}
                                subvalue={`${s.win_rate}% WR`}
                                isShip={true}
                                shipXws={s.ship_xws}
                            />
                        ));
                    }}
                </RankingPanel>
            </div>

            {/* Column 2: Pilots + Upgrades */}
            <div className="flex flex-col gap-6">
                {/* Top Pilots */}
                <RankingPanel title="TOP PILOTS">
                    {(sort) => {
                        const sorted = sortedBy(pilots, sort);
                        return sorted.slice(0, 5).map((p, i) => (
                            <TopItemRow
                                key={i}
                                rank={i + 1}
                                name={p.name}
                                value={`${p.popularity} Lists`}
                                subvalue={`${p.win_rate}% WR`}
                                factionKey={p.faction}
                            />
                        ));
                    }}
                </RankingPanel>

                {/* Top Upgrades */}
                <RankingPanel title="TOP UPGRADES">
                    {(sort) => {
                        const sorted = sortedBy(upgrades, sort);
                        return sorted.slice(0, 5).map((u, i) => (
                            <TopItemRow
                                key={i}
                                rank={i + 1}
                                name={u.name}
                                value={`${u.popularity} Lists`}
                                subvalue={`${u.win_rate}% WR`}
                            />
                        ));
                    }}
                </RankingPanel>
            </div>
        </div>
    );
}
