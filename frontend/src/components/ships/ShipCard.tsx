import React from 'react';
import Link from 'next/link';
import { ShipStat } from '@/lib/types';
import { ShipIcon, FactionIcon } from '@/components/Icons';
import { Badge } from '@/components/ui/Badge';
import { getFactionColor } from '@/lib/factions';

interface ShipCardProps {
    ship: ShipStat;
}

const FACTION_LABELS: Record<string, string> = {
    rebelalliance: "Rebel Alliance",
    galacticempire: "Galactic Empire",
    scumandvillainy: "Scum and Villainy",
    resistance: "Resistance",
    firstorder: "First Order",
    galacticrepublic: "Galactic Republic",
    separatistalliance: "Separatist Alliance",
};

export function ShipCard({ ship }: ShipCardProps) {
    const factionColor = getFactionColor(ship.faction_xws);
    const winRateText = ship.win_rate === "NA" ? "NA" : `${Math.round(ship.win_rate as number)}%`;
    const displayFaction = FACTION_LABELS[ship.faction_xws] || ship.faction;

    let winRateColor: "gray" | "green" | "orange" = "gray";
    if (ship.win_rate !== "NA") {
        winRateColor = (ship.win_rate as number) >= 50 ? "green" : "orange";
    }

    return (
        <Link
            href={`/cards?ship=${ship.ship_xws}&faction=${ship.faction_xws}`}
            className="block group"
        >
            <div
                className="flex flex-col bg-terminal-panel border border-border-terminal rounded-lg h-[320px] w-full p-4 transition-all duration-200 hover:-translate-y-1 hover:bg-[#1a1f2b] hover:shadow-lg"
                style={{ borderColor: undefined }}
                onMouseEnter={(e) => (e.currentTarget.style.borderColor = factionColor)}
                onMouseLeave={(e) => (e.currentTarget.style.borderColor = '')}
            >
                {/* Ship Icon */}
                <div className="flex items-center justify-center w-full h-[100px]">
                    <ShipIcon
                        xws={ship.ship_xws}
                        className="text-[80px] leading-none"
                        style={{ color: factionColor }}
                    />
                </div>

                {/* Info */}
                <div className="flex flex-col items-center w-full gap-1 mt-2">
                    <div className="font-bold text-text-primary text-base text-center leading-tight truncate w-full">
                        {ship.ship_name}
                    </div>
                    <div
                        className="text-xs font-bold text-center uppercase tracking-wider"
                        style={{ color: factionColor }}
                    >
                        {displayFaction}
                    </div>
                    <FactionIcon factionXws={ship.faction_xws} className="text-2xl mt-1" />
                </div>

                <div className="flex-grow" />

                {/* Stats */}
                <div className="flex flex-wrap justify-center w-full gap-2 pt-2 border-t border-border-terminal mt-2">
                    <Badge color="gray">{ship.popularity} LISTS</Badge>
                    <Badge color="gray">{ship.games} GAMES</Badge>
                    <Badge color={winRateColor}>{winRateText} WR</Badge>
                </div>
            </div>
        </Link>
    );
}
