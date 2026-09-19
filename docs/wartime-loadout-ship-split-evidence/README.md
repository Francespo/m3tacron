# Visual evidence — Wartime Loadout Y-Wing split (phase 1)

Committed so the review evidence lives in the repository instead of only in the
PR description. Every image is a screenshot of **this branch** running as a
local production build; nothing here is a mock-up and no production data was
written.

Total size is kept small (~200 KB): the PNGs were palette-optimised
(`PIL` `quantize(colors=256)` + `optimize=True`) from the raw captures. The
wider set of captures (icon fix, old-link checks) stays in the PR description
because those checks are textual (`getComputedStyle` output), not visual.

## How these were produced

```bash
# 1. throwaway database for the local stack (empty schema, no data written)
docker run -d --name m3tacron-alias-test-pg \
  -e POSTGRES_PASSWORD=test -e POSTGRES_DB=m3tacron -p 5433:5432 postgres:17-alpine

# 2. backend: real vendored XWA data, cache prewarm disabled, empty database
DATABASE_URL="postgresql://postgres:test@localhost:5433/m3tacron" PREWARM_CACHE=false \
  .venv/bin/python -m uvicorn backend.main:app --host 0.0.0.0 --port 8888

# 3. frontend: production build + adapter-node server (same-origin /api proxy)
npm ci --prefix frontend
npm run check --prefix frontend     # 0 errors
npm run build --prefix frontend
PORT=4173 ORIGIN=http://localhost:4173 node frontend/build
```

`/etc/hosts` needed a temporary `127.0.0.1 backend` entry because the SvelteKit
SSR proxy in `frontend/src/routes/api/[...path]/+server.js` targets
`http://backend:8888/api`. The entry was removed afterwards.

Captures: desktop viewport `1440x900`, mobile viewport `390x844`, taken with the
agent browser (`set viewport …` → `open <url>` → `screenshot <path>`).

URLs used:

```
http://localhost:4173/ships?ships=btanr2ywing&ships=btanr2wywing&sort_metric=Name&sort_direction=asc
http://localhost:4173/ship/btanr2ywing
http://localhost:4173/ship/btanr2wywing
```

## The images

| File | Viewport | What it shows |
| --- | --- | --- |
| `desktop-ships-both-labels.png` | 1440x900 | Ships grid filtered to the two chassis: two cards reading **`Y-wing`** and **`Y-wing (Wartime Loadout)`**, both "10 Pilots", instead of two identical "BTA-NR2 Y-Wing" cards. |
| `mobile-ships-both-labels.png` | 390x844 | The same two cards stacked on mobile, with the same two distinct labels. |
| `desktop-ship-filter-options-and-chips.png` | 1440x900 | Filter options and active-filter chips: the chassis list shows a checked **`Y-wing`** and a checked **`Y-wing (Wartime Loadout)`** (and no collision with `BTL-A4 Y-wing` / `BTL-B Y-wing`); the two active chips carry the titles `Ship: Y-wing` and `Ship: Y-wing (Wartime Loadout)`. |
| `desktop-ship-y-wing.png` | 1440x900 | Plain chassis detail page: title `Y-wing`, statline attack 2 / agility 1 / hull 4 / **shields 3**, `Ship Ability: Intuitive Interface`. |
| `desktop-ship-y-wing-wartime-loadout.png` | 1440x900 | Integrated chassis detail page: title `Y-wing (Wartime Loadout)`, statline attack 2 / agility 1 / hull 4 / **shields 5**, `Ship Ability: Devastating Barrage`. |
| `mobile-ship-y-wing.png` | 390x844 | The plain chassis page on mobile: `Y-wing`, shields 3, `Intuitive Interface`. |
| `mobile-ship-y-wing-wartime-loadout.png` | 390x844 | The integrated chassis page on mobile: `Y-wing (Wartime Loadout)`, shields 5, `Devastating Barrage`. |

## Observed values behind the images

Extracted from the running app (not from the earlier report):

```
GET /api/ships/all?data_source=xwa
-> {"xws":"btanr2ywing",  "name":"Y-wing",                   "factions":["resistance"]}
   {"xws":"btanr2wywing", "name":"Y-wing (Wartime Loadout)", "factions":["resistance"]}
   {"xws":"delta7baethersprite","name":"Delta-7B Aethersprite","factions":["galacticrepublic"]}

/ships?ships=btanr2ywing&ships=btanr2wywing
-> card labels ["Y-wing", "Y-wing (Wartime Loadout)"]; chip titles
   ["Ship: Y-wing", "Ship: Y-wing (Wartime Loadout)"]

/ship/btanr2ywing   -> title "Y-wing — Ship Detail | M3taCron"
                       "Y-wing SMALL 2 1 4 3 SHIP ABILITY Intuitive Interface …"
/ship/btanr2wywing  -> title "Y-wing (Wartime Loadout) — Ship Detail | M3taCron"
                       "Y-wing (Wartime Loadout) SMALL 2 1 4 5 SHIP ABILITY Devastating Barrage …"
```

Every value above comes from the vendored source or an id-keyed lookup; the
labels are display-only and the ids (`btanr2ywing`, `btanr2wywing`) and pilot
`-wartime` suffixes are unchanged. See
[`../wartime-loadout-ship-split-inventory.md`](../wartime-loadout-ship-split-inventory.md)
§14/§15 for where the labels are defined and why they are not baked into the
generated manifests.
