"use client";

import { useState } from "react";
import { Sidebar, MobileHeader, SidebarContent } from "./Sidebar";
import { X } from "lucide-react";

export function AppShell({ children }: { children: React.ReactNode }) {
    const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

    // Default desktop collapsed state (using local structural assumption for now)
    // In a real app we might store this in context or localStorage
    const [desktopCollapsed] = useState(false); // we manage inside Sidebar, but we need width for margin

    return (
        <div className="relative min-h-screen bg-terminal-bg">
            <Sidebar />
            <MobileHeader mobileMenuOpen={mobileMenuOpen} setMobileMenuOpen={setMobileMenuOpen} />

            {/* Mobile Drawer Overlay */}
            {mobileMenuOpen && (
                <div className="md:hidden fixed inset-0 z-50 flex">
                    {/* Backdrop */}
                    <div
                        className="fixed inset-0 bg-black/60"
                        onClick={() => setMobileMenuOpen(false)}
                    />

                    {/* Drawer Content */}
                    <div className="relative w-[260px] h-full bg-terminal-panel flex flex-col shadow-2xl z-50">
                        {/* Close button inside drawer */}
                        <div className="absolute top-4 right-4 z-50">
                            <button
                                onClick={() => setMobileMenuOpen(false)}
                                className="p-1 text-text-secondary hover:text-text-primary hover:bg-[rgba(255,255,255,0.05)] rounded focus:outline-none transition-colors"
                            >
                                <X size={20} />
                            </button>
                        </div>
                        <SidebarContent collapsed={false} />
                    </div>
                </div>
            )}

            {/* Main Content Area */}
            <main
                className={`
                    pt-[60px] md:pt-0 
                    md:ml-[260px] 
                    transition-all duration-200 min-h-screen
                `}
            >
                {/* Note: since Sidebar manages its own collapsed state internally in this simple setup, 
                    the margin might need to be dynamic. 
                    Let's use a simpler approach: fixed width 260px for now to ensure it works.
                    A real implementation would sync the state via Context. */}
                {children}
            </main>
        </div>
    );
}
