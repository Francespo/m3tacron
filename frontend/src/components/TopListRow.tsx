/**
 * TopListRow — a descriptive row for squad lists.
 *
 * Shows faction color accent, pilot breakdown with ship names
 * and upgrade names, plus the primary stat value.
 */

import { getFactionColor, FACTION_LABELS } from "@/lib/factions";
import type { ListData } from "@/lib/types";
import { FactionIcon, ShipIcon } from "./Icons";

interface TopListRowProps {
    list: ListData;
    value: string;
}

export default function TopListRow({ list, value }: TopListRowProps) {
    const color = getFactionColor(list.faction_key);
    const factionLabel = FACTION_LABELS[list.faction_key] ?? list.faction;

    return (
        <div
            className="flex flex-col gap-1 px-[14px] py-[10px] w-full border-b border-border-terminal
                 bg-[rgba(255,255,255,0.01)] hover:bg-[rgba(255,255,255,0.03)]
                 transition-colors cursor-default"
        >
            {/* Header: faction icon + spacer + value */}
            <div className="flex items-center gap-2 w-full">
                <FactionIcon faction={list.faction_key} className="text-[1.2em]" />
                <span className="text-xs text-text-secondary font-mono truncate">
                    {factionLabel}
                </span>
                <span className="ml-auto text-sm font-bold font-mono text-text-primary whitespace-nowrap">
                    {value}
                </span>
            </div>

            {/* Pilot breakdown */}
            <div className="flex flex-col gap-0.5 pl-5">
                {list.pilots.map((p, i) => (
                    <div key={i} className="flex flex-col gap-0 py-[2px]">
                        <span className="flex items-center gap-2 text-sm font-bold text-text-primary truncate">
                            {p.ship_icon && <ShipIcon xws={p.ship_icon} className="text-[1em]" />}
                            {p.name}
                        </span>
                        {p.upgrades.length > 0 && (
                            <div className="flex flex-wrap gap-x-1.5 gap-y-0">
                                {p.upgrades.map((u, j) => (
                                    <span key={j} className="text-xs text-text-secondary">
                                        {u.name}
                                    </span>
                                ))}
                            </div>
                        )}
                    </div>
                ))}
            </div>
        </div>
    );
}
