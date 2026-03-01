import { getFactionColor } from "@/lib/factions";

const FACTION_ICONS: Record<string, string> = {
    rebelalliance: "xwing-miniatures-font-rebel",
    galacticempire: "xwing-miniatures-font-empire",
    scumandvillainy: "xwing-miniatures-font-scum",
    resistance: "xwing-miniatures-font-rebel",
    firstorder: "xwing-miniatures-font-firstorder",
    galacticrepublic: "xwing-miniatures-font-republic",
    separatistalliance: "xwing-miniatures-font-separatists",
};

export function FactionIcon({ faction, factionXws, className = "" }: { faction?: string; factionXws?: string; className?: string }) {
    const key = faction || factionXws || "";
    const iconClass = FACTION_ICONS[key] ?? "";
    const color = getFactionColor(key);

    if (!iconClass) return null;

    return (
        <i
            className={`xwing-miniatures-font ${iconClass} ${className}`}
            style={{ color, fontStyle: "normal" }}
        />
    );
}

export function UpgradeIcon({ slot, className = "" }: { slot: string; className?: string }) {
    if (!slot) return null;

    // Normalize slot for icon name
    const iconClass = `xwing-miniatures-font-${slot.toLowerCase().replace(/ /g, '')}`;

    return (
        <i
            className={`xwing-miniatures-font ${iconClass} ${className}`}
            style={{ fontStyle: "normal" }}
        />
    );
}

export function ShipIcon({ xws, className = "", style }: { xws: string; className?: string; style?: React.CSSProperties }) {
    if (!xws) return null;

    // Normalize XWS for icons (e.g. tieininterceptor -> tieinterceptor)
    let cleanName = xws.toLowerCase().replace("xwing-miniatures-ship-", "");
    if (cleanName === "tieininterceptor") {
        cleanName = "tieinterceptor";
    }

    return (
        <i
            className={`xwing-miniatures-ship xwing-miniatures-ship-${cleanName} ${className}`}
            style={{ fontStyle: "normal" }}
        />
    );
}
