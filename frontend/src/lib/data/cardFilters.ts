/**
 * Option lists for the cards-page advanced filter multi-selects.
 *
 * Derived from the xwing-data2 dataset (external_data/xwing-data2 in the
 * backend repo — see backend/analytics/core.py for the authoritative filter
 * logic). The dataset is static, so these lists are hardcoded rather than
 * fetched; selecting an option that has no cards in the current mode simply
 * yields zero results.
 */

/** Upgrade slots that appear on pilots and upgrades. */
export const CARD_SLOT_TYPES = [
    'Astromech',
    'Cannon',
    'Cargo',
    'Command',
    'Configuration',
    'Crew',
    'Device',
    'Force Power',
    'Gunner',
    'Hardpoint',
    'Hyperdrive',
    'Illicit',
    'Missile',
    'Modification',
    'Sensor',
    'Tactical Relay',
    'Talent',
    'Team',
    'Tech',
    'Title',
    'Torpedo',
    'Turret',
];

/** Pilot keywords (XWA dataset). */
export const PILOT_KEYWORDS = [
    'A-wing',
    'B-wing',
    'Bounty Hunter',
    'Clone',
    'Dark Side',
    'Droid',
    'Freighter',
    'Jedi',
    'Light Side',
    'Mandalorian',
    'Partisan',
    'Sith',
    'Spectre',
    'TIE',
    'X-wing',
    'Y-wing',
    'YT-1300',
];

/** Ship/pilot action types. */
export const PILOT_ACTIONS = [
    'Barrel Roll',
    'Boost',
    'Calculate',
    'Cloak',
    'Coordinate',
    'Evade',
    'Focus',
    'Jam',
    'Lock',
    'Reinforce',
    'Reload',
    'Rotate Arc',
    'SLAM',
];

/** Linked-action types (actions granted as a linked action). */
export const PILOT_LINKED_ACTIONS = [
    'Barrel Roll',
    'Boost',
    'Calculate',
    'Evade',
    'Focus',
    'Lock',
    'Reload',
    'Rotate Arc',
];

/** Attack arc icons found on ships. */
export const PILOT_ARC_ICONS = [
    'Front Arc',
    'Full Front Arc',
    'Rear Arc',
    'Left Arc',
    'Right Arc',
    'Single Turret Arc',
    'Double Turret Arc',
    'Bullseye Arc',
];
