/**
 * MetaStatCard — a dark-bordered metric card.
 *
 * Server Component. Renders label, value, and optional subtext
 * inside a terminal-style panel.
 */

interface MetaStatCardProps {
    label: string;
    value: string | number;
    subtext?: string;
}

export default function MetaStatCard({ label, value, subtext }: MetaStatCardProps) {
    return (
        <div className="panel flex flex-col gap-1">
            <span className="text-xs font-bold tracking-wider text-text-secondary font-mono uppercase">
                {label}
            </span>
            <span className="text-3xl font-bold text-text-primary font-sans">
                {value}
            </span>
            {subtext && (
                <span className="text-xs text-text-secondary font-mono">{subtext}</span>
            )}
        </div>
    );
}
