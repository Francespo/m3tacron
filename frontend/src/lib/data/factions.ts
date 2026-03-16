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
    unknown: 'Unknown Faction'
};

export const FACTION_ICON_CLASSES: Record<string, string> = {
    rebelalliance: 'xwing-miniatures-font-rebel',
    galacticempire: 'xwing-miniatures-font-empire',
    scumandvillainy: 'xwing-miniatures-font-scum',
    resistance: 'xwing-miniatures-font-resistance',
    firstorder: 'xwing-miniatures-font-firstorder',
    galacticrepublic: 'xwing-miniatures-font-republic',
    separatistalliance: 'xwing-miniatures-font-separatists',
    unknown: ''
};

export const ALL_FACTIONS = Object.keys(FACTION_COLORS).filter(f => f !== 'unknown');

export function getFactionColor(xws: string): string {
    return FACTION_COLORS[xws] || FACTION_COLORS.unknown;
}

export function getFactionChar(xws: string): string {
    return FACTION_CHARS[xws] || FACTION_CHARS.unknown;
}

export function getFactionLabel(xws: string): string {
    return FACTION_LABELS[xws] || FACTION_LABELS.unknown;
}

export function getFactionIconClass(xws: string): string {
    const sanitized = (xws || '').toLowerCase().replace(/[^a-z0-9]/g, '');
    return FACTION_ICON_CLASSES[sanitized] || '';
}

export function getShipIconClass(xws: string): string {
    if (!xws) return '';
    return 'xwing-miniatures-ship-' + xws.toLowerCase().replace(/[^a-z0-9]/g, '');
}

export function getUpgradeIconClass(type: string): string {
    if (!type) return '';
    return 'xwing-miniatures-font-' + type.toLowerCase().replace(/[^a-z0-9]/g, '');
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
