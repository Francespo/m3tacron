"""
Analytics Package.

=============================================================================
LAYER OVERVIEW
=============================================================================
The analytics layer is the data pipeline between the database and the API.
Each "heavy" page (lists, squadrons, ships, cards) has one analytics file
that runs the SQL aggregation for that page. Detail endpoints (list_detail,
squadron_detail, pilot_detail) also live in backend/api/ and use these same
analytics primitives.

=============================================================================
FILE MAP
=============================================================================
  core.py          — Pilot & upgrade card analytics (cards/* pages).
                     Also contains the catalog filter (Phase 1 of the
                     2-phase strategy: filter in-memory catalog, then
                     SQL-aggregate the matching list_json rows).
  lists.py         — List analytics (/lists page). GROUP BY list.canonical_signature.
  squadrons.py     — Squadron analytics (/squadrons page). GROUP BY list.ship_list.
  ships.py         — Ship analytics (/ships page). Uses pilot_ship_mapping table.
  factions.py      — Faction aggregations + get_meta_snapshot for the dashboard.
  charts.py        — Time-series chart data (legacy, full table scan — not yet
                     converted to use the list table).
  filters.py       — Legacy `filter_query` (SQLAlchemy ORM query builder).
                     Most analytics files now build WHERE clauses by hand
                     for performance; this is used by API detail endpoints.
  filter_helpers.py — Shared SQL-clause helpers: ship_list_filter_clause and
                      format_filter_clause. Eliminates duplication between
                      lists.py, squadrons.py, and the API detail endpoints.

=============================================================================
DATA MODEL
=============================================================================
All four heavy analytics files share the same shape:
  1. Build dynamic WHERE clauses from a `filters` dict.
  2. Run a single SQL GROUP BY query that JOINs playerstanding, tournament,
     and (for normalized analytics) the `list` table.
  3. Post-process in Python only for:
       - Faction enum mapping
       - Pilot JSON reshaping (raw -> Pydantic schema)
       - Result sorting

The `list` table (see backend/models.py) holds one row per unique squad list,
referenced by playerstanding.list_id. See backend/scripts/migrate_normalize_list.sql
for how it was created from historical data.

=============================================================================
CALLERS
=============================================================================
  api/lists.py          → aggregate_list_stats
  api/squadrons.py      → aggregate_squadron_stats
  api/ships.py          → aggregate_ship_stats
  api/cards.py          → aggregate_card_stats (mode='pilots' or 'upgrades')
  api/ship_detail.py    → aggregate_squadron_stats (for ship detail page)
  api/list_detail.py    → (queries list table directly, no helper call)
  api/squadron_detail.py → (queries list table directly, no helper call)
  api/pilot_detail.py   → (queries list table directly, no helper call)
  main.py               → get_meta_snapshot (dashboard)
"""
from .core import aggregate_card_stats
from .filters import filter_query, check_format_filter, apply_tournament_filters
from .ships import aggregate_ship_stats
from .factions import aggregate_faction_stats, get_meta_snapshot
from .lists import aggregate_list_stats

