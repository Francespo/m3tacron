/**
 * TopItemRow — a ranked row in a leaderboard list.
 *
 * Renders rank number, name, subvalue, and primary value.
 * Hover effect matches the original Reflex style.
 */

import { getFactionColor } from "@/lib/factions";
import { ShipIcon, FactionIcon } from "./Icons";

interface TopItemRowProps {
    rank: number;
    name: string;
    value: string;
    subvalue?: string;
    factionKey?: string;
    isShip?: boolean;
    shipXws?: string;
}

export default function TopItemRow({
    rank,
    name,
    value,
    subvalue,
    factionKey,
    isShip,
    shipXws,
}: TopItemRowProps) {
    // Colored left accent for faction items
    const accentColor = factionKey ? getFactionColor(factionKey) : undefined;

    return (
        <div
            className="flex items-center gap-3 px-3 py-2 w-full border-b border-border-terminal
                 bg-[rgba(255,255,255,0.02)] hover:bg-[rgba(255,255,255,0.05)]
                 transition-colors cursor-default"
        >
            {/* Icon or Rank badge */}
            {isShip && shipXws ? (
                <div className="w-8 h-8 flex items-center justify-center rounded bg-[rgba(255,255,255,0.05)] shrink-0 mr-1">
                    <ShipIcon xws={shipXws} className="text-[1.3em] text-text-primary" />
                </div>
            ) : factionKey ? (
                <div className="w-8 h-8 flex items-center justify-center rounded-full border border-border-terminal shrink-0 mr-1"
                    style={{ borderColor: accentColor }}>
                    <FactionIcon faction={factionKey} className="text-[1.2em]" />
                </div>
            ) : (
                <div className="w-8 h-8 flex items-center justify-center rounded-full
                       border border-border-terminal shrink-0 font-mono text-sm
                       font-bold text-text-secondary mr-1">
                    #{rank}
                </div>
            )}

            {/* Name + subvalue */}
            <div className="flex flex-col min-w-0 flex-1">
                <span className="text-sm font-bold text-text-primary truncate">{name}</span>
                {subvalue && (
                    <span className="text-xs text-text-secondary font-mono">{subvalue}</span>
                )}
            </div>

            {/* Primary value */}
            <span className="text-sm font-bold font-mono text-text-primary whitespace-nowrap ml-auto">
                {value}
            </span>
        </div>
    );
}
