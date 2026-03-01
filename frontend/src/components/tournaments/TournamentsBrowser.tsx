"use client";

import { useState } from "react";
import { useTournaments } from "@/lib/api-client";
import { Accordion } from "@/components/ui/Accordion";
import { Pagination } from "@/components/ui/Pagination";
import { RotateCcw } from "lucide-react";
import Link from "next/link";

const FORMAT_OPTIONS = [
    { label: "XWA Standard", value: 17 },
    { label: "XWA Extended", value: 18 },
    { label: "Legacy Standard", value: 13 },
    { label: "Legacy Wild Space", value: 15 },
    { label: "Legacy Epic", value: 16 },
    { label: "AMG Standard", value: 0 },
];

export function TournamentsBrowser() {
    const [page, setPage] = useState(0);
    const [search, setSearch] = useState("");
    const [formats, setFormats] = useState<number[]>([]);

    const params = new URLSearchParams();
    params.set("page", page.toString());
    params.set("size", "15");
    if (search) params.set("search", search);
    formats.forEach(f => params.append("format", f.toString()));

    const { data, isLoading } = useTournaments(params);

    const toggleFormat = (val: number) => {
        setFormats(prev =>
            prev.includes(val) ? prev.filter(f => f !== val) : [...prev, val]
        );
        setPage(0);
    };

    return (
        <div className="flex flex-col md:flex-row w-full gap-8 text-white">
            {/* Filter Sidebar */}
            <div className="w-full md:min-w-[280px] md:max-w-[280px] shrink-0 flex flex-col gap-6">
                <div className="flex items-center justify-between">
                    <h2 className="text-sm font-bold tracking-[1px] text-text-primary uppercase">
                        TOURNAMENT FILTERS
                    </h2>
                    <button
                        onClick={() => { setSearch(""); setFormats([]); setPage(0); }}
                        className="p-1 text-text-secondary hover:text-text-primary hover:bg-[rgba(255,255,255,0.1)] rounded transition-colors"
                        title="Reset Filters"
                    >
                        <RotateCcw size={16} />
                    </button>
                </div>

                <Accordion title="FORMAT" defaultOpen={true}>
                    <div className="flex flex-col gap-3">
                        {FORMAT_OPTIONS.map(opt => (
                            <div key={opt.value} className="flex items-center gap-3 cursor-pointer group" onClick={() => toggleFormat(opt.value)}>
                                <div className={`w-4 h-4 rounded border flex items-center justify-center transition-colors ${formats.includes(opt.value) ? 'bg-[#4facfe] border-[#4facfe]' : 'border-border-terminal group-hover:border-text-secondary'}`}>
                                    {formats.includes(opt.value) && <div className="w-1.5 h-1.5 bg-terminal-bg rounded-sm" />}
                                </div>
                                <span className="text-sm font-mono text-text-secondary group-hover:text-text-primary transition-colors select-none">{opt.label}</span>
                            </div>
                        ))}
                    </div>
                </Accordion>

                <div className="flex flex-col gap-2 mt-4">
                    <span className="text-[10px] font-bold text-text-secondary font-mono tracking-[1px] uppercase">Search Name</span>
                    <input
                        type="text"
                        value={search}
                        onChange={(e) => { setSearch(e.target.value); setPage(0); }}
                        placeholder="Search name..."
                        className="bg-terminal-bg border border-border-terminal rounded-md p-3 text-sm text-text-primary font-mono focus:outline-none focus:border-text-primary shadow-[inset_0_1px_0_rgba(255,255,255,0.03)] transition-colors"
                    />
                </div>
            </div>

            {/* Main Content */}
            <div className="flex-1 flex flex-col min-w-0">
                <div className="border-b border-border-terminal pb-6 mb-6">
                    <h1 className="text-[28px] font-bold font-sans text-text-primary">Tournaments</h1>
                </div>

                {isLoading ? (
                    <div className="text-text-secondary animate-pulse font-mono tracking-widest">LOADING...</div>
                ) : (
                    <>
                        <div className="mb-4 text-sm font-mono text-text-secondary tracking-widest">
                            {data?.total || 0} TOURNAMENTS FOUND
                        </div>
                        {data?.items && data.items.length > 0 ? (
                            <div className="flex flex-col gap-0 border border-border-terminal rounded-md overflow-hidden bg-terminal-panel shadow-[inset_0_1px_0_rgba(255,255,255,0.03)]">
                                {data.items.map((t: any) => (
                                    <TournamentRow key={t.id} tournament={t} />
                                ))}
                            </div>
                        ) : (
                            <div className="w-full py-16 flex flex-col items-center justify-center border border-border-terminal rounded-md bg-terminal-panel gap-3">
                                <span className="text-text-secondary tracking-widest font-mono font-bold">0 TOURNAMENTS FOUND</span>
                                <span className="text-sm text-text-secondary">No tournaments match your current filters.</span>
                            </div>
                        )}
                        <Pagination
                            page={data?.page || 0}
                            total={data?.total || 0}
                            size={data?.size || 15}
                            setPage={setPage}
                        />
                    </>
                )}
            </div>
        </div>
    );
}

function TournamentRow({ tournament }: { tournament: any }) {
    return (
        <Link href={`/tournaments/${tournament.id}`} className="flex items-center w-full min-h-[80px] p-3 border-b border-border-terminal last:border-0 transition-colors hover:bg-[rgba(255,255,255,0.03)] no-underline">
            {/* Badge */}
            <div className="w-[60px] h-[60px] rounded-md bg-terminal-bg border border-border-terminal flex flex-col items-center justify-center shrink-0 shadow-[inset_0_1px_0_rgba(255,255,255,0.03)]">
                <span className="text-sm md:text-base font-bold text-text-primary leading-none">{tournament.badge_l1}</span>
                {tournament.badge_l2 && <span className="text-[10px] md:text-xs font-bold text-text-secondary leading-none">{tournament.badge_l2}</span>}
            </div>

            {/* Info */}
            <div className="flex flex-col flex-1 pl-4 min-w-0 justify-center h-full gap-1">
                <h3 className="text-base font-bold font-sans text-white hover:text-[#4facfe] transition-colors truncate">
                    {tournament.name}
                </h3>
                <div className="flex items-center gap-2 flex-wrap text-xs">
                    <span className="text-[#4facfe] font-mono uppercase">{tournament.platform_label}</span>
                    <span className="text-border-terminal">•</span>
                    <span className="text-text-secondary font-mono">{tournament.date}</span>
                    {tournament.location && tournament.location !== "Unknown Location" && (
                        <>
                            <span className="text-border-terminal">•</span>
                            <span className="text-text-secondary truncate max-w-[120px] sm:max-w-[300px]">{tournament.location}</span>
                        </>
                    )}
                </div>
            </div>

            {/* Counts */}
            <div className="flex items-center pr-1 sm:pr-4 shrink-0 h-full">
                <div className="flex flex-col items-end">
                    <span className="text-xl md:text-2xl font-bold text-text-primary font-mono leading-none">{tournament.players}</span>
                    <span className="text-[10px] text-text-secondary font-mono tracking-widest mt-1">PLY</span>
                </div>
            </div>
        </Link>
    );
}
