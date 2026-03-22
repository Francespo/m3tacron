export const SOURCE_LABELS: Record<string, string> = {
    listfortress: 'ListFortress',
    longshanks: 'Longshanks',
    rollbetter: 'Rollbetter',
    unknown: 'Unknown'
};

export function getSourceLabel(source: string): string {
    return SOURCE_LABELS[source.toLowerCase()] ?? source;
}
