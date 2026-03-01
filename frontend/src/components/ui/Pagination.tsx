"use client";

import { ChevronLeft, ChevronRight } from "lucide-react";

interface PaginationProps {
    page: number;
    total: number;
    size: number;
    setPage: (p: number) => void;
}

export function Pagination({ page, total, size, setPage }: PaginationProps) {
    const totalPages = Math.ceil(total / size);

    if (totalPages <= 1) return null;

    return (
        <div className="flex items-center justify-center gap-4 mt-8 py-4">
            <button
                disabled={page === 0}
                onClick={() => setPage(page - 1)}
                className="p-2 rounded bg-terminal-panel border border-border-terminal text-text-secondary hover:text-text-primary hover:border-text-primary disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                aria-label="Previous Page"
            >
                <ChevronLeft size={20} />
            </button>
            <span className="text-sm font-mono text-text-secondary tracking-widest">
                PAGE <span className="text-text-primary font-bold">{page + 1}</span> OF {totalPages}
            </span>
            <button
                disabled={page >= totalPages - 1}
                onClick={() => setPage(page + 1)}
                className="p-2 rounded bg-terminal-panel border border-border-terminal text-text-secondary hover:text-text-primary hover:border-text-primary disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                aria-label="Next Page"
            >
                <ChevronRight size={20} />
            </button>
        </div>
    );
}
