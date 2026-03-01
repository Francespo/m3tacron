"use client";

import { useState, ReactNode } from "react";
import { ChevronDown, ChevronRight } from "lucide-react";

export function Accordion({ title, children, defaultOpen = true }: { title: string, children: ReactNode, defaultOpen?: boolean }) {
    const [isOpen, setIsOpen] = useState(defaultOpen);

    return (
        <div className="border-b border-border-terminal last:border-0 py-3">
            <button
                onClick={() => setIsOpen(!isOpen)}
                className="flex items-center justify-between w-full text-left text-sm font-bold text-text-primary uppercase font-mono tracking-wider focus:outline-none focus:ring-1 focus:ring-border-terminal rounded"
            >
                {title}
                {isOpen ? <ChevronDown size={16} className="text-text-secondary" /> : <ChevronRight size={16} className="text-text-secondary" />}
            </button>
            <div className={`overflow-hidden transition-all duration-200 ${isOpen ? "max-h-[1000px] opacity-100 mt-3" : "max-h-0 opacity-0"}`}>
                <div className="pb-2">{children}</div>
            </div>
        </div>
    );
}
