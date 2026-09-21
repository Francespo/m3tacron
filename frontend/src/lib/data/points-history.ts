/**
 * Star Wars: X-Wing Points Change History & Constants
 *
 * Data is dynamically synchronized from `external_data/points_history`
 * (Francespo/xwing-unified-data) by scripts/generate-xwing-data.js.
 */

import pointsHistoryJson from './points-history.json';

export interface PointsUpdate {
    date: string;
    version: string;
    name?: string;
    description: string;
    highlights?: string[];
}

export interface PointsHistoryData {
    system: string;
    name: string;
    default_format: string;
    description?: string;
    official_url?: string;
    points_url?: string;
    latest_date: string;
    updates: PointsUpdate[];
}

export const POINTS_HISTORY: Record<string, PointsHistoryData> = (pointsHistoryJson as any) || {};

/**
 * Normalize system or format string to one of the 4 key stewardship systems.
 */
export function normalizeSystem(systemOrFormat: string | null | undefined): string {
    const s = (systemOrFormat || '').trim().toLowerCase();
    if (s.includes('legacy') || s === 'x2po' || s.startsWith('legacy_')) return 'legacy';
    if (s === 'xwa' || s === 'amg_50p') return 'xwa';
    if (s === 'amg' || s === '2.5') return 'amg';
    if (s === 'ffg' || s === '2.0') return 'ffg';
    return s || 'xwa';
}

/**
 * Get the latest points change date for the given system or dataSource.
 * Legacy -> 2026-03-31
 * XWA -> 2026-08-16
 * AMG -> 2024-09-06
 * FFG -> 2020-11-24
 */
export function getLatestPointsDate(systemOrFormat: string | null | undefined): string {
    const sys = normalizeSystem(systemOrFormat);
    return POINTS_HISTORY[sys]?.latest_date ?? (sys === 'legacy' ? '2026-03-31' : '2026-08-16');
}

/**
 * Get the most recent PointsUpdate object for the given system or dataSource.
 */
export function getLatestPointsUpdate(systemOrFormat: string | null | undefined): PointsUpdate | null {
    const sys = normalizeSystem(systemOrFormat);
    const updates = POINTS_HISTORY[sys]?.updates;
    return updates && updates.length > 0 ? updates[0] : null;
}

/**
 * Get the complete points history data record for the given system.
 */
export function getPointsHistory(systemOrFormat: string | null | undefined): PointsHistoryData | null {
    const sys = normalizeSystem(systemOrFormat);
    return POINTS_HISTORY[sys] || null;
}

export interface PointsEra {
    id: string;
    name: string;
    version: string;
    system: 'xwa' | 'amg' | 'legacy' | 'ffg';
    systemLabel: string;
    startDate: string;
    endDate: string; // empty string '' if latest / ongoing
    label: string;
    isLatest: boolean;
    description?: string;
}

export interface PointsEraGroup {
    system: 'xwa' | 'amg' | 'legacy' | 'ffg';
    systemLabel: string;
    eras: PointsEra[];
}

const SYSTEM_LABELS: Record<string, string> = {
    xwa: 'XWA (50P)',
    amg: 'AMG (2.5)',
    legacy: 'Legacy (X2PO 2.0)',
    ffg: 'FFG (Second Edition 2.0)',
};

function getDayBefore(isoDate: string): string {
    const d = new Date(isoDate + 'T00:00:00Z');
    d.setUTCDate(d.getUTCDate() - 1);
    return d.toISOString().slice(0, 10);
}

/**
 * Determine the systems in chronological lineage for a format / dataSource.
 * - Legacy includes Legacy updates (2022–present) + FFG updates (2018–2020)
 * - XWA includes XWA updates (2024–present) + AMG updates (2022–2024)
 * - Explicit single-format selections (ffg only, amg only) restrict to that system.
 */
export function getLineageSystems(
    systemOrDataSource: string | null | undefined,
    selectedFormats?: string[],
): ('xwa' | 'amg' | 'legacy' | 'ffg')[] {
    if (selectedFormats && selectedFormats.length > 0) {
        const unique = new Set(selectedFormats.map((f) => f.toLowerCase()));
        if (unique.size === 1 && unique.has('ffg')) return ['ffg'];
        if (unique.size === 1 && unique.has('amg')) return ['amg'];
        if (selectedFormats.some((f) => f.startsWith('legacy_') || f === 'legacy')) {
            return ['legacy', 'ffg'];
        }
        if (selectedFormats.some((f) => f === 'xwa' || f === 'amg_50p')) {
            return ['xwa', 'amg'];
        }
    }

    const sys = normalizeSystem(systemOrDataSource);
    if (sys === 'legacy' || sys === 'ffg') {
        return ['legacy', 'ffg'];
    }
    return ['xwa', 'amg'];
}

/**
 * Compute organized points eras grouped by system for dropdown and quick-selector usage.
 */
export function getPointsEraGroups(
    systemOrDataSource: string | null | undefined,
    selectedFormats?: string[],
): PointsEraGroup[] {
    const systems = getLineageSystems(systemOrDataSource, selectedFormats);
    const groups: PointsEraGroup[] = [];

    for (let sIdx = 0; sIdx < systems.length; sIdx++) {
        const sys = systems[sIdx];
        const sysData = POINTS_HISTORY[sys];
        if (!sysData || !sysData.updates || sysData.updates.length === 0) continue;

        const updates = [...sysData.updates].sort((a, b) => b.date.localeCompare(a.date));
        const nextSystemNewerDate = sIdx > 0 ? POINTS_HISTORY[systems[0]]?.updates?.slice(-1)[0]?.date : undefined;

        const eras: PointsEra[] = updates.map((u, i) => {
            const isLatest = sIdx === 0 && i === 0;
            const startDate = u.date;
            let endDate = '';

            if (i > 0) {
                endDate = getDayBefore(updates[i - 1].date);
            } else if (nextSystemNewerDate) {
                endDate = getDayBefore(nextSystemNewerDate);
            }

            if (endDate && endDate < startDate) {
                endDate = '';
            }

            const label = isLatest
                ? `${u.name || u.version} (Since ${startDate})`
                : endDate
                  ? `${u.name || u.version} (${startDate} to ${endDate})`
                  : `${u.name || u.version} (From ${startDate})`;

            return {
                id: `${sys}-${startDate}`,
                name: u.name || u.version,
                version: u.version,
                system: sys,
                systemLabel: SYSTEM_LABELS[sys] || sys.toUpperCase(),
                startDate,
                endDate,
                label,
                isLatest,
                description: u.description,
            };
        });

        groups.push({
            system: sys,
            systemLabel: SYSTEM_LABELS[sys] || sys.toUpperCase(),
            eras,
        });
    }

    return groups;
}

/**
 * Get a flat list of all eras in lineage order (newest to oldest).
 */
export function getAllPointsEras(
    systemOrDataSource: string | null | undefined,
    selectedFormats?: string[],
): PointsEra[] {
    return getPointsEraGroups(systemOrDataSource, selectedFormats).flatMap((g) => g.eras);
}

