/**
 * TopListRow — a descriptive row for squad lists.
 *
 * Shows faction color accent, pilot breakdown with ship names
 * and upgrade names, plus the primary stat value.
 */

import { getFactionColor, FACTION_LABELS } from "@/lib/factions";
import type { ListData } from "@/lib/types";

interface TopListRowProps {
    list: ListData;
    value: string;
}

export default function TopListRow({ list, value }: TopListRowProps) {
    const color = getFactionColor(list.faction_key);
    const factionLabel = FACTION_LABELS[list.faction_key] ?? list.faction;

    return (
        <div
            className="flex flex-col gap-1 px-3 py-2.5 w-full border-b border-border-terminal
                 bg-[rgba(255,255,255,0.01)] hover:bg-[rgba(255,255,255,0.03)]
                 transition-colors cursor-default"
        >
            {/* Header: faction dot + spacer + value */}
            <div className="flex items-center gap-2 w-full">
                <span
                    className="w-3 h-3 rounded-full shrink-0"
                    style={{ backgroundColor: color }}
                    title={factionLabel}
                />
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
                    <div key={i} className="flex flex-col gap-0">
                        <span className="text-sm font-bold text-text-primary truncate">
                            {p.name}
                            {p.ship_name && (
                                <span className="text-xs text-text-secondary font-normal ml-1.5">
                                    ({p.ship_name})
                                </span>
                            )}
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
