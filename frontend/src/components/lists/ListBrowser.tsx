"use client";

import { useState } from "react";
import { useLists } from "@/lib/api-client";
import { Accordion } from "@/components/ui/Accordion";
import { Pagination } from "@/components/ui/Pagination";
import { RotateCcw, ArrowDownWideNarrow, ArrowUpNarrowWide } from "lucide-react";
import DataSourceToggle from "@/components/DataSourceToggle";
import { useSearchParams } from "next/navigation";
import { ListRow } from "./ListRow";

const FACTION_OPTIONS = [
    { label: "Rebel Alliance", value: "rebelalliance" },
    { label: "Galactic Empire", value: "galacticempire" },
    { label: "Scum and Villainy", value: "scumandvillainy" },
    { label: "Resistance", value: "resistance" },
    { label: "First Order", value: "firstorder" },
    { label: "Galactic Republic", value: "galacticrepublic" },
    { label: "Separatist Alliance", value: "separatistalliance" },
];

export function ListBrowser() {
    const searchParamsOrigin = useSearchParams();
    const source = searchParamsOrigin?.get("source") || "xwa";

    const [page, setPage] = useState(0);
    const [factions, setFactions] = useState<string[]>([]);

    // Numeric Filters
    const [pointsMin, setPointsMin] = useState<number>(0);
    const [pointsMax, setPointsMax] = useState<number>(source === "xwa" ? 50 : 200);
    const [loadoutMin, setLoadoutMin] = useState<number>(0);
    const [loadoutMax, setLoadoutMax] = useState<number>(50);
    const [minGames, setMinGames] = useState<number>(0);

    // Sorting
    const [sortMetric, setSortMetric] = useState<string>("Games"); // Games, Win Rate, Points Cost, Total Loadout
    const [sortDirection, setSortDirection] = useState<"desc" | "asc">("desc");

    const params = new URLSearchParams();
    params.set("page", page.toString());
    params.set("size", "20");
    params.set("data_source", source);
    params.set("sort_metric", sortMetric);
    params.set("sort_direction", sortDirection);

    if (pointsMin > 0) params.set("points_min", pointsMin.toString());
    if (pointsMax > 0 && pointsMax < 200) params.set("points_max", pointsMax.toString());
    if (minGames > 0) params.set("min_games", minGames.toString());

    if (source === "xwa") {
        if (loadoutMin > 0) params.set("loadout_min", loadoutMin.toString());
        if (loadoutMax < 50) params.set("loadout_max", loadoutMax.toString());
    }

    factions.forEach(f => params.append("factions", f));

    const { data, isLoading } = useLists(params);

    const toggleFaction = (val: string) => {
        setFactions(prev =>
            prev.includes(val) ? prev.filter(f => f !== val) : [...prev, val]
        );
        setPage(0);
    };

    const resetFilters = () => {
        setFactions([]);
        setPointsMin(0);
        setPointsMax(source === "xwa" ? 50 : 200);
        setLoadoutMin(0);
        setLoadoutMax(50);
        setMinGames(0);
        setSortMetric("Games");
        setSortDirection("desc");
        setPage(0);
    };

    return (
        <div className="flex flex-col md:flex-row w-full gap-8 text-white">
            {/* Filter Sidebar */}
            <div className="w-full md:min-w-[280px] md:max-w-[280px] shrink-0 flex flex-col gap-6">

                {/* Content Source Filter */}
                <div className="flex flex-col gap-2 mb-2">
                    <span className="text-[10px] font-bold text-text-secondary font-mono uppercase tracking-wider">GAME SOURCE</span>
                    <DataSourceToggle />
                </div>

                <div className="h-[1px] w-full bg-border-terminal" />

                <div className="flex items-center justify-between">
                    <h2 className="text-sm font-bold tracking-[1px] text-text-primary uppercase">
                        LIST FILTERS
                    </h2>
                    <button
                        onClick={resetFilters}
                        className="p-1 text-text-secondary hover:text-text-primary hover:bg-[rgba(255,255,255,0.1)] rounded transition-colors"
                        title="Reset Filters"
                    >
                        <RotateCcw size={16} />
                    </button>
                </div>

                {/* Sort By */}
                <div className="flex flex-col gap-2">
                    <span className="text-[10px] font-bold text-text-secondary font-mono tracking-[1px] uppercase">Sort By</span>
                    <div className="flex gap-2">
                        <select
                            value={sortMetric}
                            onChange={(e) => { setSortMetric(e.target.value); setPage(0); }}
                            className="bg-terminal-bg border border-border-terminal rounded-md p-2 text-sm text-text-primary font-mono focus:outline-none focus:border-text-primary flex-1"
                        >
                            <option value="Games">Games</option>
                            <option value="Win Rate">Win Rate</option>
                            <option value="Points Cost">Points Cost</option>
                            <option value="Total Loadout">Total Loadout</option>
                        </select>
                        <button
                            onClick={() => { setSortDirection(d => d === "desc" ? "asc" : "desc"); setPage(0); }}
                            className="bg-terminal-panel border border-border-terminal rounded-md w-10 flex items-center justify-center text-text-secondary hover:text-text-primary hover:bg-[rgba(255,255,255,0.05)] transition-colors"
                        >
                            {sortDirection === "desc" ? <ArrowDownWideNarrow size={18} /> : <ArrowUpNarrowWide size={18} />}
                        </button>
                    </div>
                </div>

                <Accordion title="FACTION" defaultOpen={true}>
                    <div className="flex flex-col gap-3">
                        {FACTION_OPTIONS.map(opt => (
                            <div key={opt.value} className="flex items-center gap-3 cursor-pointer group" onClick={() => toggleFaction(opt.value)}>
                                <div className={`w-4 h-4 rounded border flex items-center justify-center transition-colors ${factions.includes(opt.value) ? 'bg-[#4facfe] border-[#4facfe]' : 'border-border-terminal group-hover:border-text-secondary'}`}>
                                    {factions.includes(opt.value) && <div className="w-1.5 h-1.5 bg-terminal-bg rounded-sm" />}
                                </div>
                                <span className="text-sm font-mono text-text-secondary group-hover:text-text-primary transition-colors select-none">{opt.label}</span>
                            </div>
                        ))}
                    </div>
                </Accordion>

                <div className="flex flex-col gap-4">
                    {/* Min Games */}
                    <div className="flex flex-col gap-2">
                        <span className="text-[10px] font-bold text-text-secondary font-mono tracking-[1px] uppercase">Min Games</span>
                        <input
                            type="number" min="0" value={minGames} onChange={e => { setMinGames(parseInt(e.target.value) || 0); setPage(0); }}
                            className="bg-terminal-bg border border-border-terminal rounded-md p-2 text-sm text-text-primary font-mono focus:outline-none focus:border-text-primary w-full"
                        />
                    </div>

                    {/* Points Cost */}
                    <div className="flex flex-col gap-2">
                        <span className="text-[10px] font-bold text-text-secondary font-mono tracking-[1px] uppercase">Points Cost</span>
                        <div className="flex items-center gap-2">
                            <input
                                type="number" min="0" value={pointsMin} onChange={e => { setPointsMin(parseInt(e.target.value) || 0); setPage(0); }}
                                className="bg-terminal-bg border border-border-terminal rounded-md p-2 text-sm text-text-primary font-mono focus:outline-none focus:border-text-primary flex-1 min-w-0"
                            />
                            <span className="text-text-secondary">-</span>
                            <input
                                type="number" min="0" value={pointsMax} onChange={e => { setPointsMax(parseInt(e.target.value) || 0); setPage(0); }}
                                className="bg-terminal-bg border border-border-terminal rounded-md p-2 text-sm text-text-primary font-mono focus:outline-none focus:border-text-primary flex-1 min-w-0"
                            />
                        </div>
                    </div>

                    {/* Total Loadout (XWA Only) */}
                    {source === "xwa" && (
                        <div className="flex flex-col gap-2">
                            <span className="text-[10px] font-bold text-text-secondary font-mono tracking-[1px] uppercase">Total Loadout</span>
                            <div className="flex items-center gap-2">
                                <input
                                    type="number" min="0" value={loadoutMin} onChange={e => { setLoadoutMin(parseInt(e.target.value) || 0); setPage(0); }}
                                    className="bg-terminal-bg border border-border-terminal rounded-md p-2 text-sm text-text-primary font-mono focus:outline-none focus:border-text-primary flex-1 min-w-0"
                                />
                                <span className="text-text-secondary">-</span>
                                <input
                                    type="number" min="0" value={loadoutMax} onChange={e => { setLoadoutMax(parseInt(e.target.value) || 0); setPage(0); }}
                                    className="bg-terminal-bg border border-border-terminal rounded-md p-2 text-sm text-text-primary font-mono focus:outline-none focus:border-text-primary flex-1 min-w-0"
                                />
                            </div>
                        </div>
                    )}
                </div>
            </div>

            {/* Main Content */}
            <div className="flex-1 flex flex-col min-w-0">
                <div className="border-b border-border-terminal pb-6 mb-6">
                    <h1 className="text-[28px] font-bold font-sans text-text-primary">List Browser</h1>
                </div>

                {isLoading ? (
                    <div className="text-text-secondary animate-pulse font-mono tracking-widest">LOADING...</div>
                ) : (
                    <>
                        <div className="mb-4 text-sm font-mono text-text-secondary tracking-widest uppercase">
                            {data?.total || 0} LISTS FOUND
                        </div>

                        {data?.items && data.items.length > 0 ? (
                            <div className="flex flex-col gap-3">
                                {data.items.map((l: any, i: number) => (
                                    <ListRow key={i} list={l} />
                                ))}
                            </div>
                        ) : (
                            <div className="w-full py-16 flex flex-col items-center justify-center border border-border-terminal rounded-md bg-terminal-panel gap-3 shadow-[inset_0_1px_0_rgba(255,255,255,0.03)]">
                                <span className="text-text-secondary tracking-widest font-mono font-bold uppercase">0 LISTS FOUND</span>
                                <span className="text-sm text-text-secondary">No lists match your current filters.</span>
                            </div>
                        )}

                        <Pagination
                            page={data?.page || 0}
                            total={data?.total || 0}
                            size={data?.size || 20}
                            setPage={setPage}
                        />
                    </>
                )}
            </div>
        </div>
    );
}
