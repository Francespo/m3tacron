# backend/data_structures/

## Responsibility
Enum types and Pydantic/SQLAlchemy value objects that define the closed sets of identifiers and shapes used across the X-Wing analytics backend (factions, formats, sources, scenarios, upgrade types, location). They act as the canonical vocabulary and DTO primitives shared by the database, analytics, and HTTP layers.

## Design
- Heavy use of `enum.StrEnum` with a `label` `@property` returning a human-readable string, and a `__str__` returning the raw value.
- `Faction` exposes `from_xws()` classmethod for tolerant XWS-string parsing and `get_faction_char()` helper for icon mapping.
- `Format` / `MacroFormat` form a two-level hierarchy: `Format` is a granular code (`AMG`, `XWA`, `FFG`, `LEGACY_X2PO`, `LEGACY_XLC`) and `Format.macro` resolves to `MacroFormat.V2_5` / `V2_0` / `UNKNOWN`. `infer_format_from_xws()` infers the format by inspecting the XWS `vendor` block (LBN, YASB, raithos, longshanks links).
- `SortingCriteria` provides `from_label()` for reverse-lookup and pairs with `SortDirection` for query ordering.
- `Location` is a `pydantic.BaseModel` with a `_normalize()` staticmethod (Title Case + strip) exposed via `Location.create()`. `LocationType` is a SQLAlchemy `TypeDecorator` (impl `JSON`) that serializes/deserializes the Pydantic model transparently to/from a JSON column.
- `Scenario`, `RoundType`, `UpgradeType`, `Source`, `DataSource`, `ViewMode` are flat string enums with `label` properties.
- No Pydantic `response_model` classes live here; schemas for HTTP I/O are defined in `backend/api/schemas.py`.

## Flow
1. Scraper or API request ingests raw XWS / tournament data and passes it through a parser (e.g., `Faction.from_xws()`, `infer_format_from_xws()`) to normalize into the canonical enum values.
2. Analytics layer (`backend/analytics/*`) receives `SortingCriteria` / `SortDirection` / `DataSource` enums as parameters and runs aggregations.
3. `Location` instances are created via `Location.create()`, persisted through the `LocationType` JSON column, and rehydrated on read.
4. Service/handler returns ORM rows or enum values; `backend/api/schemas.py` Pydantic models (which import these enums for typed fields) serialize the final JSON response.

## Integration
- **Consumed by**: `backend/models.py` (`Format`, `Source`, `Scenario`, `RoundType`, `Location`, `LocationType`), `backend/main.py` (`DataSource`), `backend/api/schemas.py` (`Faction`, `Format`, `Source`), `backend/api/{cards,ships,ship_detail,pilot_detail,squadrons}.py` and `backend/analytics/{core,ships,squadrons}.py` (`SortingCriteria`, `SortDirection`).
- **Depends on**: `enum.StrEnum`, `pydantic.BaseModel`, `sqlalchemy.JSON` / `TypeDecorator`.
- **Exposes**:
  - `Faction` — X-Wing faction identifiers (Rebel, Empire, Scum, Resistance, First Order, Republic, Separatist, Unknown) with `from_xws()` and `get_faction_char()`.
  - `Format` / `MacroFormat` — granular + macro X-Wing rule format codes, plus `infer_format_from_xws()`.
  - `Source` — tournament data origin (Longshanks, ListFortress, Rollbetter, Unknown).
  - `DataSource` — game-content data source (Legacy, XWA).
  - `Scenario` — 2.5 scenario names (Ancient Knowledge, Salvage Mission, etc.).
  - `RoundType` — `SWISS` / `CUT` round classification.
  - `UpgradeType` — X-Wing upgrade slot types (Talent, Crew, Torpedo, …).
  - `SortingCriteria` / `SortDirection` — query sort key + direction.
  - `ViewMode` — card browser view mode (`BASIC` / `ADVANCED`).
  - `Location` / `LocationType` — normalized city/country/continent Pydantic model with a matching SQLAlchemy JSON type.
