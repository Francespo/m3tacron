"""
Bulk precompute of all pilot/upgrade detail stats.

Rationale (per project owner): the in-memory cache is already invalidated
when the scraper bumps `scrape_meta.data_version`, but detail pages were only
warmed lazily (first user pays the cold GROUP BY per card). Instead, we
compute a single snapshot covering ALL pilots and ALL upgrades in a handful
of SQL passes, cache it under `card_detail_snapshot|<ds>`, and have detail
endpoints read from it (filtered by format in Python). Cost is paid once per
data_version (scrape), not per user visit.

Snapshot shape (all values pre-aggregated):

  pilot_upgrades: {fmt: {pilot_xws: {upg_xws: {lists, games, wins}}}}
  upgrade_pilots: {fmt: {upg_xws: {pilot_xws: {lists, games, wins}}}}
  pilot_chart:    {fmt: {pilot_xws: {YYYY-MM: games}}}
  upgrade_chart:  {fmt: {upg_xws: {YYYY-MM: games}}}
  pilot_configs:  {fmt: {pilot_xws: {combo_key: {upg_ids, lists, games, wins, count}}}}
  header:         {pilot_xws: {squadron_count, list_count, different_lists_count,
                                entries_count, games_count, wins}}
"""
from collections import defaultdict
from sqlmodel import Session
from sqlalchemy import text

from ..cache import get_cached_or_compute
from ..database import engine
from ..data_structures.data_source import DataSource


def _safe_games(swiss_wins, swiss_losses, swiss_draws, cut_wins, cut_losses, cut_draws):
    return (
        max(0, swiss_wins or 0) + max(0, swiss_losses or 0) + max(0, swiss_draws or 0)
        + max(0, cut_wins or 0) + max(0, cut_losses or 0) + max(0, cut_draws or 0)
    )


def _fmt_of(fmt):
    return fmt or "unknown"


