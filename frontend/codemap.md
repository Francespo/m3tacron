# frontend/

## Responsibility
SvelteKit single-page application for browsing X-Wing Miniatures tournament data, squad builders, pilot/ship/upgrade lookup, analytics dashboards, and a public supporter/fundraising page. It is the read-only UI layer that talks to the FastAPI backend and to a pre-built X-Wing game data manifest.

## Design
- **Framework**: SvelteKit 2 with Svelte 5 runes (`$state`, `$derived`, `$effect`, `$props`); Node adapter for Docker/Coolify deployment; SSR enabled in production, disabled in dev.
- **Routing**: File-based routes under `src/routes/`; each page pairs a `+page.svelte` with a `+page.ts` `load` function that fetches data via the SvelteKit `fetch` and returns it as `data` props.
- **Reactive state**: Module-level runes inside `.svelte.ts` files replace classic `writable`/`derived` stores.
  - `src/lib/stores/filters.svelte.ts` exposes the `filters` object — global filter state (data source, dates, continents/countries/cities, formats, sources, ships, search, advanced ranges) with `activeChips`, `removeChip`, and `resetAll`.
  - `src/lib/stores/xwingData.svelte.ts` exposes the `xwingData` class instance — lazy-loaded manifest for `'xwa'` and `'legacy'` sources with `getShip`, `getPilot`, `getUpgrade`, `getPilotCountByShip`, and per-source caching.
- **API client**: `src/lib/api.ts` resolves `API_BASE` (same-origin `/api` fallback, honors `VITE_API_BASE` for absolute URLs, blocks internal hosts when browser is on a public host). Per-domain helpers in `src/lib/api/ships.ts` (`fetchAllShips`).
- **Styling**: Tailwind v4 via `@tailwindcss/vite` plus a `layout.css`; "terminal" theme classes (`bg-terminal-bg`, `bg-terminal-panel`, `border-border-dark`, `text-secondary`, `font-mono`). X-Wing Miniatures Font (icon classes like `xwing-miniatures-ship-*`, `xwing-miniatures-font-*`) and Chart.js (`chartAction` Svelte action on the dashboard).
- **Static game data**: Built by `scripts/generate-xwing-data.js` into `static/data-xwa/xwing-data.json` and `static/data-legacy/xwing-data.json`, then fetched at runtime by `xwingData` store.
- **Server routes** (SvelteKit endpoints, not pages): `src/routes/api/[...path]/+server.js` is a generic GET proxy to the backend (`http://backend:8888/api`), and `src/routes/api/meta-snapshot/+server.ts` proxies the dashboard snapshot.
- **Component composition**: `Sidebar` is fixed in `+layout.svelte`; listing pages mount a `FilterPanel` (with `extra` snippet for page-specific filters) + `SortSelector` + `ActiveChips` + list/grid cards. Detail pages embed specialized cards (`PilotCard`, `UpgradeCard`, `ListRowCard`, `SquadronRowCard`, `HallOfHeroes`).

## Flow
1. User navigates to a route (e.g., `/tournaments`).
2. SvelteKit runs the route's `+page.ts` `load` function with the SvelteKit `fetch` and `url` (URL params drive filters and pagination).
3. `load` calls the backend at `API_BASE/<endpoint>...` (e.g., `/api/tournaments?page=0&size=20&...`), threading `filters` values through `url.searchParams`.
4. Server-side proxy `src/routes/api/[...path]/+server.js` forwards client calls to the FastAPI service when used directly.
5. The page component receives `data` as `$props()`, applies client-side `+layout.ts` (`ssr` toggle) and local `$state` (page, sort, selected factions).
6. The shared `filters` store and `xwingData` manifest store expose derived, reactive state used across components (e.g., `ContentSourceToggle` writes `filters.dataSource`, the dashboard re-fetches `/api/meta-snapshot` in a `$effect`).
7. Components render lists, cards, and Chart.js canvases; `$derived` keeps ranks/win rates reactive to sort mode and source changes.

## Integration
- **Consumed by**: end users via the browser; served by the SvelteKit Node adapter (same origin as the backend's `/api` when behind a reverse proxy).
- **Depends on**:
  - FastAPI backend at `/api/*` (CORS or same-origin) — endpoints used: `meta-snapshot`, `tournaments(/[id])`, `squadrons`, `squadron/[signature]/{stats,pilots,lists}`, `lists`, `list/[list_id]/stats`, `ships(/all)`, `ship/[xws]`, `pilots`, `pilot/[xws]/{upgrades,chart,configurations}`, `cards/{pilots,upgrades}`, `support/fund-status`, `support/supporters`.
  - Static xwing-data2 manifests under `static/data-xwa/` and `static/data-legacy/` (fetched by the `xwingData` store).
- **Exposes**: Browser routes — `/` (dashboard), `/tournaments` + `/tournaments/[id]`, `/squadrons` + `/squadron/[signature]`, `/lists` + `/list/[list_id]`, `/ships` + `/ship/[xws]`, `/pilots/[id]` (cards-tab pilot), `/pilot/[id]` (deep pilot view), `/cards`, `/upgrades/[id]`, `/support`; and the public `$lib` component library.

## Subdirectories
- `src/routes/` — file-based routes (pages, dynamic detail routes, and SvelteKit `+server` proxy endpoints under `routes/api/`).
- `src/lib/components/` — UI components: `Sidebar`, `FilterPanel`, `TournamentFilters`, `AdvancedFilters`, `ActiveFilters`, `ActiveChips`, `ContentSourceToggle`, `SortSelector`, `ShipChassisFilter`, `PilotCard`, `UpgradeCard`, `ListRowCard`, `SquadronRowCard`, `StatIcon`, `EvolutionProgressBar`, `HallOfHeroes`.
- `src/lib/stores/` — reactive module-state stores: `filters.svelte.ts` (global filter UI state) and `xwingData.svelte.ts` (game data manifest cache).
- `src/lib/api/` — backend clients: `api.ts` (resolves `API_BASE` / `VITE_API_BASE`) and `api/ships.ts` (`fetchAllShips`).
- `src/lib/data/` — static lookup tables and helpers: `factions.ts` (colors/chars/labels), `formats.ts` (AMG/XWA/FFG/Legacy labels/colors), `slots.ts` (X-Wing slot icon glyphs), `source.ts` (ListFortress/Longshanks/Rollbetter).
- `src/lib/index.ts`, `src/lib/index.js` — `$lib` alias entry stubs.
- `src/app.css`, `src/app.html`, `src/app.d.ts` — global Tailwind entry, HTML shell, and ambient TypeScript types.
