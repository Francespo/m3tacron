/**
 * Faction color mapping.
 *
 * Matches FACTION_COLORS from m3tacron/theme.py exactly.
 */

export const FACTION_COLORS: Record<string, string> = {
    rebelalliance: "#FF3333",
    galacticempire: "#2979FF",
    scumandvillainy: "#006400",
    resistance: "#FF8C00",
    firstorder: "#800020",
    galacticrepublic: "#E6D690",
    separatistalliance: "#607D8B",
    unknown: "#666666",
};

/** Resolve a faction key to its HEX color. Falls back to grey. */
export function getFactionColor(factionKey: string): string {
    return FACTION_COLORS[factionKey] ?? FACTION_COLORS.unknown;
}

/** Faction human-readable labels. */
export const FACTION_LABELS: Record<string, string> = {
    rebelalliance: "Rebel Alliance",
    galacticempire: "Galactic Empire",
    scumandvillainy: "Scum & Villainy",
    resistance: "Resistance",
    firstorder: "First Order",
    galacticrepublic: "Galactic Republic",
    separatistalliance: "Separatist Alliance",
    unknown: "Unknown",
};
