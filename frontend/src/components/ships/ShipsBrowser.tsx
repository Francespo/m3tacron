"use client";

import { useState, useMemo } from "react";
import { useShips, useMeta } from "@/lib/api-client";
import { Accordion } from "@/components/ui/Accordion";
import { Pagination } from "@/components/ui/Pagination";
import { SearchableAccordion } from "@/components/ui/SearchableAccordion";
import { RotateCcw, ArrowDownWideNarrow, ArrowUpNarrowWide } from "lucide-react";
import DataSourceToggle from "@/components/DataSourceToggle";
import { useSearchParams } from "next/navigation";
import { ShipCard } from "./ShipCard";
import { ShipStat } from "@/lib/types";

const FACTION_OPTIONS = [
    { label: "Rebel Alliance", value: "rebelalliance" },
    { label: "Galactic Empire", value: "galacticempire" },
    { label: "Scum and Villainy", value: "scumandvillainy" },
    { label: "Resistance", value: "resistance" },
    { label: "First Order", value: "firstorder" },
    { label: "Galactic Republic", value: "galacticrepublic" },
    { label: "Separatist Alliance", value: "separatistalliance" },
];

export function ShipsBrowser() {
    const searchParamsOrigin = useSearchParams();
    const source = searchParamsOrigin?.get("source") || "xwa";

    const [page, setPage] = useState(0);
    const [factions, setFactions] = useState<string[]>([]);
    const [selectedShips, setSelectedShips] = useState<string[]>([]);

    // Sorting
    const [sortMetric, setSortMetric] = useState<string>("Popularity"); // Games, Popularity, Win Rate
    const [sortDirection, setSortDirection] = useState<"desc" | "asc">("desc");

    const params = new URLSearchParams();
    params.set("page", page.toString());
    params.set("size", "20");
    params.set("data_source", source);
    params.set("sort_metric", sortMetric);
    params.set("sort_direction", sortDirection);

    factions.forEach(f => params.append("factions", f));
    selectedShips.forEach(s => params.append("ships", s));

    const { data, isLoading } = useShips(params);
    const { data: metaData } = useMeta(source);

    // Derived ships for filter
    const availableShips = useMemo(() => {
        if (!metaData?.ships) return [];

        let filtered = metaData.ships;
        if (factions.length > 0) {
            filtered = filtered.filter(s => factions.includes(s.faction_xws));
        }

        // Deduplicate ship names 
        const unq = new Map<string, string>();
        filtered.forEach(s => {
            unq.set(s.ship_xws, s.ship_name);
        });

        return Array.from(unq.entries())
            .map(([xws, name]) => ({ label: name, value: xws }))
            .sort((a, b) => a.label.localeCompare(b.label));
    }, [metaData, factions]);

    const toggleFaction = (val: string) => {
        setFactions(prev => prev.includes(val) ? prev.filter(f => f !== val) : [...prev, val]);
        setPage(0);
    };

    const toggleShip = (val: string) => {
        setSelectedShips(prev => prev.includes(val) ? prev.filter(s => s !== val) : [...prev, val]);
        setPage(0);
    };

    const resetFilters = () => {
        setFactions([]);
        setSelectedShips([]);
        setSortMetric("Popularity");
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
                        SHIP FILTERS
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
                            <option value="Popularity">Popularity</option>
                            <option value="Items">Games</option>
                            <option value="Win Rate">Win Rate</option>
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

                <SearchableAccordion
                    title="SHIP CHASSIS"
                    defaultOpen={true}
                    options={availableShips}
                    selectedValues={selectedShips}
                    onToggle={toggleShip}
                />
            </div>

            {/* Main Content */}
            <div className="flex-1 flex flex-col min-w-0">
                <div className="border-b border-border-terminal pb-6 mb-6">
                    <h1 className="text-[28px] font-bold font-sans text-text-primary">Ships</h1>
                    <p className="text-sm text-text-secondary font-sans mt-1">Browse all ships with aggregated statistics per faction</p>
                </div>

                {isLoading ? (
                    <div className="text-text-secondary animate-pulse font-mono tracking-widest">LOADING...</div>
                ) : (
                    <>
                        <div className="mb-4 text-sm font-mono text-text-secondary tracking-widest uppercase">
                            {data?.total || 0} SHIPS FOUND
                        </div>

                        {data?.items && data.items.length > 0 ? (
                            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 w-full">
                                {data.items.map((s: ShipStat, i: number) => (
                                    <ShipCard key={`${s.ship_xws}-${s.faction_xws}-${i}`} ship={s} />
                                ))}
                            </div>
                        ) : (
                            <div className="w-full py-16 flex flex-col items-center justify-center border border-border-terminal rounded-md bg-terminal-panel gap-3 shadow-[inset_0_1px_0_rgba(255,255,255,0.03)]">
                                <span className="text-text-secondary tracking-widest font-mono font-bold uppercase">0 SHIPS FOUND</span>
                                <span className="text-sm text-text-secondary">No ships match your current filters.</span>
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
