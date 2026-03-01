import React from 'react';
import Link from 'next/link';
import { PilotStat, UpgradeStat } from '@/lib/types';
import { ShipIcon, FactionIcon } from '@/components/Icons';
import { Badge } from '@/components/ui/Badge';
import { getFactionColor } from '@/lib/factions';

const FACTION_LABELS: Record<string, string> = {
    rebelalliance: "Rebel Alliance",
    galacticempire: "Galactic Empire",
    scumandvillainy: "Scum and Villainy",
    resistance: "Resistance",
    firstorder: "First Order",
    galacticrepublic: "Galactic Republic",
    separatistalliance: "Separatist Alliance",
};

export function PilotCard({ pilot }: { pilot: PilotStat }) {
    const factionColor = getFactionColor(pilot.faction);
    const winRateText = pilot.win_rate === "NA" ? "NA" : `${Math.round(pilot.win_rate as number)}%`;
    const displayFaction = FACTION_LABELS[pilot.faction] || pilot.faction;

    let winRateColor: "gray" | "green" | "orange" = "gray";
    if (pilot.win_rate !== "NA") {
        winRateColor = (pilot.win_rate as number) >= 50 ? "green" : "orange";
    }

    return (
        <Link
            href={`/cards?pilot=${pilot.xws}`}
            className="block group"
        >
            <div className="panel h-full flex flex-col justify-between transition-colors duration-200 group-hover:border-accent-primary relative overflow-hidden group-hover:bg-[#1a1f2b]">
                <div className="p-4 flex flex-col items-center justify-center gap-4 flex-grow">
                    {/* Card Icon */}
                    <div className="relative pt-2 drop-shadow-md transition-transform duration-300 group-hover:scale-110">
                        {pilot.ship_icon && <ShipIcon xws={pilot.ship_xws} className="text-[80px] text-white" />}
                        {!pilot.ship_icon && <FactionIcon factionXws={pilot.faction} className="text-[80px] text-white" />}
                    </div>

                    <div className="text-center w-full z-10 flex flex-col items-center">
                        <h3 className="text-lg font-bold font-sans text-text-primary leading-tight truncate w-full">
                            {pilot.name}
                        </h3>
                        <div
                            className="text-xs font-bold text-center tracking-widest uppercase mt-1 mb-2"
                            style={{ color: factionColor }}
                        >
                            {displayFaction}
                        </div>
                        {/* Cost & Loadout */}
                        <div className="flex items-center justify-center gap-2 mt-2">
                            <span className="bg-terminal-bg border border-border-terminal px-2 py-0.5 rounded text-xs font-mono font-bold">
                                {pilot.cost} PTS
                            </span>
                            <span className="bg-terminal-bg border border-border-terminal px-2 py-0.5 rounded text-xs font-mono font-bold text-blue-400">
                                {pilot.loadout} LD
                            </span>
                        </div>
                    </div>
                </div>

                {/* Stats Footer */}
                <div className="w-full bg-black/40 border-t border-border-terminal group-hover:bg-accent-primary/5 transition-colors">
                    <div className="flex flex-wrap items-center justify-center gap-2 p-2">
                        <Badge color="gray">{pilot.popularity} LISTS</Badge>
                        <Badge color="gray">{pilot.games} GAMES</Badge>
                        <Badge color={winRateColor}>{winRateText} WR</Badge>
                    </div>
                </div>
            </div>
        </Link>
    );
}

export function UpgradeCard({ upgrade }: { upgrade: UpgradeStat }) {
    const winRateText = upgrade.win_rate === "NA" ? "NA" : `${Math.round(upgrade.win_rate as number)}%`;

    let winRateColor: "gray" | "green" | "orange" = "gray";
    if (upgrade.win_rate !== "NA") {
        winRateColor = (upgrade.win_rate as number) >= 50 ? "green" : "orange";
    }

    return (
        <Link
            href={`/cards?upgrade=${upgrade.xws}`}
            className="block group"
        >
            <div className="panel h-full flex flex-col justify-between transition-colors duration-200 group-hover:border-accent-primary relative overflow-hidden group-hover:bg-[#1a1f2b]">
                <div className="p-4 flex flex-col items-center justify-center gap-4 flex-grow">
                    {/* Using a generic or type-based icon for upgrades like Reflex? Here we can just show the Type */}
                    <div className="relative pt-6 pb-2 drop-shadow-md transition-transform duration-300 group-hover:scale-110">
                        <span className="text-4xl font-black text-text-muted uppercase">
                            {upgrade.type}
                        </span>
                    </div>

                    <div className="text-center w-full z-10 flex flex-col items-center">
                        <h3 className="text-lg font-bold font-sans text-text-primary leading-tight truncate w-full">
                            {upgrade.name}
                        </h3>
                        <div className="text-xs font-bold text-text-secondary tracking-widest mt-1 mb-2">
                            UPGRADE
                        </div>
                        {/* Cost */}
                        <div className="flex items-center justify-center gap-2 mt-2">
                            <span className="bg-terminal-bg border border-border-terminal px-2 py-0.5 rounded text-xs font-mono font-bold">
                                {upgrade.cost} PTS
                            </span>
                        </div>
                    </div>
                </div>

                {/* Stats Footer */}
                <div className="w-full bg-black/40 border-t border-border-terminal group-hover:bg-accent-primary/5 transition-colors">
                    <div className="flex flex-wrap items-center justify-center gap-2 p-2">
                        <Badge color="gray">{upgrade.popularity} LISTS</Badge>
                        <Badge color="gray">{upgrade.games} GAMES</Badge>
                        <Badge color={winRateColor}>{winRateText} WR</Badge>
                    </div>
                </div>
            </div>
        </Link>
    );
}