def build_snapshot(ds: DataSource) -> dict:
    """Compute the full card-detail snapshot for a data source in a few SQL passes."""
    fmt_key = "xwa" if ds == DataSource.XWA else "legacy"

    pilot_upgrades: dict = defaultdict(lambda: defaultdict(dict))
    upgrade_pilots: dict = defaultdict(lambda: defaultdict(dict))
    pilot_chart: dict = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
    upgrade_chart: dict = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
    pilot_configs: dict = defaultdict(lambda: defaultdict(dict))

    with Session(engine) as session:
        # ---- Pass 1: per (pilot, upgrade) game/lists/wins + month buckets + config combos.
        # Unnest pilots -> upgrades, keep format + month for chart buckets and
        # pilot id for config grouping. One scan of the joined tables.
        sql = text("""
            WITH pilot_data AS (
                SELECT
                    ps.id AS ps_id,
                    l.ship_list,
                    l.list_json,
                    ps.swiss_wins, ps.swiss_losses, ps.swiss_draws,
                    ps.cut_wins, ps.cut_losses, ps.cut_draws,
                    p,
                    t.format,
                    to_char(t.date, 'YYYY-MM') AS month
                FROM playerstanding ps
                JOIN tournament t ON t.id = ps.tournament_id
                JOIN list l ON l.id = ps.list_id
                JOIN jsonb_array_elements(l.list_json::jsonb->'pilots') p ON true
                WHERE (NOT t.is_team_event OR ps.is_team_member)
            ),
            upgrade_values AS (
                SELECT
                    ps_id, ship_list, list_json,
                    swiss_wins, swiss_losses, swiss_draws,
                    cut_wins, cut_losses, cut_draws,
                    p->>'id' AS pilot_xws,
                    month, format,
                    CASE
                        WHEN jsonb_typeof(p->'upgrades') = 'array' THEN p->'upgrades'
                        WHEN jsonb_typeof(p->'upgrades') = 'object' THEN
                            COALESCE(
                                (SELECT jsonb_agg(v)
                                 FROM jsonb_each(p->'upgrades') e,
                                      jsonb_array_elements_text(e.value) v
                                 WHERE jsonb_typeof(e.value) = 'array'),
                                '[]'::jsonb
                            )
                        ELSE '[]'::jsonb
                    END AS upgrades_json
                FROM pilot_data
            )
            SELECT
                pilot_xws,
                u_elem AS upgrade_xws,
                format,
                month,
                GREATEST(0, COALESCE(swiss_wins,0)) + GREATEST(0, COALESCE(swiss_losses,0))
                    + GREATEST(0, COALESCE(swiss_draws,0)) + GREATEST(0, COALESCE(cut_wins,0))
                    + GREATEST(0, COALESCE(cut_losses,0)) + GREATEST(0, COALESCE(cut_draws,0)) AS games,
                GREATEST(0, COALESCE(swiss_wins,0)) + GREATEST(0, COALESCE(cut_wins,0)) AS wins
            FROM upgrade_values, jsonb_array_elements_text(upgrades_json) u_elem
            WHERE u_elem IS NOT NULL
        """)
        rows = session.execute(sql).fetchall()

        # ---- Pass 1c: per-pilot chart data (INCLUDES pilots with no upgrades,
        # e.g. standard-loadout / horizontal quickbuild cards). One scan grouped
        # by (pilot, format, month). Kept separate so upgrade-unnest drops never
        # lose chart rows for upgrade-less pilots.
        sql_chart = text("""
            SELECT
                p->>'id' AS pilot_xws,
                t.format,
                to_char(t.date, 'YYYY-MM') AS month,
                SUM(GREATEST(0, COALESCE(ps.swiss_wins,0)) + GREATEST(0, COALESCE(ps.swiss_losses,0))
                    + GREATEST(0, COALESCE(ps.swiss_draws,0)) + GREATEST(0, COALESCE(ps.cut_wins,0))
                    + GREATEST(0, COALESCE(ps.cut_losses,0)) + GREATEST(0, COALESCE(ps.cut_draws,0))) AS games
            FROM playerstanding ps
            JOIN tournament t ON t.id = ps.tournament_id
            JOIN list l ON l.id = ps.list_id
            JOIN jsonb_array_elements(l.list_json::jsonb->'pilots') p ON true
            WHERE (NOT t.is_team_event OR ps.is_team_member)
            GROUP BY p->>'id', t.format, to_char(t.date, 'YYYY-MM')
        """)
        chart_rows = session.execute(sql_chart).fetchall()

    # Pass 1a: pilot->upgrade + upgrade->pilot + charts (from dedicated chart pass).
    for pilot_xws, fmt, month, games in chart_rows:
        f = _fmt_of(fmt)
        pilot_chart[f][pilot_xws][month or "unknown"] += int(games or 0)

    for pilot_xws, upg_xws, fmt, month, games, wins in rows:
        f = _fmt_of(fmt)
        games = int(games or 0)
        wins = int(wins or 0)
        has_game = games > 0

        # pilot->upgrade stats
        pu = pilot_upgrades[f][pilot_xws].setdefault(upg_xws, {"lists": 0, "games": 0, "wins": 0})
        pu["games"] += games
        pu["wins"] += wins
        if has_game:
            pu["lists"] += 1

        # upgrade->pilot stats
        up = upgrade_pilots[f][upg_xws].setdefault(pilot_xws, {"lists": 0, "games": 0, "wins": 0})
        up["games"] += games
        up["wins"] += wins
        if has_game:
            up["lists"] += 1

        # upgrade chart (only upgrade carriers — upgrades have no chart without rows)
        upgrade_chart[f][upg_xws][month or "unknown"] += games

    # Pass 1b: pilot config combos — separate GROUP BY over the full list (pilot->combo).
    with Session(engine) as session:
        sql2 = text("""
            WITH pilot_data AS (
                SELECT
                    ps.id AS ps_id,
                    ps.swiss_wins, ps.swiss_losses, ps.swiss_draws,
                    ps.cut_wins, ps.cut_losses, ps.cut_draws,
                    p, t.format
                FROM playerstanding ps
                JOIN tournament t ON t.id = ps.tournament_id
                JOIN list l ON l.id = ps.list_id
                JOIN jsonb_array_elements(l.list_json::jsonb->'pilots') p ON true
                WHERE (NOT t.is_team_event OR ps.is_team_member)
            ),
            upg AS (
                SELECT
                    ps_id,
                    swiss_wins, swiss_losses, swiss_draws,
                    cut_wins, cut_losses, cut_draws,
                    p->>'id' AS pilot_xws,
                    format,
                    CASE
                        WHEN jsonb_typeof(p->'upgrades') = 'array' THEN p->'upgrades'
                        WHEN jsonb_typeof(p->'upgrades') = 'object' THEN
                            COALESCE(
                                (SELECT jsonb_agg(v ORDER BY v)
                                 FROM jsonb_each(p->'upgrades') e,
                                      jsonb_array_elements_text(e.value) v
                                 WHERE jsonb_typeof(e.value) = 'array'),
                                '[]'::jsonb
                            )
                        ELSE '[]'::jsonb
                    END AS ids_json
                FROM pilot_data
            )
            SELECT
                pilot_xws,
                format,
                array_to_string(ARRAY(SELECT jsonb_array_elements_text(ids_json) ORDER BY 1), '|') AS combo,
                GREATEST(0, COALESCE(swiss_wins,0)) + GREATEST(0, COALESCE(swiss_losses,0))
                    + GREATEST(0, COALESCE(swiss_draws,0)) + GREATEST(0, COALESCE(cut_wins,0))
                    + GREATEST(0, COALESCE(cut_losses,0)) + GREATEST(0, COALESCE(cut_draws,0)) AS games,
                GREATEST(0, COALESCE(swiss_wins,0)) + GREATEST(0, COALESCE(cut_wins,0)) AS wins
            FROM upg
        """)
        rows2 = session.execute(sql2).fetchall()

    config_by_pilot: dict = defaultdict(lambda: defaultdict(dict))
    for pilot_xws, fmt, combo, games, wins in rows2:
        f = _fmt_of(fmt)
        games = int(games or 0)
        wins = int(wins or 0)
        ids = combo.split("|") if combo else []
        ids.sort()
        key = "|".join(ids)
        bucket = config_by_pilot[f][pilot_xws]
        if key not in bucket:
            bucket[key] = {"upgrade_ids": ids, "lists": 0, "games": 0, "wins": 0, "count": 0}
        cfg = bucket[key]
        cfg["count"] += 1
        cfg["games"] += games
        cfg["wins"] += wins
        if games > 0:
            cfg["lists"] += 1

    # ---- Header stats (one GROUP BY per source, same as cards/pilots). ----
    with Session(engine) as session:
        sql3 = text("""
            SELECT
                p->>'id' AS card_xws,
                COUNT(DISTINCT ps.id) AS entries_count,
                SUM(GREATEST(0, COALESCE(ps.swiss_wins,0)) + GREATEST(0, COALESCE(ps.cut_wins,0))) AS wins,
                SUM(
                    GREATEST(0, COALESCE(ps.swiss_wins,0)) + GREATEST(0, COALESCE(ps.swiss_losses,0))
                    + GREATEST(0, COALESCE(ps.swiss_draws,0)) + GREATEST(0, COALESCE(ps.cut_wins,0))
                    + GREATEST(0, COALESCE(ps.cut_losses,0)) + GREATEST(0, COALESCE(ps.cut_draws,0))
                ) AS games,
                COUNT(DISTINCT ps.list_id) AS different_lists_count,
                COUNT(DISTINCT l.ship_list) AS squadron_count
            FROM playerstanding ps
            JOIN tournament t ON t.id = ps.tournament_id
            JOIN list l ON l.id = ps.list_id
            JOIN jsonb_array_elements(l.list_json::jsonb->'pilots') p ON true
            WHERE (NOT t.is_team_event OR ps.is_team_member)
              AND t.format = :fmt
            GROUP BY p->>'id'
        """)
        target_fmt = "xwa" if ds == DataSource.XWA else "legacy_x2po"
        header_rows = session.execute(sql3, {"fmt": target_fmt}).fetchall()

    header = {}
    for card_xws, entries, wins, games, diff_lists, sq in header_rows:
        header[card_xws] = {
            "entries_count": int(entries or 0),
            "wins": int(wins or 0),
            "games_count": int(games or 0),
            "different_lists_count": int(diff_lists or 0),
            "list_count": int(diff_lists or 0),
            "squadron_count": int(sq or 0),
        }

    # Freeze defaultdicts -> plain dicts.
    pilot_configs_out = {}
    for f, by_pilot in config_by_pilot.items():
        pilot_configs_out[f] = {}
        for p, by_combo in by_pilot.items():
            pilot_configs_out[f][p] = {combo: dict(cfg) for combo, cfg in by_combo.items()}

    return {
        "pilot_upgrades": {f: dict(d) for f, d in pilot_upgrades.items()},
        "upgrade_pilots": {f: dict(d) for f, d in upgrade_pilots.items()},
        "pilot_chart": {f: dict(d) for f, d in pilot_chart.items()},
        "upgrade_chart": {f: dict(d) for f, d in upgrade_chart.items()},
        "pilot_configs": pilot_configs_out,
        "header": header,
        "ds": fmt_key,
    }


def get_snapshot(ds: DataSource) -> dict:
    """Cached access to the card-detail snapshot (auto-invalidated on data_version bump)."""
    return get_cached_or_compute(f"card_detail_snapshot|{ds.value}", lambda: build_snapshot(ds))
