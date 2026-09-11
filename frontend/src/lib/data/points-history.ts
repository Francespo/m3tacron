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
