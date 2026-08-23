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
    legacy_pandorum: 'PAND',
    other: 'UNK'
};

export const FORMAT_FULL_LABELS: Record<string, string> = {
    amg: 'AMG',
    xwa: 'XWA',
    ffg: 'FFG',
    legacy_x2po: 'Legacy X2PO',
    legacy_xlc: 'Legacy XLC',
    legacy_pandorum: 'Legacy Pandorum',
    other: 'Unknown'
};

export const FORMAT_COLORS: Record<string, string> = {
    // 2.5 — keep AMG cyan, warm up XWA to amber/gold (pairs with Champion amber)
    amg: '#22d3ee',         // Cyan 400 — current-era, premium
    xwa: '#f59e0b',         // Amber 500 — community XWA, warm

    // 2.0 — separate FFG legacy distinctly
    ffg: '#6366f1',         // Indigo 500 — 1.0 era
    legacy_x2po: '#8b5cf6', // Violet 500 — X2PO
    legacy_xlc: '#ec4899',  // Rose 500 — XLC (playful, avoids faction greens/blues)
    legacy_pandorum: '#a78bfa', // Violet 300 — Pandorum, lighter

    // Unknown / Other
    other: '#475569'         // Slate 600
};

export function getFormatLabel(formatXws: string): string {
    return FORMAT_LABELS[formatXws] ?? formatXws.toUpperCase();
}

export function getFormatFullLabel(formatXws: string): string {
    return FORMAT_FULL_LABELS[formatXws] ?? getFormatLabel(formatXws);
}

export function getFormatColor(formatXws: string): string {
    return FORMAT_COLORS[formatXws] ?? FORMAT_COLORS.other;
}

export function getMacroFormat(formatXws: string): string {
    if (['amg', 'xwa'].includes(formatXws)) return '2.5';
    if (['ffg', 'legacy_x2po', 'legacy_xlc', 'legacy_pandorum'].includes(formatXws)) return '2.0';
    return '';
}

/**
 * Infer display format for legacy tournaments where the stored
 * `format` is `unknown`. Pre-2021 AMG/XWA tournaments are frequently
 * stored as `unknown` due to missing ListFortress/Rollbetter format IDs,
 * but the rule system at the time was exclusively FFG (2.0).
 *
 * For detail pages and chips that have access to the tournament date,
 * pass `dateStr` (YYYY-MM-DD) to recover the correct era label.
 *
 * Behaviour:
 *  - If `formatXws` is not `unknown` / `other` / falsy, return as-is.
 *  - If `formatXws` is unknown and the date is before 2021-01-01, infer `ffg`.
 *  - Otherwise return the original value (caller shows "Unknown").
 */
export function resolveDisplayFormat(
    formatXws: string | null | undefined,
    dateStr?: string | null,
): string {
    const raw = (formatXws ?? '').toLowerCase().trim();
    if (raw && raw !== 'unknown' && raw !== 'other') return raw;
    if (dateStr) {
        // Lexicographic comparison is safe for YYYY-MM-DD
        if (dateStr < '2021-01-01') return 'ffg';
    }
    return raw || 'unknown';
}

export function getDisplayFormatLabel(
    formatXws: string | null | undefined,
    dateStr?: string | null,
): string {
    return getFormatLabel(resolveDisplayFormat(formatXws, dateStr));
}

export function getDisplayFormatFullLabel(
    formatXws: string | null | undefined,
    dateStr?: string | null,
): string {
    return getFormatFullLabel(resolveDisplayFormat(formatXws, dateStr));
}
