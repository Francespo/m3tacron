"use client";

import { BarChart, Bar, XAxis, YAxis, CartesianGrid, ResponsiveContainer, Cell, PieChart, Pie, Tooltip as RechartsTooltip } from 'recharts';
import { FactionIcon } from './Icons';

const FACTION_COLORS: Record<string, string> = {
    "rebelalliance": "#FF3333",
    "galacticempire": "#2979FF",
    "scumandvillainy": "#006400",
    "resistance": "#FF8C00",
    "firstorder": "#800020",
    "galacticrepublic": "#E6D690",
    "separatistalliance": "#607D8B",
    "unknown": "#666666"
};

export function FactionPerformanceChart({ data, dataKey, title }: { data: any[]; dataKey: string, title: string }) {
    return (
        <div className="flex flex-col w-full h-full p-5 bg-terminal-panel border border-border-terminal rounded-[6px] shadow-[inset_0_1px_0_rgba(255,255,255,0.03)]">
            <h3 className="text-sm font-bold font-mono text-text-primary mb-4 uppercase">{title}</h3>
            <div className="w-full h-[250px]">
                <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={data}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#222" vertical={false} />
                        <XAxis
                            dataKey="icon_char"
                            stroke="#AAAAAA"
                            tick={{ fontFamily: 'xwing-miniatures', fontSize: 20, fill: '#AAAAAA' }}
                            axisLine={false}
                            tickLine={false}
                            dy={10}
                        />
                        <YAxis
                            stroke="#AAAAAA"
                            tick={{ fontFamily: '"JetBrains Mono", monospace', fontSize: 10 }}
                            axisLine={false}
                            tickLine={false}
                        />
                        <RechartsTooltip
                            cursor={{ fill: 'rgba(255,255,255,0.05)' }}
                            contentStyle={{ backgroundColor: "#0A0A0A", borderColor: "#333", color: "#FFF", fontFamily: 'Inter, sans-serif' }}
                            itemStyle={{ color: "#FFF" }}
                        />
                        <Bar dataKey={dataKey} radius={[4, 4, 0, 0]} isAnimationActive={false}>
                            {data.map((entry, index) => (
                                <Cell key={`cell-${index}`} fill={FACTION_COLORS[entry.xws] || FACTION_COLORS.unknown} />
                            ))}
                        </Bar>
                    </BarChart>
                </ResponsiveContainer>
            </div>
        </div>
    );
}

export function FactionGamePieChart({ data }: { data: any[] }) {
    return (
        <div className="flex flex-col w-full h-full p-5 bg-terminal-panel border border-border-terminal rounded-[6px] shadow-[inset_0_1px_0_rgba(255,255,255,0.03)]">
            <h3 className="text-sm font-bold font-mono text-text-primary mb-4">GAME DISTRIBUTION</h3>
            <div className="w-full h-[180px]">
                <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                        <Pie
                            data={data}
                            dataKey="games"
                            nameKey="real_name"
                            cx="50%"
                            cy="50%"
                            outerRadius={70}
                            innerRadius={0}
                            isAnimationActive={false}
                        >
                            {data.map((entry, index) => (
                                <Cell key={`cell-${index}`} fill={FACTION_COLORS[entry.xws] || FACTION_COLORS.unknown} />
                            ))}
                        </Pie>
                        <RechartsTooltip
                            contentStyle={{ backgroundColor: "#0A0A0A", borderColor: "#333", color: "#FFF", fontFamily: 'Inter, sans-serif' }}
                        />
                    </PieChart>
                </ResponsiveContainer>
            </div>
            <div className="flex flex-wrap justify-center w-full mt-2 gap-x-3 gap-y-1">
                {data.map((entry, index) => (
                    <div key={index} className="flex items-center gap-1">
                        <FactionIcon factionXws={entry.xws} className="text-lg" />
                        <span className="text-xs text-text-secondary font-mono">{entry.percentage}%</span>
                    </div>
                ))}
            </div>
        </div>
    );
}
