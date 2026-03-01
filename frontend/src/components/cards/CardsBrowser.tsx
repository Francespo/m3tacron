"use client";

import { useState, useMemo } from "react";
import { useCards, useMeta } from "@/lib/api-client";
import { Accordion } from "@/components/ui/Accordion";
import { SearchableAccordion } from "@/components/ui/SearchableAccordion";
import { Pagination } from "@/components/ui/Pagination";
import { Search, RotateCcw, Crosshair } from "lucide-react";
import { PilotStat, UpgradeStat } from "@/lib/types";
import { PilotCard, UpgradeCard } from "./CardItems";

export function CardsBrowser() {
    const [tab, setTab] = useState<"pilots" | "upgrades">("pilots");

    // SWR to fetch dynamic options from snapshot
    const { data: meta } = useMeta("xwa");

    // Pagination state
    const [page, setPage] = useState(0);

    // Common Filters
    const [searchText, setSearchText] = useState("");

    // Pilots Filters
    const [selectedFactions, setSelectedFactions] = useState<Set<string>>(new Set());
    const [selectedShips, setSelectedShips] = useState<Set<string>>(new Set());
    const [selectedInitiatives, setSelectedInitiatives] = useState<Set<string>>(new Set());

    // Upgrades Filters
    const [selectedUpgradeTypes, setSelectedUpgradeTypes] = useState<Set<string>>(new Set());

    // Factions derived from snapshot (global) for pilots
    const factionOptions = useMemo(() => {
        if (!meta) return [];
        return meta.factions
            .filter((f) => f.xws !== "unknown")
            .map((f) => ({
                id: f.xws,
                label: f.name,
                icon_char: f.icon_char,
            }));
    }, [meta]);

    // Ships derived from meta snapshot ships
    const shipOptions = useMemo(() => {
        if (!meta) return [];
        // Only filter by selected factions if any are active
        let filtered = meta.ships;
        if (selectedFactions.size > 0) {
            filtered = filtered.filter((s) => selectedFactions.has(s.faction_xws));
        }

        // De-duplicate ships by xws since multiple factions might share a ship Chassis name
        const uniqueShips = new Map();
        filtered.forEach(s => {
            if (!uniqueShips.has(s.ship_xws)) {
                uniqueShips.set(s.ship_xws, {
                    value: s.ship_xws,
                    label: s.ship_name
                });
            }
        });

        return Array.from(uniqueShips.values()).sort((a, b) =>
            a.label.localeCompare(b.label)
        );
    }, [meta, selectedFactions]);

    const initiativeOptions = Array.from({ length: 8 }, (_, i) => ({ id: `${i}`, label: `${i}` }));

    // We can infer dynamic upgrade types from metadata upgrades
    const upgradeTypeOptions = useMemo(() => {
        if (!meta?.upgrades) return [];
        const uniqueTypes = new Set(meta.upgrades.map(u => u.type).filter(x => x));
        return Array.from(uniqueTypes).sort().map(ut => ({ value: ut.toLowerCase(), label: ut }));
    }, [meta]);

    // Construct URLSearchParams
    const params = new URLSearchParams();
    params.set("page", page.toString());
    params.set("size", "36");
    if (searchText) params.set("search_text", searchText);

    if (tab === "pilots") {
        Array.from(selectedFactions).forEach((f) => params.append("factions", f));
        Array.from(selectedShips).forEach((s) => params.append("ships", s));
        Array.from(selectedInitiatives).forEach((i) => params.append("initiatives", i));
    } else {
        Array.from(selectedUpgradeTypes).forEach((u) => params.append("upgrade_types", u));
    }

    // Fetch Cards Data
    const { data: cardsResponse, isLoading } = useCards<PilotStat | UpgradeStat>(tab, params);

    const handleReset = () => {
        setSearchText("");
        setSelectedFactions(new Set());
        setSelectedShips(new Set());
        setSelectedInitiatives(new Set());
        setSelectedUpgradeTypes(new Set());
        setPage(0);
    };

    return (
        <div className="flex flex-col lg:flex-row gap-6 max-w-[1400px] mx-auto p-4 sm:p-6 lg:p-10 min-h-[calc(100vh-64px)] pb-32">

            {/* -- SCROLLABLE SIDEBAR -- */}
            <aside className="w-full lg:w-72 flex-shrink-0 flex flex-col gap-6">
                {/* Header & Reset */}
                <div className="flex items-center justify-between mt-2">
                    <h2 className="text-xl font-bold font-sans tracking-wide flex items-center gap-2 text-text-primary">
                        <Crosshair className="w-5 h-5 text-accent-primary" />
                        DATABASE
                    </h2>
                    <button
                        onClick={handleReset}
                        className="text-xs text-text-secondary hover:text-accent-primary flex items-center gap-1 font-mono transition-colors"
                        title="Reset Filters"
                    >
                        <RotateCcw className="w-3 h-3" />
                        RESET
                    </button>
                </div>

                {/* Tabs */}
                <div className="flex rounded-sm bg-black border border-border-terminal p-1 font-mono uppercase tracking-wider text-xs">
                    <button
                        onClick={() => { setTab("pilots"); setPage(0); }}
                        className={`flex-1 py-1.5 text-center transition-colors rounded-sm ${tab === "pilots" ? "bg-accent-primary text-black font-extrabold" : "text-text-secondary hover:text-text-primary"
                            }`}
                    >
                        Pilots
                    </button>
                    <button
                        onClick={() => { setTab("upgrades"); setPage(0); }}
                        className={`flex-1 py-1.5 text-center transition-colors rounded-sm ${tab === "upgrades" ? "bg-accent-primary text-black font-extrabold" : "text-text-secondary hover:text-text-primary"
                            }`}
                    >
                        Upgrades
                    </button>
                </div>

                {/* Filters */}
                <div className="flex flex-col gap-px bg-border-terminal border border-border-terminal overflow-hidden rounded shadow-lg panel-glow">
                    {/* Text Search */}
                    <div className="bg-terminal-bg p-4">
                        <label className="text-xs font-bold text-text-secondary uppercase tracking-wider mb-2 block">
                            Search Name / Text
                        </label>
                        <div className="relative">
                            <input
                                type="text"
                                value={searchText}
                                onChange={(e) => {
                                    setSearchText(e.target.value);
                                    setPage(0);
                                }}
                                className="w-full bg-black border border-border-terminal rounded px-3 py-2 pl-9 text-sm text-text-primary focus:outline-none focus:border-accent-primary font-sans"
                                placeholder="Search cards..."
                            />
                            <Search className="w-4 h-4 text-text-secondary absolute left-3 top-2.5" />
                        </div>
                    </div>

                    {tab === "pilots" && (
                        <>
                            {/* Faction Accordion */}
                            <Accordion title="FACTION" defaultOpen={selectedFactions.size > 0}>
                                <div className="p-3 max-h-60 overflow-y-auto custom-scrollbar flex flex-col gap-1">
                                    {factionOptions.map((f) => (
                                        <label key={f.id} className="flex items-center gap-3 p-2 hover:bg-white/5 rounded cursor-pointer group">
                                            <input
                                                type="checkbox"
                                                className="w-4 h-4 rounded border-border-terminal bg-black text-accent-primary focus:ring-accent-primary/20 accent-accent-primary"
                                                checked={selectedFactions.has(f.id)}
                                                onChange={(e) => {
                                                    const next = new Set(selectedFactions);
                                                    if (e.target.checked) next.add(f.id);
                                                    else next.delete(f.id);
                                                    setSelectedFactions(next);
                                                    setPage(0);
                                                    // Also reset ships because they depend on faction
                                                    setSelectedShips(new Set());
                                                }}
                                            />
                                            {f.icon_char && (
                                                <i className={`xwing-miniatures-font xwing-miniatures-font-${f.id} text-lg text-text-secondary group-hover:text-accent-primary transition-colors`} />
                                            )}
                                            <span className="text-sm font-medium font-sans text-text-primary">
                                                {f.label}
                                            </span>
                                        </label>
                                    ))}
                                </div>
                            </Accordion>

                            <SearchableAccordion
                                title="SHIP CHASSIS"
                                options={shipOptions}
                                selectedValues={Array.from(selectedShips)}
                                onToggle={(val) => {
                                    const next = new Set(selectedShips);
                                    if (next.has(val)) next.delete(val);
                                    else next.add(val);
                                    setSelectedShips(next);
                                    setPage(0);
                                }}
                                defaultOpen={selectedShips.size > 0}
                            />

                            <Accordion title="INITIATIVE" defaultOpen={selectedInitiatives.size > 0}>
                                <div className="p-3 grid grid-cols-4 gap-2">
                                    {initiativeOptions.map((f) => (
                                        <label key={f.id} className={`flex items-center justify-center py-2 hover:bg-white/10 rounded cursor-pointer border ${selectedInitiatives.has(f.id) ? 'bg-accent-primary/10 border-accent-primary text-accent-primary' : 'border-border-terminal bg-black text-text-secondary'} font-mono font-bold transition-all`}>
                                            <input
                                                type="checkbox"
                                                className="sr-only"
                                                checked={selectedInitiatives.has(f.id)}
                                                onChange={(e) => {
                                                    const next = new Set(selectedInitiatives);
                                                    if (e.target.checked) next.add(f.id);
                                                    else next.delete(f.id);
                                                    setSelectedInitiatives(next);
                                                    setPage(0);
                                                }}
                                            />
                                            {f.label}
                                        </label>
                                    ))}
                                </div>
                            </Accordion>
                        </>
                    )}

                    {tab === "upgrades" && (
                        <SearchableAccordion
                            title="UPGRADE TYPE"
                            options={upgradeTypeOptions}
                            selectedValues={Array.from(selectedUpgradeTypes)}
                            onToggle={(val) => {
                                const next = new Set(selectedUpgradeTypes);
                                if (next.has(val)) next.delete(val);
                                else next.add(val);
                                setSelectedUpgradeTypes(next);
                                setPage(0);
                            }}
                            defaultOpen={selectedUpgradeTypes.size > 0}
                        />
                    )}
                </div>
            </aside>

            {/* -- CONTENT AREA -- */}
            <div className="flex-1 flex flex-col min-w-0">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6 pt-2">
                    <h1 className="text-2xl font-bold font-sans text-text-primary capitalize">
                        {tab} Database
                    </h1>
                    <div className="text-sm font-mono text-text-secondary">
                        {isLoading ? "LOADING..." : <span className="text-accent-primary">{cardsResponse?.total || 0} CARDS FOUND</span>}
                    </div>
                </div>

                {isLoading && (
                    <div className="flex-1 flex items-center justify-center p-12">
                        <div className="animate-pulse text-accent-primary font-mono tracking-widest">
                            SCANNING DATABASE...
                        </div>
                    </div>
                )}

                {!isLoading && cardsResponse && cardsResponse.items.length === 0 && (
                    <div className="flex-1 flex items-center justify-center p-12">
                        <div className="text-text-secondary font-mono tracking-wide text-center">
                            NO CARDS MATCH CURRENT FILTERS.
                            <div className="mt-2 text-xs">TRY ADJUSTING YOUR PARAMETERS.</div>
                        </div>
                    </div>
                )}

                {!isLoading && cardsResponse && cardsResponse.items.length > 0 && (
                    <div className="flex-1 flex flex-col justify-between">
                        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 xl:grid-cols-5 2xl:grid-cols-6 gap-4 pl-1">
                            {cardsResponse.items.map((card) => {
                                if (tab === "pilots") {
                                    return <PilotCard key={(card as PilotStat).xws} pilot={card as PilotStat} />;
                                } else {
                                    return <UpgradeCard key={(card as UpgradeStat).xws} upgrade={card as UpgradeStat} />;
                                }
                            })}
                        </div>

                        {cardsResponse.total > cardsResponse.size && (
                            <div className="mt-8 pt-4 border-t border-border-terminal border-opacity50">
                                <Pagination
                                    page={cardsResponse.page}
                                    total={cardsResponse.total}
                                    size={cardsResponse.size}
                                    setPage={setPage}
                                />
                            </div>
                        )}
                    </div>
                )}
            </div>

        </div>
    );
}
