-- Drop indexes that are redundant or unused on production.
--
-- Every entry is either an exact duplicate of another index or a prefix of a
-- wider one, so no query loses a plan. Verified against pg_stat_user_indexes
-- after months of uptime: idx_scan = 0 for all of them.
--
-- Not applied at startup on purpose: DROP INDEX takes an ACCESS EXCLUSIVE
-- lock. Run it manually in a low-traffic window, with a short lock timeout:
--
--   psql "$DATABASE_URL" -v ON_ERROR_STOP=1 \
--        -c "SET lock_timeout = '5s'" \
--        -f backend/scripts/migrate_drop_unused_indexes.sql
--
-- Safe to re-run (DROP INDEX IF EXISTS). ANALYZE refreshes the planner after
-- the drop.

-- Exact duplicates (the ix_* twin is the one the ORM / startup ensures).
DROP INDEX IF EXISTS idx_playerstanding_tournament_id;
DROP INDEX IF EXISTS idx_ps_faction_xws_normalized;
DROP INDEX IF EXISTS idx_list_faction_xws_normalized;

-- Single-column prefix of idx_psm_ship_source (ship_xws, source).
DROP INDEX IF EXISTS ix_pilot_ship_mapping_ship_xws;

-- jsonb_path_ops GIN index on playerstanding.list_json: 12 MB, never scanned
-- (the analytics unnest the JSON instead of using containment operators).
DROP INDEX IF EXISTS idx_ps_list_json_gin;

ANALYZE;
