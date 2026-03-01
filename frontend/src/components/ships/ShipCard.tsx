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
                className="flex flex-col bg-gray-2 border border-gray-12 rounded-xl h-[350px] w-full p-4 transition-all duration-200 hover:-translate-y-1 hover:bg-gray-3"
                style={{
                    // Apply custom dynamic border color on hover using CSS variables
                    '--hover-border-color': factionColor,
                } as React.CSSProperties}
            >
                <style dangerouslySetInnerHTML={{
                    __html: `
          .group:hover > div {
            border-color: var(--hover-border-color) !important;
          }
        `}} />

                {/* Ship Icon Container */}
                <div className="flex items-center justify-center w-full h-[140px]">
                    <ShipIcon
                        xws={ship.ship_xws}
                        className="text-[120px] leading-none"
                        style={{ color: factionColor }}
                    />
                </div>

                {/* Info Stack */}
                <div className="flex flex-col items-center w-full gap-2 mt-2">
                    <div className="font-bold text-text-primary text-xl text-center leading-[1.2]">
                        {ship.ship_name}
                    </div>
                    <div
                        className="text-sm font-bold text-center"
                        style={{ color: factionColor }}
                    >
                        {displayFaction}
                    </div>
                    <FactionIcon factionXws={ship.faction_xws} className="text-3xl" />
                </div>

                <div className="flex-grow" />

                {/* Stats Badges */}
                <div className="flex flex-wrap justify-center w-full gap-2 pt-2">
                    <Badge color="gray">{ship.popularity} LISTS</Badge>
                    <Badge color="gray">{ship.games} GAMES</Badge>
                    <Badge color={winRateColor}>{winRateText} WR</Badge>
                </div>
            </div>
        </Link>
    );
}
