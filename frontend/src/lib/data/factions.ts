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

const FACTION_ALIASES: Record<string, string> = {
    rebel: 'rebelalliance',
    empire: 'galacticempire',
    scum: 'scumandvillainy',
    resistance: 'resistance',
    firstorder: 'firstorder',
    republic: 'galacticrepublic',
    separatist: 'separatistalliance'
};

function coerceFactionValue(value: unknown): string {
    return String(value ?? '').trim();
}

export function normalizeFactionKey(value: unknown): string {
    const normalized = coerceFactionValue(value).toLowerCase().replace(/[^a-z0-9]/g, '');
    if (!normalized) return 'unknown';
    if (normalized in FACTION_COLORS) return normalized;

    for (const [alias, faction] of Object.entries(FACTION_ALIASES)) {
        if (normalized === alias || normalized.includes(alias)) {
            return faction;
        }
    }

    return 'unknown';
}

export function getFactionColor(factionXws: unknown): string {
    const key = normalizeFactionKey(factionXws);
    return FACTION_COLORS[key] ?? FACTION_COLORS.unknown;
}

export function getFactionChar(factionXws: unknown): string {
    const key = normalizeFactionKey(factionXws);
    return FACTION_CHARS[key] ?? FACTION_CHARS.unknown;
}

export function getFactionLabel(factionXws: unknown): string {
    const key = normalizeFactionKey(factionXws);
    return FACTION_LABELS[key] ?? (coerceFactionValue(factionXws) || FACTION_LABELS.unknown);
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
