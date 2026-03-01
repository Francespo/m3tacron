(globalThis.TURBOPACK || (globalThis.TURBOPACK = [])).push([typeof document === "object" ? document.currentScript : undefined,
"[project]/src/components/RankingPanel.tsx [app-client] (ecmascript)", ((__turbopack_context__) => {
"use strict";

__turbopack_context__.s([
    "default",
    ()=>RankingPanel
]);
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/next/dist/compiled/react/jsx-dev-runtime.js [app-client] (ecmascript)");
/**
 * RankingPanel — client component that wraps a ranked list section
 * with a title and POP/WR% sort toggle.
 */ var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/next/dist/compiled/react/index.js [app-client] (ecmascript)");
;
var _s = __turbopack_context__.k.signature();
"use client";
;
function RankingPanel(param) {
    let { title, children } = param;
    _s();
    const [sort, setSort] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useState"])("popularity");
    return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
        className: "panel flex flex-col gap-2",
        children: [
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                className: "flex items-center gap-3 w-full",
                children: [
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("h3", {
                        className: "text-sm font-bold tracking-wider text-text-primary font-mono uppercase",
                        children: title
                    }, void 0, false, {
                        fileName: "[project]/src/components/RankingPanel.tsx",
                        lineNumber: 23,
                        columnNumber: 17
                    }, this),
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                        className: "ml-auto flex bg-terminal-bg rounded overflow-hidden border border-border-terminal",
                        children: [
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("button", {
                                onClick: ()=>setSort("popularity"),
                                className: "px-2.5 py-1 text-xs font-mono font-bold transition-colors ".concat(sort === "popularity" ? "bg-border-terminal text-text-primary" : "text-text-secondary hover:text-text-primary"),
                                children: "POP"
                            }, void 0, false, {
                                fileName: "[project]/src/components/RankingPanel.tsx",
                                lineNumber: 27,
                                columnNumber: 21
                            }, this),
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("button", {
                                onClick: ()=>setSort("win_rate"),
                                className: "px-2.5 py-1 text-xs font-mono font-bold transition-colors ".concat(sort === "win_rate" ? "bg-border-terminal text-text-primary" : "text-text-secondary hover:text-text-primary"),
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
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
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
_s(RankingPanel, "IOdPr41fYZZEVUM7oZ3mPRUEc3w=");
_c = RankingPanel;
var _c;
__turbopack_context__.k.register(_c, "RankingPanel");
if (typeof globalThis.$RefreshHelpers$ === 'object' && globalThis.$RefreshHelpers !== null) {
    __turbopack_context__.k.registerExports(__turbopack_context__.m, globalThis.$RefreshHelpers$);
}
}),
"[project]/src/lib/factions.ts [app-client] (ecmascript)", ((__turbopack_context__) => {
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
    var _FACTION_COLORS_factionKey;
    return (_FACTION_COLORS_factionKey = FACTION_COLORS[factionKey]) !== null && _FACTION_COLORS_factionKey !== void 0 ? _FACTION_COLORS_factionKey : FACTION_COLORS.unknown;
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
if (typeof globalThis.$RefreshHelpers$ === 'object' && globalThis.$RefreshHelpers !== null) {
    __turbopack_context__.k.registerExports(__turbopack_context__.m, globalThis.$RefreshHelpers$);
}
}),
"[project]/src/components/Icons.tsx [app-client] (ecmascript)", ((__turbopack_context__) => {
"use strict";

__turbopack_context__.s([
    "FactionIcon",
    ()=>FactionIcon,
    "ShipIcon",
    ()=>ShipIcon,
    "UpgradeIcon",
    ()=>UpgradeIcon
]);
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/next/dist/compiled/react/jsx-dev-runtime.js [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$src$2f$lib$2f$factions$2e$ts__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/src/lib/factions.ts [app-client] (ecmascript)");
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
function FactionIcon(param) {
    let { faction, factionXws, className = "" } = param;
    const key = faction || factionXws || "";
    var _FACTION_ICONS_key;
    const iconClass = (_FACTION_ICONS_key = FACTION_ICONS[key]) !== null && _FACTION_ICONS_key !== void 0 ? _FACTION_ICONS_key : "";
    const color = (0, __TURBOPACK__imported__module__$5b$project$5d2f$src$2f$lib$2f$factions$2e$ts__$5b$app$2d$client$5d$__$28$ecmascript$29$__["getFactionColor"])(key);
    if (!iconClass) return null;
    return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("i", {
        className: "xwing-miniatures-font ".concat(iconClass, " ").concat(className),
        style: {
            color,
            fontStyle: "normal"
        }
    }, void 0, false, {
        fileName: "[project]/src/components/Icons.tsx",
        lineNumber: 21,
        columnNumber: 9
    }, this);
}
_c = FactionIcon;
function UpgradeIcon(param) {
    let { slot, className = "" } = param;
    if (!slot) return null;
    // Normalize slot for icon name
    const iconClass = "xwing-miniatures-font-".concat(slot.toLowerCase().replace(/ /g, ''));
    return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("i", {
        className: "xwing-miniatures-font ".concat(iconClass, " ").concat(className),
        style: {
            fontStyle: "normal"
        }
    }, void 0, false, {
        fileName: "[project]/src/components/Icons.tsx",
        lineNumber: 35,
        columnNumber: 9
    }, this);
}
_c1 = UpgradeIcon;
function ShipIcon(param) {
    let { xws, className = "", style } = param;
    if (!xws) return null;
    // Normalize XWS for icons (e.g. tieininterceptor -> tieinterceptor)
    let cleanName = xws.toLowerCase().replace("xwing-miniatures-ship-", "");
    if (cleanName === "tieininterceptor") {
        cleanName = "tieinterceptor";
    }
    return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("i", {
        className: "xwing-miniatures-ship xwing-miniatures-ship-".concat(cleanName, " ").concat(className),
        style: {
            fontStyle: "normal"
        }
    }, void 0, false, {
        fileName: "[project]/src/components/Icons.tsx",
        lineNumber: 52,
        columnNumber: 9
    }, this);
}
_c2 = ShipIcon;
var _c, _c1, _c2;
__turbopack_context__.k.register(_c, "FactionIcon");
__turbopack_context__.k.register(_c1, "UpgradeIcon");
__turbopack_context__.k.register(_c2, "ShipIcon");
if (typeof globalThis.$RefreshHelpers$ === 'object' && globalThis.$RefreshHelpers !== null) {
    __turbopack_context__.k.registerExports(__turbopack_context__.m, globalThis.$RefreshHelpers$);
}
}),
"[project]/src/components/TopItemRow.tsx [app-client] (ecmascript)", ((__turbopack_context__) => {
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
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/next/dist/compiled/react/jsx-dev-runtime.js [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$src$2f$lib$2f$factions$2e$ts__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/src/lib/factions.ts [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$src$2f$components$2f$Icons$2e$tsx__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/src/components/Icons.tsx [app-client] (ecmascript)");
;
;
;
function TopItemRow(param) {
    let { rank, name, value, subvalue, factionKey, isShip, shipXws } = param;
    // Colored left accent for faction items
    const accentColor = factionKey ? (0, __TURBOPACK__imported__module__$5b$project$5d2f$src$2f$lib$2f$factions$2e$ts__$5b$app$2d$client$5d$__$28$ecmascript$29$__["getFactionColor"])(factionKey) : undefined;
    return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
        className: "flex items-center gap-3 px-3 py-2 w-full border-b border-border-terminal   bg-[rgba(255,255,255,0.02)] hover:bg-[rgba(255,255,255,0.05)]   transition-colors cursor-default",
        children: [
            isShip && shipXws ? /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                className: "w-8 h-8 flex items-center justify-center rounded bg-[rgba(255,255,255,0.05)] shrink-0 mr-1",
                children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$src$2f$components$2f$Icons$2e$tsx__$5b$app$2d$client$5d$__$28$ecmascript$29$__["ShipIcon"], {
                    xws: shipXws,
                    className: "text-[1.3em] text-text-primary"
                }, void 0, false, {
                    fileName: "[project]/src/components/TopItemRow.tsx",
                    lineNumber: 42,
                    columnNumber: 21
                }, this)
            }, void 0, false, {
                fileName: "[project]/src/components/TopItemRow.tsx",
                lineNumber: 41,
                columnNumber: 17
            }, this) : factionKey ? /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                className: "w-8 h-8 flex items-center justify-center rounded-full border border-border-terminal shrink-0 mr-1",
                style: {
                    borderColor: accentColor
                },
                children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$src$2f$components$2f$Icons$2e$tsx__$5b$app$2d$client$5d$__$28$ecmascript$29$__["FactionIcon"], {
                    faction: factionKey,
                    className: "text-[1.2em]"
                }, void 0, false, {
                    fileName: "[project]/src/components/TopItemRow.tsx",
                    lineNumber: 47,
                    columnNumber: 21
                }, this)
            }, void 0, false, {
                fileName: "[project]/src/components/TopItemRow.tsx",
                lineNumber: 45,
                columnNumber: 17
            }, this) : /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                className: "w-8 h-8 flex items-center justify-center rounded-full   border border-border-terminal shrink-0 font-mono text-sm   font-bold text-text-secondary mr-1",
                children: [
                    "#",
                    rank
                ]
            }, void 0, true, {
                fileName: "[project]/src/components/TopItemRow.tsx",
                lineNumber: 50,
                columnNumber: 17
            }, this),
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                className: "flex flex-col min-w-0 flex-1",
                children: [
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                        className: "text-sm font-bold text-text-primary truncate",
                        children: name
                    }, void 0, false, {
                        fileName: "[project]/src/components/TopItemRow.tsx",
                        lineNumber: 59,
                        columnNumber: 17
                    }, this),
                    subvalue && /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                        className: "text-xs text-text-secondary font-mono",
                        children: subvalue
                    }, void 0, false, {
                        fileName: "[project]/src/components/TopItemRow.tsx",
                        lineNumber: 61,
                        columnNumber: 21
                    }, this)
                ]
            }, void 0, true, {
                fileName: "[project]/src/components/TopItemRow.tsx",
                lineNumber: 58,
                columnNumber: 13
            }, this),
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                className: "text-sm font-bold font-mono text-text-primary whitespace-nowrap ml-auto",
                children: value
            }, void 0, false, {
                fileName: "[project]/src/components/TopItemRow.tsx",
                lineNumber: 66,
                columnNumber: 13
            }, this)
        ]
    }, void 0, true, {
        fileName: "[project]/src/components/TopItemRow.tsx",
        lineNumber: 34,
        columnNumber: 9
    }, this);
}
_c = TopItemRow;
var _c;
__turbopack_context__.k.register(_c, "TopItemRow");
if (typeof globalThis.$RefreshHelpers$ === 'object' && globalThis.$RefreshHelpers !== null) {
    __turbopack_context__.k.registerExports(__turbopack_context__.m, globalThis.$RefreshHelpers$);
}
}),
"[project]/src/components/TopListRow.tsx [app-client] (ecmascript)", ((__turbopack_context__) => {
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
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/next/dist/compiled/react/jsx-dev-runtime.js [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$src$2f$lib$2f$factions$2e$ts__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/src/lib/factions.ts [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$src$2f$components$2f$Icons$2e$tsx__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/src/components/Icons.tsx [app-client] (ecmascript)");
;
;
;
function TopListRow(param) {
    let { list, value } = param;
    const color = (0, __TURBOPACK__imported__module__$5b$project$5d2f$src$2f$lib$2f$factions$2e$ts__$5b$app$2d$client$5d$__$28$ecmascript$29$__["getFactionColor"])(list.faction_key);
    var _FACTION_LABELS_list_faction_key;
    const factionLabel = (_FACTION_LABELS_list_faction_key = __TURBOPACK__imported__module__$5b$project$5d2f$src$2f$lib$2f$factions$2e$ts__$5b$app$2d$client$5d$__$28$ecmascript$29$__["FACTION_LABELS"][list.faction_key]) !== null && _FACTION_LABELS_list_faction_key !== void 0 ? _FACTION_LABELS_list_faction_key : list.faction;
    return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
        className: "flex flex-col gap-1 px-[14px] py-[10px] w-full border-b border-border-terminal   bg-[rgba(255,255,255,0.01)] hover:bg-[rgba(255,255,255,0.03)]   transition-colors cursor-default",
        children: [
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                className: "flex items-center gap-2 w-full",
                children: [
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$src$2f$components$2f$Icons$2e$tsx__$5b$app$2d$client$5d$__$28$ecmascript$29$__["FactionIcon"], {
                        faction: list.faction_key,
                        className: "text-[1.2em]"
                    }, void 0, false, {
                        fileName: "[project]/src/components/TopListRow.tsx",
                        lineNumber: 29,
                        columnNumber: 17
                    }, this),
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                        className: "text-xs text-text-secondary font-mono truncate",
                        children: factionLabel
                    }, void 0, false, {
                        fileName: "[project]/src/components/TopListRow.tsx",
                        lineNumber: 30,
                        columnNumber: 17
                    }, this),
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
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
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                className: "flex flex-col gap-0.5 pl-5",
                children: list.pilots.map((p, i)=>/*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                        className: "flex flex-col gap-0 py-[2px]",
                        children: [
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                className: "flex items-center gap-2 text-sm font-bold text-text-primary truncate",
                                children: [
                                    p.ship_icon && /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$src$2f$components$2f$Icons$2e$tsx__$5b$app$2d$client$5d$__$28$ecmascript$29$__["ShipIcon"], {
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
                            p.upgrades.length > 0 && /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                className: "flex flex-wrap gap-x-1.5 gap-y-0",
                                children: p.upgrades.map((u, j)=>/*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
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
_c = TopListRow;
var _c;
__turbopack_context__.k.register(_c, "TopListRow");
if (typeof globalThis.$RefreshHelpers$ === 'object' && globalThis.$RefreshHelpers !== null) {
    __turbopack_context__.k.registerExports(__turbopack_context__.m, globalThis.$RefreshHelpers$);
}
}),
"[project]/src/components/DashboardRankings.tsx [app-client] (ecmascript)", ((__turbopack_context__) => {
"use strict";

__turbopack_context__.s([
    "default",
    ()=>DashboardRankings
]);
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/next/dist/compiled/react/jsx-dev-runtime.js [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$src$2f$components$2f$RankingPanel$2e$tsx__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/src/components/RankingPanel.tsx [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$src$2f$components$2f$TopItemRow$2e$tsx__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/src/components/TopItemRow.tsx [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$src$2f$components$2f$TopListRow$2e$tsx__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/src/components/TopListRow.tsx [app-client] (ecmascript)");
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
function DashboardRankings(param) {
    let { lists, ships, pilots, upgrades } = param;
    return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
        className: "grid grid-cols-1 md:grid-cols-2 gap-4 w-full",
        children: [
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                className: "flex flex-col gap-6",
                children: [
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$src$2f$components$2f$RankingPanel$2e$tsx__$5b$app$2d$client$5d$__$28$ecmascript$29$__["default"], {
                        title: "TOP SQUAD LISTS",
                        children: (sort)=>{
                            const sorted = sortedLists(lists, sort);
                            return sorted.slice(0, 5).map((l, i)=>/*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$src$2f$components$2f$TopListRow$2e$tsx__$5b$app$2d$client$5d$__$28$ecmascript$29$__["default"], {
                                    list: l,
                                    value: sort === "win_rate" ? "".concat(l.win_rate, "%") : "".concat(l.count)
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
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$src$2f$components$2f$RankingPanel$2e$tsx__$5b$app$2d$client$5d$__$28$ecmascript$29$__["default"], {
                        title: "TOP CHASSIS",
                        children: (sort)=>{
                            const sorted = sortedBy(ships, sort);
                            return sorted.slice(0, 5).map((s, i)=>/*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$src$2f$components$2f$TopItemRow$2e$tsx__$5b$app$2d$client$5d$__$28$ecmascript$29$__["default"], {
                                    rank: i + 1,
                                    name: s.ship_name,
                                    value: "".concat(s.popularity, " Lists"),
                                    subvalue: "".concat(s.win_rate, "% WR"),
                                    isShip: true,
                                    shipXws: s.ship_xws
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
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                className: "flex flex-col gap-6",
                children: [
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$src$2f$components$2f$RankingPanel$2e$tsx__$5b$app$2d$client$5d$__$28$ecmascript$29$__["default"], {
                        title: "TOP PILOTS",
                        children: (sort)=>{
                            const sorted = sortedBy(pilots, sort);
                            return sorted.slice(0, 5).map((p, i)=>/*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$src$2f$components$2f$TopItemRow$2e$tsx__$5b$app$2d$client$5d$__$28$ecmascript$29$__["default"], {
                                    rank: i + 1,
                                    name: p.name,
                                    value: "".concat(p.popularity, " Lists"),
                                    subvalue: "".concat(p.win_rate, "% WR"),
                                    factionKey: p.faction
                                }, i, false, {
                                    fileName: "[project]/src/components/DashboardRankings.tsx",
                                    lineNumber: 95,
                                    columnNumber: 29
                                }, this));
                        }
                    }, void 0, false, {
                        fileName: "[project]/src/components/DashboardRankings.tsx",
                        lineNumber: 91,
                        columnNumber: 17
                    }, this),
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$src$2f$components$2f$RankingPanel$2e$tsx__$5b$app$2d$client$5d$__$28$ecmascript$29$__["default"], {
                        title: "TOP UPGRADES",
                        children: (sort)=>{
                            const sorted = sortedBy(upgrades, sort);
                            return sorted.slice(0, 5).map((u, i)=>/*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$src$2f$components$2f$TopItemRow$2e$tsx__$5b$app$2d$client$5d$__$28$ecmascript$29$__["default"], {
                                    rank: i + 1,
                                    name: u.name,
                                    value: "".concat(u.popularity, " Lists"),
                                    subvalue: "".concat(u.win_rate, "% WR")
                                }, i, false, {
                                    fileName: "[project]/src/components/DashboardRankings.tsx",
                                    lineNumber: 112,
                                    columnNumber: 29
                                }, this));
                        }
                    }, void 0, false, {
                        fileName: "[project]/src/components/DashboardRankings.tsx",
                        lineNumber: 108,
                        columnNumber: 17
                    }, this)
                ]
            }, void 0, true, {
                fileName: "[project]/src/components/DashboardRankings.tsx",
                lineNumber: 89,
                columnNumber: 13
            }, this)
        ]
    }, void 0, true, {
        fileName: "[project]/src/components/DashboardRankings.tsx",
        lineNumber: 48,
        columnNumber: 9
    }, this);
}
_c = DashboardRankings;
var _c;
__turbopack_context__.k.register(_c, "DashboardRankings");
if (typeof globalThis.$RefreshHelpers$ === 'object' && globalThis.$RefreshHelpers !== null) {
    __turbopack_context__.k.registerExports(__turbopack_context__.m, globalThis.$RefreshHelpers$);
}
}),
]);

//# sourceMappingURL=src_90d788c3._.js.map