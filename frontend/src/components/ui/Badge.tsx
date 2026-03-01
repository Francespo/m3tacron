import { ReactNode } from "react";

interface BadgeProps {
    children: ReactNode;
    color?: "gray" | "green" | "orange" | "blue" | "red";
}

export function Badge({ children, color = "gray" }: BadgeProps) {
    const colorClasses = {
        gray: "bg-terminal-panel border-border-terminal text-text-secondary",
        green: "bg-green-900/20 border-green-700 text-green-400",
        orange: "bg-orange-900/20 border-orange-700 text-orange-400",
        blue: "bg-blue-900/20 border-blue-700 text-blue-400",
        red: "bg-red-900/20 border-red-700 text-red-400"
    };

    return (
        <span className={`px-2 py-0.5 text-[10px] font-bold font-mono uppercase tracking-wider rounded-full border ${colorClasses[color]}`}>
            {children}
        </span>
    );
}
