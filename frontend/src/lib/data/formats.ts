/**
 * Format data constants.
 * Maps backend Format enum values to frontend display labels.
 */

export const FORMAT_LABELS: Record<string, string> = {
    amg: 'AMG',
    xwa: 'XWA',
    ffg: 'FFG',
    legacy_x2po: 'X2PO',
    legacy_xlc: 'XLC',
    other: 'UNK'
};

export const FORMAT_COLORS: Record<string, string> = {
    // Macro 2.5 (Cyan shades)
    amg: '#22d3ee',         // Cyan 400
    xwa: '#0891b2',         // Cyan 600

    // Macro 2.0 (Purple/Violet shades)
    ffg: '#a855f7',         // Purple 500
    legacy_x2po: '#7c3aed', // Violet 600
    legacy_xlc: '#6d28d9',  // Violet 700

    // Low importance/Non-stats
    other: '#475569'         // Slate 600 (Gisio/Dead)
};

export function getFormatLabel(formatXws: string): string {
    return FORMAT_LABELS[formatXws] ?? formatXws.toUpperCase();
}

export function getFormatColor(formatXws: string): string {
    return FORMAT_COLORS[formatXws] ?? FORMAT_COLORS.other;
}

export function getMacroFormat(formatXws: string): string {
    if (['amg', 'xwa'].includes(formatXws)) return '2.5';
    if (['ffg', 'legacy_x2po', 'legacy_xlc'].includes(formatXws)) return '2.0';
    return '';
}
