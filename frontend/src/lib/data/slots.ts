
export const SLOT_ICONS: Record<string, string> = {
    talent: 'E',
    forcepower: 'F',
    system: 'S',
    cannon: 'C',
    turret: 'U',
    torpedo: 'P',
    missile: 'M',
    bomb: 'B', // or device?
    astromech: 'A',
    illicit: 'I',
    tech: 'X',
    modification: 'm',
    title: 't',
    gunner: 'G',
    crew: 'W',
    device: 'B',
    configuration: 'n',
    tacticalrelay: 'Z',
    command: 'D',
    hardpoint: 'H',
    team: 'T',
    cargo: 'G',
    sensor: 'S' // legacy 1.0?
};

export function getSlotIcon(slot: string): string {
    return SLOT_ICONS[slot.toLowerCase().replace(/[^a-z]/g, '')] || '';
}
