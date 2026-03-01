"use client";

import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
    return twMerge(clsx(inputs));
}

interface SegmentedControlProps {
    options: { label: string; value: string }[];
    value: string;
    onChange: (value: string) => void;
    size?: "sm" | "md";
    className?: string;
}

export function SegmentedControl({ options, value, onChange, size = "md", className }: SegmentedControlProps) {
    return (
        <div className={cn("inline-flex bg-[rgba(255,255,255,0.05)] rounded-md p-1", className)}>
            {options.map((opt) => (
                <button
                    key={opt.value}
                    onClick={() => onChange(opt.value)}
                    className={cn(
                        "rounded transition-all",
                        size === "sm" ? "px-2 py-0.5 text-xs" : "px-4 py-1 text-sm",
                        value === opt.value
                            ? "bg-[rgba(255,255,255,0.15)] text-text-primary shadow-sm"
                            : "text-text-secondary hover:text-text-primary hover:bg-[rgba(255,255,255,0.08)]"
                    )}
                >
                    {opt.label}
                </button>
            ))}
        </div>
    );
}
