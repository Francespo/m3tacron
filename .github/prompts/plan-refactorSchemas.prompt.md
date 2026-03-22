# Plan: Refactor Schemas (Coherent Naming)

We are finalizing the schema refactor with consistent naming conventions:
- **`*Data`**: Composition models & Event Info (structural data).
- **`*Stats`**: Analytic models (aggregated stats).

## Renaming Mapping
*   `FactionStat` → `FactionStats`
*   `TournamentRow` → `TournamentData` (Holds core tournament info).
*   `PlayerStandingsRow` → `PlayerResultData` (Holds individual player result data).
*   `MatchRow` → `MatchData` (Holds match data).

## Schema Finale (backend/api/schemas.py)

### 1. Composition Data (Strutturali)
*   **`UpgradeData`**:
    *   `xws`: `str`
*   **`PilotData`**:
    *   `xws`: `str`
    *   `upgrades`: `list[UpgradeData]`
*   **`ListData`**:
    *   `name`: `str`
    *   `signature`: `str`
    *   `points`: `int`
    *   `original_points`: `int`
    *   `faction_xws`: `Faction` (Enum) - *Renamed from faction to faction_xws for consistency with ShipStats*
    *   `pilots`: `list[PilotData]`
    *   `wins`: `int`
    *   `games`: `int`

### 2. Analytics Stats (Aggregati)
*   **`FactionStats`**:
    *   `xws`: `Faction` (Enum)
    *   `games_count`: `int`
    *   `list_count`: `int`
    *   `different_lists_count`: `int`
    *   `wins`: `int`
*   **`PilotStats`**:
    *   `xws`: `str`
    *   `games_count`: `int`
    *   `list_count`: `int`
    *   `different_lists_count`: `int`
    *   `wins`: `int`
*   **`UpgradeStats`**:
    *   `xws`: `str`
    *   `games_count`: `int`
    *   `list_count`: `int`
    *   `different_lists_count`: `int`
    *   `wins`: `int`
*   **`ShipStats`**:
    *   `xws`: `str`
    *   `faction_xws`: `Faction` (Enum)
    *   `games_count`: `int`
    *   `list_count`: `int`
    *   `different_lists_count`: `int`
    *   `wins`: `int`

### 3. Event Data (Tornei e Risultati)
*   **`TournamentData`**:
    *   `id`: `int`
    *   `name`: `str`
    *   `date`: `str`
    *   `players`: `int`
    *   `format`: `Format` (Enum)
    *   `platform`: `Platform` (Enum)
    *   `location`: `str`
    *   `url`: `str`
*   **`PlayerResultData`**:
    *   `id`: `int`
    *   `name`: `str`
    *   `rank`: `int`
    *   `swiss_rank`: `int`
    *   `cut_rank`: `int | None`
    *   `wins`: `int`
    *   `losses`: `int`
    *   `list_json`: `dict | None`
    *   `faction`: `Faction` (Enum)
*   **`MatchData`**:
    *   `round`: `int`
    *   `type`: `str`
    *   `player1`: `str`
    *   `player2`: `str`
    *   `score1`: `int`
    *   `score2`: `int`
    *   `winner_id`: `int`
    *   `scenario`: `str`

## Execution Steps
1.  **Update `backend/data_structures`**: Ensure `Faction`, `Format`, `Platform` are Enums.
2.  **Update `backend/api/schemas.py`**: Rewrite with the final schemas defined above.
3.  **Update References**:
    *   `Pagination*Response` models.
    *   `MetaSnapshotResponse`.
    *   `backend/api/tournaments.py`, `backend/analytics/core.py`, `backend/analytics/factions.py`.

## Verification
1.  Check naming consistency across all schemas.
2.  Verify logical separation (Data vs Stats).
