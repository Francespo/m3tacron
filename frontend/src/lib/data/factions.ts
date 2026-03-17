/**
 * Faction data constants.
 * Mirrors Reflex theme.py FACTION_COLORS, FACTION_ICONS, and factions.py FACTION_CHARS.
 */

export const FACTION_COLORS: Record<string, string> = {
    rebelalliance: '#FF3333',
    galacticempire: '#2979FF',
    scumandvillainy: '#006400',
    resistance: '#FF8C00',
    firstorder: '#800020',
    galacticrepublic: '#E6D690',
    separatistalliance: '#607D8B',
    unknown: '#666666'
};

/** X-Wing Miniatures Font characters for faction icons. */
export const FACTION_CHARS: Record<string, string> = {
    rebelalliance: '!',
    galacticempire: '@',
    scumandvillainy: '#',
    resistance: '!',
    firstorder: '+',
    galacticrepublic: '/',
    separatistalliance: '.',
    unknown: '?'
};

export const FACTION_LABELS: Record<string, string> = {
    rebelalliance: 'Rebel Alliance',
    galacticempire: 'Galactic Empire',
    scumandvillainy: 'Scum and Villainy',
    resistance: 'Resistance',
    firstorder: 'First Order',
    galacticrepublic: 'Galactic Republic',
    separatistalliance: 'Separatist Alliance',
    unknown: 'Unknown'
};

export const ALL_FACTIONS = Object.keys(FACTION_COLORS).filter(f => f !== 'unknown');

export function getFactionColor(factionXws: string): string {
    return FACTION_COLORS[factionXws] ?? FACTION_COLORS.unknown;
}

export function getFactionChar(factionXws: string): string {
    return FACTION_CHARS[factionXws] ?? '?';
}

export function getFactionLabel(factionXws: string): string {
    return FACTION_LABELS[factionXws] ?? factionXws;
}

/**
 * Returns a CSS color for a win rate value (continuous gradient).
 * 0% → red, 50% → yellow, 100% → green.
 */
export function getWinRateColor(wr: number): string {
    if (wr >= 60) return '#22c55e'; // green-500
    if (wr >= 50) return '#84cc16'; // lime-500
    if (wr >= 40) return '#eab308'; // yellow-500
    if (wr >= 30) return '#f97316'; // orange-500
    return '#ef4444'; // red-500
}
/**
 * Returns the CSS class for a faction icon in xwing-miniatures-font.
 */
export function getFactionIconClass(factionXws: string): string {
    return factionXws.replace(/[^a-z0-9]/g, '');
}

/**
 * Returns the CSS class for a ship icon in xwing-miniatures-ship font.
 */
export function getShipIconClass(shipXws: string): string {
    if (!shipXws) return '';
    return 'xwing-miniatures-ship-' + shipXws.replace(/[^a-z0-9]/g, '');
}

/**
 * Returns the CSS class for an upgrade icon in xwing-miniatures-font.
 */
export function getUpgradeIconClass(upgradeType: string): string {
    if (!upgradeType) return '';
    const type = upgradeType.toLowerCase().replace(/[^a-z0-9]/g, '');
    return 'xwing-miniatures-font-' + type;
}
