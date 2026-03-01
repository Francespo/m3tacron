import { ListData, PilotData, UpgradeData } from "@/lib/types";
import { FactionIcon, ShipIcon, UpgradeIcon } from "@/components/Icons";
import { getFactionColor } from "@/lib/factions";

function PilotBlock({ pilot }: { pilot: PilotData }) {
    return (
        <div className="flex flex-col gap-2 p-2 w-full md:min-w-[250px] flex-1 bg-[rgba(255,255,255,0.03)] rounded-lg">
            {/* Top row: Ship Icon + Pilot Title + Stats */}
            <div className="flex items-center gap-2 w-full cursor-pointer hover:text-text-primary transition-colors group">
                <ShipIcon xws={pilot.ship_icon} className="text-4xl text-text-primary group-hover:text-[#4facfe] transition-colors" />
                <div className="flex flex-col">
                    <span className="text-sm font-bold font-sans text-white group-hover:text-[#4facfe] transition-colors">{pilot.name}</span>
                    <div className="flex items-center gap-2">
                        <span className="text-[10px] text-text-secondary font-mono">{pilot.points} pts</span>
                        {pilot.loadout > 0 && <span className="text-[10px] text-text-secondary font-mono">LV: {pilot.loadout}</span>}
                    </div>
                </div>
            </div>

            {/* Upgrades */}
            <div className="flex flex-wrap gap-1 w-full">
                {pilot.upgrades.map((upg, i) => (
                    <div key={i} className="flex items-center gap-1 px-1.5 py-0.5 border border-border-terminal rounded bg-[rgba(0,0,0,0.3)] cursor-pointer hover:bg-[rgba(255,255,255,0.1)] hover:border-text-secondary transition-colors" title={upg.name}>
                        <UpgradeIcon slot={upg.slot} className="text-[12px] text-text-primary" />
                        <span className="text-[10px] text-text-secondary whitespace-nowrap">{upg.name} ({upg.points})</span>
                    </div>
                ))}
            </div>
        </div>
    );
}

export function ListRow({ list }: { list: ListData }) {
    const factionColor = getFactionColor(list.faction_key);

    return (
        <div className="flex w-full bg-terminal-panel border border-border-terminal rounded-md overflow-hidden hover:border-text-secondary transition-colors group shadow-[inset_0_1px_0_rgba(255,255,255,0.03)]">
            {/* Color Strip */}
            <div className="w-[6px] shrink-0" style={{ backgroundColor: factionColor }} />

            {/* Content */}
            <div className="flex flex-col w-full p-3 gap-3">
                {/* Header */}
                <div className="flex flex-wrap items-center justify-between gap-2 w-full">
                    <div className="flex items-center gap-2">
                        <FactionIcon faction={list.faction_key} className="text-2xl" />
                        <span className="text-xs font-bold text-text-primary uppercase hidden sm:block">{list.faction}</span>
                    </div>

                    <div className="flex flex-wrap items-center gap-2 justify-end">
                        <span className="px-2 py-0.5 rounded bg-[rgba(255,255,255,0.1)] text-white text-[10px] font-bold font-mono border border-[rgba(255,255,255,0.2)]">{list.points} pts</span>
                        {list.total_loadout > 0 && (
                            <span className="px-2 py-0.5 rounded border border-purple-500/50 text-purple-300 text-[10px] font-bold font-mono bg-purple-500/10">LV: {list.total_loadout}</span>
                        )}
                        <span className={`px-2 py-0.5 rounded text-[10px] font-bold font-mono border ${list.win_rate >= 50 ? 'bg-green-500/10 text-green-400 border-green-500/30' : 'bg-orange-500/10 text-orange-400 border-orange-500/30'}`}>
                            {list.win_rate}% WR
                        </span>
                        <span className="text-[10px] text-text-secondary font-mono tracking-widest uppercase">{list.games} games</span>
                    </div>
                </div>

                {/* Pilots Grid */}
                <div className="flex flex-wrap gap-2 w-full">
                    {list.pilots.map((pilot, i) => (
                        <PilotBlock key={i} pilot={pilot} />
                    ))}
                </div>
            </div>
        </div>
    );
}
