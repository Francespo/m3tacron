"use client";

/**
 * RankingPanel — client component that wraps a ranked list section
 * with a title and POP/WR% sort toggle.
 */

import { useState, type ReactNode } from "react";

interface RankingPanelProps {
    title: string;
    /** Render function receives current sort mode. */
    children: (sortMode: "popularity" | "win_rate") => ReactNode;
}

export default function RankingPanel({ title, children }: RankingPanelProps) {
    const [sort, setSort] = useState<"popularity" | "win_rate">("popularity");

    return (
        <div className="panel flex flex-col gap-2">
            {/* Header */}
            <div className="flex items-center gap-3 w-full">
                <h3 className="text-sm font-bold tracking-wider text-text-primary font-mono uppercase">
                    {title}
                </h3>
                <div className="ml-auto flex bg-terminal-bg rounded overflow-hidden border border-border-terminal">
                    <button
                        onClick={() => setSort("popularity")}
                        className={`px-2.5 py-1 text-xs font-mono font-bold transition-colors ${sort === "popularity"
                                ? "bg-border-terminal text-text-primary"
                                : "text-text-secondary hover:text-text-primary"
                            }`}
                    >
                        POP
                    </button>
                    <button
                        onClick={() => setSort("win_rate")}
                        className={`px-2.5 py-1 text-xs font-mono font-bold transition-colors ${sort === "win_rate"
                                ? "bg-border-terminal text-text-primary"
                                : "text-text-secondary hover:text-text-primary"
                            }`}
                    >
                        WR%
                    </button>
                </div>
            </div>

            {/* Content */}
            <div className="flex flex-col">{children(sort)}</div>
        </div>
    );
}
