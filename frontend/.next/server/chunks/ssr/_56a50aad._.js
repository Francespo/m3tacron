module.exports = [
"[project]/src/components/RankingPanel.tsx [app-ssr] (ecmascript)", ((__turbopack_context__) => {
"use strict";

__turbopack_context__.s([
    "default",
    ()=>RankingPanel
]);
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/next/dist/server/route-modules/app-page/vendored/ssr/react-jsx-dev-runtime.js [app-ssr] (ecmascript)");
/**
 * RankingPanel — client component that wraps a ranked list section
 * with a title and POP/WR% sort toggle.
 */ var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/next/dist/server/route-modules/app-page/vendored/ssr/react.js [app-ssr] (ecmascript)");
"use client";
;
;
function RankingPanel({ title, children }) {
    const [sort, setSort] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["useState"])("popularity");
    return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
        className: "panel flex flex-col gap-2",
        children: [
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                className: "flex items-center gap-3 w-full",
                children: [
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("h3", {
                        className: "text-sm font-bold tracking-wider text-text-primary font-mono uppercase",
                        children: title
                    }, void 0, false, {
                        fileName: "[project]/src/components/RankingPanel.tsx",
                        lineNumber: 23,
                        columnNumber: 17
                    }, this),
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                        className: "ml-auto flex bg-terminal-bg rounded overflow-hidden border border-border-terminal",
                        children: [
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("button", {
                                onClick: ()=>setSort("popularity"),
                                className: `px-2.5 py-1 text-xs font-mono font-bold transition-colors ${sort === "popularity" ? "bg-border-terminal text-text-primary" : "text-text-secondary hover:text-text-primary"}`,
                                children: "POP"
                            }, void 0, false, {
                                fileName: "[project]/src/components/RankingPanel.tsx",
                                lineNumber: 27,
                                columnNumber: 21
                            }, this),
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("button", {
                                onClick: ()=>setSort("win_rate"),
                                className: `px-2.5 py-1 text-xs font-mono font-bold transition-colors ${sort === "win_rate" ? "bg-border-terminal text-text-primary" : "text-text-secondary hover:text-text-primary"}`,
                                children: "WR%"
                            }, void 0, false, {
                                fileName: "[project]/src/components/RankingPanel.tsx",
                                lineNumber: 36,
                                columnNumber: 21
                            }, this)
                        ]
                    }, void 0, true, {
                        fileName: "[project]/src/components/RankingPanel.tsx",
                        lineNumber: 26,
                        columnNumber: 17
                    }, this)
                ]
            }, void 0, true, {
                fileName: "[project]/src/components/RankingPanel.tsx",
                lineNumber: 22,
                columnNumber: 13
            }, this),
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                className: "flex flex-col",
                children: children(sort)
            }, void 0, false, {
                fileName: "[project]/src/components/RankingPanel.tsx",
                lineNumber: 49,
                columnNumber: 13
            }, this)
        ]
    }, void 0, true, {
        fileName: "[project]/src/components/RankingPanel.tsx",
        lineNumber: 20,
        columnNumber: 9
    }, this);
}
}),
"[project]/src/lib/factions.ts [app-ssr] (ecmascript)", ((__turbopack_context__) => {
"use strict";

/**
 * Faction color mapping.
 *
 * Matches FACTION_COLORS from m3tacron/theme.py exactly.
 */ __turbopack_context__.s([
    "FACTION_COLORS",
    ()=>FACTION_COLORS,
    "FACTION_LABELS",
    ()=>FACTION_LABELS,
    "getFactionColor",
    ()=>getFactionColor
]);
const FACTION_COLORS = {
    rebelalliance: "#FF3333",
    galacticempire: "#2979FF",
    scumandvillainy: "#006400",
    resistance: "#FF8C00",
    firstorder: "#800020",
    galacticrepublic: "#E6D690",
    separatistalliance: "#607D8B",
    unknown: "#666666"
};
function getFactionColor(factionKey) {
    return FACTION_COLORS[factionKey] ?? FACTION_COLORS.unknown;
}
const FACTION_LABELS = {
    rebelalliance: "Rebel Alliance",
    galacticempire: "Galactic Empire",
    scumandvillainy: "Scum & Villainy",
    resistance: "Resistance",
    firstorder: "First Order",
    galacticrepublic: "Galactic Republic",
    separatistalliance: "Separatist Alliance",
    unknown: "Unknown"
};
}),
"[project]/src/components/TopItemRow.tsx [app-ssr] (ecmascript)", ((__turbopack_context__) => {
"use strict";

/**
 * TopItemRow — a ranked row in a leaderboard list.
 *
 * Renders rank number, name, subvalue, and primary value.
 * Hover effect matches the original Reflex style.
 */ __turbopack_context__.s([
    "default",
    ()=>TopItemRow
]);
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/next/dist/server/route-modules/app-page/vendored/ssr/react-jsx-dev-runtime.js [app-ssr] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$src$2f$lib$2f$factions$2e$ts__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/src/lib/factions.ts [app-ssr] (ecmascript)");
;
;
function TopItemRow({ rank, name, value, subvalue, factionKey }) {
    // Colored left accent for faction items
    const accentColor = factionKey ? (0, __TURBOPACK__imported__module__$5b$project$5d2f$src$2f$lib$2f$factions$2e$ts__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["getFactionColor"])(factionKey) : undefined;
    return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
        className: "flex items-center gap-3 px-3 py-2 w-full border-b border-border-terminal   bg-[rgba(255,255,255,0.02)] hover:bg-[rgba(255,255,255,0.05)]   transition-colors cursor-default",
        children: [
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                className: "w-8 h-8 flex items-center justify-center rounded-full   border border-border-terminal shrink-0 font-mono text-sm   font-bold text-text-secondary",
                style: accentColor ? {
                    borderColor: accentColor,
                    color: accentColor
                } : undefined,
                children: [
                    "#",
                    rank
                ]
            }, void 0, true, {
                fileName: "[project]/src/components/TopItemRow.tsx",
                lineNumber: 35,
                columnNumber: 13
            }, this),
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                className: "flex flex-col min-w-0 flex-1",
                children: [
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                        className: "text-sm font-bold text-text-primary truncate",
                        children: name
                    }, void 0, false, {
                        fileName: "[project]/src/components/TopItemRow.tsx",
                        lineNumber: 46,
                        columnNumber: 17
                    }, this),
                    subvalue && /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                        className: "text-xs text-text-secondary font-mono",
                        children: subvalue
                    }, void 0, false, {
                        fileName: "[project]/src/components/TopItemRow.tsx",
                        lineNumber: 48,
                        columnNumber: 21
                    }, this)
                ]
            }, void 0, true, {
                fileName: "[project]/src/components/TopItemRow.tsx",
                lineNumber: 45,
                columnNumber: 13
            }, this),
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                className: "text-sm font-bold font-mono text-text-primary whitespace-nowrap ml-auto",
                children: value
            }, void 0, false, {
                fileName: "[project]/src/components/TopItemRow.tsx",
                lineNumber: 53,
                columnNumber: 13
            }, this)
        ]
    }, void 0, true, {
        fileName: "[project]/src/components/TopItemRow.tsx",
        lineNumber: 29,
        columnNumber: 9
    }, this);
}
}),
"[project]/src/components/Icons.tsx [app-ssr] (ecmascript)", ((__turbopack_context__) => {
"use strict";

__turbopack_context__.s([
    "FactionIcon",
    ()=>FactionIcon,
    "ShipIcon",
    ()=>ShipIcon
]);
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/next/dist/server/route-modules/app-page/vendored/ssr/react-jsx-dev-runtime.js [app-ssr] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$src$2f$lib$2f$factions$2e$ts__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/src/lib/factions.ts [app-ssr] (ecmascript)");
;
;
const FACTION_ICONS = {
    rebelalliance: "xwing-miniatures-font-rebel",
    galacticempire: "xwing-miniatures-font-empire",
    scumandvillainy: "xwing-miniatures-font-scum",
    resistance: "xwing-miniatures-font-rebel",
    firstorder: "xwing-miniatures-font-firstorder",
    galacticrepublic: "xwing-miniatures-font-republic",
    separatistalliance: "xwing-miniatures-font-separatists"
};
function FactionIcon({ faction, className = "" }) {
    const iconClass = FACTION_ICONS[faction] ?? "";
    const color = (0, __TURBOPACK__imported__module__$5b$project$5d2f$src$2f$lib$2f$factions$2e$ts__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["getFactionColor"])(faction);
    if (!iconClass) return null;
    return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("i", {
        className: `xwing-miniatures-font ${iconClass} ${className}`,
        style: {
            color,
            fontStyle: "normal"
        }
    }, void 0, false, {
        fileName: "[project]/src/components/Icons.tsx",
        lineNumber: 20,
        columnNumber: 9
    }, this);
}
function ShipIcon({ xws, className = "" }) {
    if (!xws) return null;
    // Normalize XWS for icons (e.g. tieininterceptor -> tieinterceptor)
    let cleanName = xws.toLowerCase().replace("xwing-miniatures-ship-", "");
    if (cleanName === "tieininterceptor") {
        cleanName = "tieinterceptor";
    }
    return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("i", {
        className: `xwing-miniatures-ship xwing-miniatures-ship-${cleanName} ${className}`,
        style: {
            fontStyle: "normal"
        }
    }, void 0, false, {
        fileName: "[project]/src/components/Icons.tsx",
        lineNumber: 37,
        columnNumber: 9
    }, this);
}
}),
"[project]/src/components/TopListRow.tsx [app-ssr] (ecmascript)", ((__turbopack_context__) => {
"use strict";

/**
 * TopListRow — a descriptive row for squad lists.
 *
 * Shows faction color accent, pilot breakdown with ship names
 * and upgrade names, plus the primary stat value.
 */ __turbopack_context__.s([
    "default",
    ()=>TopListRow
]);
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/next/dist/server/route-modules/app-page/vendored/ssr/react-jsx-dev-runtime.js [app-ssr] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$src$2f$lib$2f$factions$2e$ts__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/src/lib/factions.ts [app-ssr] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$src$2f$components$2f$Icons$2e$tsx__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/src/components/Icons.tsx [app-ssr] (ecmascript)");
;
;
;
function TopListRow({ list, value }) {
    const color = (0, __TURBOPACK__imported__module__$5b$project$5d2f$src$2f$lib$2f$factions$2e$ts__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["getFactionColor"])(list.faction_key);
    const factionLabel = __TURBOPACK__imported__module__$5b$project$5d2f$src$2f$lib$2f$factions$2e$ts__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["FACTION_LABELS"][list.faction_key] ?? list.faction;
    return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
        className: "flex flex-col gap-1 px-[14px] py-[10px] w-full border-b border-border-terminal   bg-[rgba(255,255,255,0.01)] hover:bg-[rgba(255,255,255,0.03)]   transition-colors cursor-default",
        children: [
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                className: "flex items-center gap-2 w-full",
                children: [
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$src$2f$components$2f$Icons$2e$tsx__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["FactionIcon"], {
                        faction: list.faction_key,
                        className: "text-[1.2em]"
                    }, void 0, false, {
                        fileName: "[project]/src/components/TopListRow.tsx",
                        lineNumber: 29,
                        columnNumber: 17
                    }, this),
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                        className: "text-xs text-text-secondary font-mono truncate",
                        children: factionLabel
                    }, void 0, false, {
                        fileName: "[project]/src/components/TopListRow.tsx",
                        lineNumber: 30,
                        columnNumber: 17
                    }, this),
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                        className: "ml-auto text-sm font-bold font-mono text-text-primary whitespace-nowrap",
                        children: value
                    }, void 0, false, {
                        fileName: "[project]/src/components/TopListRow.tsx",
                        lineNumber: 33,
                        columnNumber: 17
                    }, this)
                ]
            }, void 0, true, {
                fileName: "[project]/src/components/TopListRow.tsx",
                lineNumber: 28,
                columnNumber: 13
            }, this),
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                className: "flex flex-col gap-0.5 pl-5",
                children: list.pilots.map((p, i)=>/*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                        className: "flex flex-col gap-0 py-[2px]",
                        children: [
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                className: "flex items-center gap-2 text-sm font-bold text-text-primary truncate",
                                children: [
                                    p.ship_icon && /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$src$2f$components$2f$Icons$2e$tsx__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["ShipIcon"], {
                                        xws: p.ship_icon,
                                        className: "text-[1em]"
                                    }, void 0, false, {
                                        fileName: "[project]/src/components/TopListRow.tsx",
                                        lineNumber: 43,
                                        columnNumber: 45
                                    }, this),
                                    p.name
                                ]
                            }, void 0, true, {
                                fileName: "[project]/src/components/TopListRow.tsx",
                                lineNumber: 42,
                                columnNumber: 25
                            }, this),
                            p.upgrades.length > 0 && /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                className: "flex flex-wrap gap-x-1.5 gap-y-0",
                                children: p.upgrades.map((u, j)=>/*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                        className: "text-xs text-text-secondary",
                                        children: u.name
                                    }, j, false, {
                                        fileName: "[project]/src/components/TopListRow.tsx",
                                        lineNumber: 49,
                                        columnNumber: 37
                                    }, this))
                            }, void 0, false, {
                                fileName: "[project]/src/components/TopListRow.tsx",
                                lineNumber: 47,
                                columnNumber: 29
                            }, this)
                        ]
                    }, i, true, {
                        fileName: "[project]/src/components/TopListRow.tsx",
                        lineNumber: 41,
                        columnNumber: 21
                    }, this))
            }, void 0, false, {
                fileName: "[project]/src/components/TopListRow.tsx",
                lineNumber: 39,
                columnNumber: 13
            }, this)
        ]
    }, void 0, true, {
        fileName: "[project]/src/components/TopListRow.tsx",
        lineNumber: 22,
        columnNumber: 9
    }, this);
}
}),
"[project]/src/components/DashboardRankings.tsx [app-ssr] (ecmascript)", ((__turbopack_context__) => {
"use strict";

__turbopack_context__.s([
    "default",
    ()=>DashboardRankings
]);
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/next/dist/server/route-modules/app-page/vendored/ssr/react-jsx-dev-runtime.js [app-ssr] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$src$2f$components$2f$RankingPanel$2e$tsx__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/src/components/RankingPanel.tsx [app-ssr] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$src$2f$components$2f$TopItemRow$2e$tsx__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/src/components/TopItemRow.tsx [app-ssr] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$src$2f$components$2f$TopListRow$2e$tsx__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/src/components/TopListRow.tsx [app-ssr] (ecmascript)");
"use client";
;
;
;
;
/** Sort helper: returns a sorted copy of the array by the given key. */ function sortedBy(items, key) {
    return [
        ...items
    ].sort((a, b)=>{
        const av = Number(a[key]) || 0;
        const bv = Number(b[key]) || 0;
        return bv - av;
    });
}
/** Sort ListData objects (which have different field names). */ function sortedLists(items, key) {
    return [
        ...items
    ].sort((a, b)=>{
        const av = key === "popularity" ? a.count : a.win_rate;
        const bv = key === "popularity" ? b.count : b.win_rate;
        return bv - av;
    });
}
function DashboardRankings({ lists, ships, pilots, upgrades }) {
    return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
        className: "grid grid-cols-1 md:grid-cols-2 gap-4 w-full",
        children: [
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                className: "flex flex-col gap-6",
                children: [
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$src$2f$components$2f$RankingPanel$2e$tsx__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["default"], {
                        title: "TOP SQUAD LISTS",
                        children: (sort)=>{
                            const sorted = sortedLists(lists, sort);
                            return sorted.slice(0, 5).map((l, i)=>/*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$src$2f$components$2f$TopListRow$2e$tsx__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["default"], {
                                    list: l,
                                    value: sort === "win_rate" ? `${l.win_rate}%` : `${l.count}`
                                }, i, false, {
                                    fileName: "[project]/src/components/DashboardRankings.tsx",
                                    lineNumber: 56,
                                    columnNumber: 29
                                }, this));
                        }
                    }, void 0, false, {
                        fileName: "[project]/src/components/DashboardRankings.tsx",
                        lineNumber: 52,
                        columnNumber: 17
                    }, this),
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$src$2f$components$2f$RankingPanel$2e$tsx__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["default"], {
                        title: "TOP CHASSIS",
                        children: (sort)=>{
                            const sorted = sortedBy(ships, sort);
                            return sorted.slice(0, 5).map((s, i)=>/*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$src$2f$components$2f$TopItemRow$2e$tsx__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["default"], {
                                    rank: i + 1,
                                    name: s.ship_name,
                                    value: `${s.popularity} Lists`,
                                    subvalue: `${s.win_rate}% WR`
                                }, i, false, {
                                    fileName: "[project]/src/components/DashboardRankings.tsx",
                                    lineNumber: 74,
                                    columnNumber: 29
                                }, this));
                        }
                    }, void 0, false, {
                        fileName: "[project]/src/components/DashboardRankings.tsx",
                        lineNumber: 70,
                        columnNumber: 17
                    }, this)
                ]
            }, void 0, true, {
                fileName: "[project]/src/components/DashboardRankings.tsx",
                lineNumber: 50,
                columnNumber: 13
            }, this),
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                className: "flex flex-col gap-6",
                children: [
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$src$2f$components$2f$RankingPanel$2e$tsx__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["default"], {
                        title: "TOP PILOTS",
                        children: (sort)=>{
                            const sorted = sortedBy(pilots, sort);
                            return sorted.slice(0, 5).map((p, i)=>/*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$src$2f$components$2f$TopItemRow$2e$tsx__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["default"], {
                                    rank: i + 1,
                                    name: p.name,
                                    value: `${p.popularity} Lists`,
                                    subvalue: `${p.win_rate}% WR`,
                                    factionKey: p.faction
                                }, i, false, {
                                    fileName: "[project]/src/components/DashboardRankings.tsx",
                                    lineNumber: 93,
                                    columnNumber: 29
                                }, this));
                        }
                    }, void 0, false, {
                        fileName: "[project]/src/components/DashboardRankings.tsx",
                        lineNumber: 89,
                        columnNumber: 17
                    }, this),
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$src$2f$components$2f$RankingPanel$2e$tsx__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["default"], {
                        title: "TOP UPGRADES",
                        children: (sort)=>{
                            const sorted = sortedBy(upgrades, sort);
                            return sorted.slice(0, 5).map((u, i)=>/*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$src$2f$components$2f$TopItemRow$2e$tsx__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["default"], {
                                    rank: i + 1,
                                    name: u.name,
                                    value: `${u.popularity} Lists`,
                                    subvalue: `${u.win_rate}% WR`
                                }, i, false, {
                                    fileName: "[project]/src/components/DashboardRankings.tsx",
                                    lineNumber: 110,
                                    columnNumber: 29
                                }, this));
                        }
                    }, void 0, false, {
                        fileName: "[project]/src/components/DashboardRankings.tsx",
                        lineNumber: 106,
                        columnNumber: 17
                    }, this)
                ]
            }, void 0, true, {
                fileName: "[project]/src/components/DashboardRankings.tsx",
                lineNumber: 87,
                columnNumber: 13
            }, this)
        ]
    }, void 0, true, {
        fileName: "[project]/src/components/DashboardRankings.tsx",
        lineNumber: 48,
        columnNumber: 9
    }, this);
}
}),
"[project]/node_modules/next/dist/server/route-modules/app-page/vendored/ssr/react-jsx-dev-runtime.js [app-ssr] (ecmascript)", ((__turbopack_context__, module, exports) => {
"use strict";

module.exports = __turbopack_context__.r("[project]/node_modules/next/dist/server/route-modules/app-page/module.compiled.js [app-ssr] (ecmascript)").vendored['react-ssr'].ReactJsxDevRuntime; //# sourceMappingURL=react-jsx-dev-runtime.js.map
}),
];

//# sourceMappingURL=_56a50aad._.js.map