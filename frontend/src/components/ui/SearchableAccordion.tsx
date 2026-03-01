"use client";

import { useState } from "react";
import { ChevronDown, ChevronRight, Search } from "lucide-react";

interface Option {
    label: string;
    value: string;
}

interface SearchableAccordionProps {
    title: string;
    options: Option[];
    selectedValues: string[];
    onToggle: (value: string) => void;
    defaultOpen?: boolean;
}

export function SearchableAccordion({ title, options, selectedValues, onToggle, defaultOpen = true }: SearchableAccordionProps) {
    const [isOpen, setIsOpen] = useState(defaultOpen);
    const [search, setSearch] = useState("");

    const filteredOptions = options.filter(opt => opt.label.toLowerCase().includes(search.toLowerCase()));

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
                <div className="pb-2 flex flex-col gap-3">
                    <div className="relative">
                        <Search size={14} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-text-secondary" />
                        <input
                            type="text"
                            placeholder="Search..."
                            value={search}
                            onChange={(e) => setSearch(e.target.value)}
                            className="w-full bg-terminal-bg border border-border-terminal rounded-md py-1.5 pl-8 pr-3 text-sm text-text-primary font-mono focus:outline-none focus:border-text-primary"
                        />
                    </div>
                    <div className="flex flex-col gap-2 max-h-60 overflow-y-auto pr-1 stylish-scrollbar">
                        {filteredOptions.length > 0 ? filteredOptions.map(opt => (
                            <div key={opt.value} className="flex items-center justify-between cursor-pointer group" onClick={() => onToggle(opt.value)}>
                                <span className="text-sm font-mono text-text-secondary group-hover:text-text-primary transition-colors select-none truncate mr-2" title={opt.label}>
                                    {opt.label}
                                </span>
                                <div className={`shrink-0 w-4 h-4 rounded border flex items-center justify-center transition-colors ${selectedValues.includes(opt.value) ? 'bg-[#4facfe] border-[#4facfe]' : 'border-border-terminal group-hover:border-text-secondary'}`}>
                                    {selectedValues.includes(opt.value) && <div className="w-1.5 h-1.5 bg-terminal-bg rounded-sm" />}
                                </div>
                            </div>
                        )) : (
                            <div className="text-xs text-text-secondary italic font-sans py-2">No items found.</div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}
