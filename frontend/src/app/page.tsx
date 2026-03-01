/**
 * Home page — Meta Snapshot Dashboard.
 *
 * React Server Component. Fetches data from FastAPI at request time
 * and renders:
 * 1. Hero section (title, sync badge, date range)
 * 2. Stat cards row (tournaments, players, factions)
 * 3. Rankings grid (lists, ships, pilots, upgrades) — client-side for sorting
 */

import { fetchMetaSnapshot } from "@/lib/api";
import MetaStatCard from "@/components/MetaStatCard";
import DashboardRankings from "@/components/DashboardRankings";

export default async function HomePage(props: { searchParams?: Promise<{ [key: string]: string | string[] | undefined }> }) {
    const searchParams = props.searchParams ? await props.searchParams : {};
    const source = (searchParams?.source as "xwa" | "legacy") || "xwa";

    let snapshot;

    try {
        snapshot = await fetchMetaSnapshot(source as "xwa" | "legacy");
    } catch {
        // Graceful fallback when backend is unavailable
        return (
            <main className="flex items-center justify-center min-h-screen px-4">
                <div className="panel text-center max-w-md">
                    <h1 className="text-2xl font-bold font-sans mb-2">M3TACRON</h1>
                    <p className="text-text-secondary text-sm font-mono">
                        Backend non raggiungibile su <code>127.0.0.1:8000</code>.
                        <br />
                        Avvia il server FastAPI e ricarica.
                    </p>
                </div>
            </main>
        );
    }

    return (
        <main className="w-full max-w-[1400px] mx-auto px-4 sm:px-6 md:px-8 lg:px-10 py-8 pb-32">
            {/* ── Hero Section ────────────────────────────────────── */}
            <section className="flex flex-col md:flex-row md:items-end gap-4 pb-10 w-full">
                <div className="flex flex-col gap-2">
                    <h1 className="text-3xl sm:text-5xl md:text-7xl font-medium font-sans tracking-[0.08em] text-text-primary">
                        META SNAPSHOT
                    </h1>
                    <div className="flex items-center gap-2 flex-wrap mt-2">
                        <span className="px-2 py-0.5 text-xs font-mono bg-border-terminal rounded text-text-secondary">
                            {snapshot.last_sync}
                        </span>
                        <span className="text-xs text-text-secondary font-mono">
                            RANGE: {snapshot.date_range}
                        </span>
                    </div>
                </div>
            </section>

            {/* ── Stat Cards ──────────────────────────────────────── */}
            <section className="grid grid-cols-1 md:grid-cols-3 gap-4 w-full mb-8">
                <MetaStatCard
                    label="RECENT TOURNAMENTS"
                    value={snapshot.total_tournaments}
                    subtext="Last 90 Days"
                />
                <MetaStatCard
                    label="RECENT LISTS"
                    value={snapshot.total_players}
                    subtext="Last 90 Days"
                />
                <MetaStatCard
                    label="ACTIVE FACTIONS"
                    value={7}
                />
            </section>

            {/* ── Rankings Grid ───────────────────────────────────── */}
            <section className="w-full">
                <DashboardRankings
                    lists={snapshot.lists}
                    ships={snapshot.ships}
                    pilots={snapshot.pilots}
                    upgrades={snapshot.upgrades}
                />
            </section>
        </main>
    );
}
