"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
    Home,
    Database,
    Swords,
    List,
    Rocket,
    StickyNote,
    Menu,
    X,
    ChevronLeft,
    ChevronRight,
    Coffee
} from "lucide-react";
import { useState } from "react";

const NAV_ITEMS = [
    { name: "DASHBOARD", href: "/", icon: Home },
    { name: "TOURNAMENTS", href: "/tournaments", icon: Database },
    { name: "SQUADRONS", href: "/squadrons", icon: Swords },
    { name: "LISTS", href: "/lists", icon: List },
    { name: "SHIPS", href: "/ships", icon: Rocket },
    { name: "CARDS", href: "/cards", icon: StickyNote },
];

export function SidebarContent({ collapsed, setCollapsed }: { collapsed: boolean; setCollapsed?: (val: boolean) => void }) {
    const pathname = usePathname();

    return (
        <div className="flex flex-col h-full bg-terminal-panel border-r border-border-terminal w-full">
            {/* Header / Brand */}
            <div className={`p-6 border-b border-border-terminal flex flex-col ${collapsed ? 'items-center p-6 px-2' : ''}`}>
                <div className="font-sans font-medium text-text-primary tracking-[0.15em] flex items-center justify-between">
                    <span className={collapsed ? "text-xl" : "text-2xl"}>
                        {collapsed ? "M3" : "M3TACRON"}
                    </span>
                </div>
                {!collapsed && <div className="text-xs text-text-secondary font-mono mt-1">v2.0.0</div>}
            </div>

            {/* Collapse Toggle (Desktop only normally, handled by prop) */}
            {setCollapsed && (
                <div className={`p-2 flex ${collapsed ? 'justify-center' : 'justify-end'}`}>
                    <button
                        onClick={() => setCollapsed(!collapsed)}
                        className="p-1 text-text-secondary hover:text-text-primary hover:bg-[rgba(255,255,255,0.05)] rounded focus:outline-none transition-colors"
                    >
                        {collapsed ? <ChevronRight size={16} /> : <ChevronLeft size={16} />}
                    </button>
                </div>
            )}

            {/* Navigation */}
            <div className="flex-1 py-2 flex flex-col">
                {NAV_ITEMS.map((item) => {
                    const isActive = pathname === item.href;
                    return (
                        <Link
                            key={item.name}
                            href={item.href}
                            className={`
                                flex items-center gap-3 px-4 py-2 w-full transition-colors
                                ${collapsed ? 'justify-center px-0 py-3' : ''}
                                ${isActive ? 'bg-[rgba(255,255,255,0.05)] border-l-2 border-text-primary text-text-primary' : 'border-l-2 border-transparent text-text-secondary hover:bg-[rgba(255,255,255,0.03)] hover:text-text-primary'}
                            `}
                        >
                            <item.icon size={18} className="shrink-0" />
                            {!collapsed && (
                                <>
                                    <span className="text-sm font-medium font-sans flex-1">{item.name}</span>
                                    {isActive && <span className="text-text-primary font-mono select-none">{"<"}</span>}
                                </>
                            )}
                        </Link>
                    );
                })}
            </div>

            {/* Footer */}
            {!collapsed && (
                <div className="p-4 border-t border-border-terminal flex flex-col items-center gap-1">
                    <div className="text-xs font-bold text-text-secondary font-sans tracking-wide">M3taCron Analytics</div>
                    <div className="text-xs text-text-secondary font-sans mb-2">Built by Francespo</div>
                    <a
                        href="https://ko-fi.com/francespo"
                        target="_blank"
                        rel="noreferrer"
                        className="flex items-center justify-center gap-2 w-full py-1.5 px-3 bg-[rgba(234,88,12,0.1)] text-orange-500 hover:bg-[rgba(234,88,12,0.2)] rounded text-xs font-mono transition-colors"
                    >
                        <Coffee size={14} /> Support on Ko-fi
                    </a>
                    <div className="w-full h-px bg-border-terminal opacity-50 my-2"></div>
                    <div className="text-[10px] text-[#555555] font-sans text-center leading-tight">
                        Star Wars and all related properties are © & ™ Lucasfilm Ltd. and/or The Walt Disney Company. This fan-created site is for informational purposes only.
                    </div>
                </div>
            )}
        </div>
    );
}

export function Sidebar() {
    const [collapsed, setCollapsed] = useState(false);

    return (
        <aside
            className={`
                fixed left-0 top-0 h-screen z-40 hidden md:block transition-all duration-200
                ${collapsed ? 'w-[60px]' : 'w-[260px]'}
            `}
        >
            <SidebarContent collapsed={collapsed} setCollapsed={setCollapsed} />
        </aside>
    );
}

export function MobileHeader({ mobileMenuOpen, setMobileMenuOpen }: { mobileMenuOpen: boolean; setMobileMenuOpen: (val: boolean) => void }) {
    return (
        <header className="md:hidden fixed top-0 left-0 right-0 h-[60px] bg-terminal-bg border-b border-border-terminal z-30 flex items-center justify-between px-4">
            <button
                onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
                className="p-1 text-text-primary hover:bg-[rgba(255,255,255,0.05)] rounded focus:outline-none transition-colors"
            >
                <Menu size={24} />
            </button>
            <div className="font-sans font-medium text-text-primary text-xl tracking-[0.15em]">
                M3TACRON
            </div>
            <div className="w-6" /> {/* Spacer to center the title */}
        </header>
    );
}
