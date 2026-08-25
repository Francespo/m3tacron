from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session, select, func
from datetime import datetime, timedelta
import os
import time

from .database import engine, create_db_and_tables
from .models import Tournament, PlayerStanding
from .analytics.factions import get_meta_snapshot
from .data_structures.data_source import DataSource
from .cache import get_cached_or_compute
from .api.schemas import MetaSnapshotResponse
from .api.tournaments import router as tournaments_router
from .api.lists import router as lists_router
from .api.squadrons import router as squadrons_router
from .api.cards import router as cards_router
from .api.ships import router as ships_router
from .api.pilot_detail import router as pilot_detail_router
from .api.upgrade_detail import router as upgrade_detail_router
from .api.ship_detail import router as ship_detail_router
from .api.squadron_detail import router as squadron_detail_router
from .api.list_detail import router as list_detail_router
from .api.support import router as support_router

app = FastAPI(title="M3taCron Backend", version="1.0.0")

# Include routers
app.include_router(tournaments_router)
app.include_router(lists_router)
app.include_router(squadrons_router)
app.include_router(cards_router)
app.include_router(ships_router)
app.include_router(pilot_detail_router)
app.include_router(upgrade_detail_router)
app.include_router(ship_detail_router)
app.include_router(squadron_detail_router)
app.include_router(list_detail_router)
app.include_router(support_router)

# Configure CORS for frontend access
allowed_origins = [o.strip() for o in os.getenv("ALLOWED_ORIGINS", "*").split(",") if o.strip()]
allow_all_origins = len(allowed_origins) == 1 and allowed_origins[0] == "*"

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if allow_all_origins else allowed_origins,
    allow_credentials=not allow_all_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    retries = int(os.getenv("DB_STARTUP_RETRIES", "20"))
    delay_seconds = float(os.getenv("DB_STARTUP_DELAY_SECONDS", "3"))

    last_error = None
    for attempt in range(1, retries + 1):
        try:
            create_db_and_tables()
            print(f"Database ready on attempt {attempt}/{retries}")
            break
        except Exception as exc:
            last_error = exc
            print(f"Database not ready (attempt {attempt}/{retries}): {exc}")
            time.sleep(delay_seconds)
    else:
        raise RuntimeError(f"Database startup failed after {retries} attempts: {last_error}")

    # Pre-warm the analytics cache so the first user request is instant.
    # Runs in a background thread so the server accepts traffic immediately.
    if os.getenv("PREWARM_CACHE", "true").lower() == "true":
        _prewarm_cache()

    # Auto-rewarm on any DB mutation: poll scrape_meta.data_version and
    # repopulate hot keys when it changes (scraper, promote, or manual bump).
    # This makes cache self-healing after *any* DB modification without
    # requiring a restart or an external webhook.
    if os.getenv("CACHE_AUTO_REWARM", "true").lower() == "true":
        _start_cache_auto_rewarm()


# ---------------------------------------------------------------------------
# Warm state — exposed via GET /api/cache/stats for live verification
# ---------------------------------------------------------------------------

_warm_state: dict = {
    "last_warm_at": None,          # ISO timestamp of last warm completion
    "last_warm_duration_s": None,  # seconds of last full warm (snapshots + endpoints + ship details)
    "detail_snapshots": {},        # {ds: {elapsed_s, pilots, upgrades}}
    "endpoints": {"ok": 0, "fail": 0, "elapsed_s": None, "items": []},  # last _probe_warm_endpoints
    "ship_details": {"ok": 0, "fail": 0, "elapsed_s": None, "total_urls": 0, "workers": None},
    "history": [],                 # last 5 warm runs (for debugging)
}

def _record_warm_history(entry: dict) -> None:
    _warm_state["history"].append(entry)
    if len(_warm_state["history"]) > 5:
        _warm_state["history"].pop(0)


# ---------------------------------------------------------------------------
# Cache warm helpers: shared endpoint list + HTTP probing
# ---------------------------------------------------------------------------

def _warm_endpoint_list() -> list[str]:
    """Canonical list of API paths to warm. Used by startup and auto-rewarm.

    Covers: dashboard (4 combos xwa/legacy x epic), ships (4 combos, all pages
    via single aggregation page/size excluded), lists/squadrons page 0 (4 combos
    each — page 1..N are slices of same cached aggregation), cards (8 combos),
    tournaments page 0 (2 entries). Total ~22 keys, <20s. Per-ship detail is
    warmed separately via _warm_ship_details() with parallel workers.
    """
    endpoints: list[str] = [
        # Dashboard meta-snapshot (xwa + legacy, with and without epic)
        "meta-snapshot?data_source=xwa",
        "meta-snapshot?data_source=xwa&epic=true",
        "meta-snapshot?data_source=legacy",
        "meta-snapshot?data_source=legacy&epic=true",
    ]
    # Ships — all pages are slices of one cached aggregation (page/size excluded
    # from key, see backend/api/ships.py). Warm 2 combos: xwa/legacy (ships
    # endpoint has no epic param — epic filtering is client-side via xwingData).
    for ds in ("xwa", "legacy"):
        endpoints.append(f"ships?page=0&size=21&sort_metric=Lists&sort_direction=desc&data_source={ds}")
    # Lists page 0 — 4 combos. page/size/sort excluded from cache key, so
    # page 1..9 are already warm if page 0 is.
    for ds in ("xwa", "legacy"):
        for epic in ("", "&epic=true"):
            endpoints.append(f"lists?page=0&size=20&sort_metric=Games&sort_direction=desc&min_games=3&data_source={ds}{epic}")
    # Squadrons page 0 — 4 combos (same page-excluded caching)
    for ds in ("xwa", "legacy"):
        for epic in ("", "&epic=true"):
            endpoints.append(f"squadrons?page=0&size=20&sort_metric=Games&sort_direction=desc&data_source={ds}{epic}")
    # Tournaments page 0 — 1 entry (tournaments has no data_source param; its
    # cache key includes page so only page 0 is warmed, page 1..4 on-demand).
    endpoints.append("tournaments?page=0&size=20&sort_metric=Date&sort_direction=desc")
    endpoints.extend([
        # Cards/Pilots - 4 combos
        "cards/pilots?page=0&size=20&sort_metric=Lists&sort_direction=desc&data_source=xwa",
        "cards/pilots?page=0&size=20&sort_metric=Lists&sort_direction=desc&data_source=xwa&epic=true",
        "cards/pilots?page=0&size=20&sort_metric=Lists&sort_direction=desc&data_source=legacy",
        "cards/pilots?page=0&size=20&sort_metric=Lists&sort_direction=desc&data_source=legacy&epic=true",
        # Cards/Upgrades - 4 combos
        "cards/upgrades?page=0&size=20&sort_metric=Lists&sort_direction=desc&data_source=xwa",
        "cards/upgrades?page=0&size=20&sort_metric=Lists&sort_direction=desc&data_source=xwa&epic=true",
        "cards/upgrades?page=0&size=20&sort_metric=Lists&sort_direction=desc&data_source=legacy",
        "cards/upgrades?page=0&size=20&sort_metric=Lists&sort_direction=desc&data_source=legacy&epic=true",
    ])
    return endpoints


def _warm_detail_snapshots() -> None:
    """Eagerly build the precomputed card-detail snapshots (xwa + legacy).

    Without this, the first detail-page request after a scrape/restart pays the
    ~12s snapshot build. Warm here at startup and after every data_version bump
    (auto-rewarm) so no user ever sees a cold detail page. The snapshot is cached
    under card_detail_snapshot|<ds> and is automatically invalidated on the next
    data_version change.
    """
    import time as _t
    from datetime import datetime, timezone
    from .analytics.precompute import get_snapshot
    from .data_structures.data_source import DataSource

    for ds in (DataSource.XWA, DataSource.LEGACY):
        t0 = _t.time()
        try:
            snap = get_snapshot(ds)
            n_upg = sum(len(v) for f, v in snap["pilot_upgrades"].items() if f == ds.value)
            elapsed = _t.time() - t0
            print(f"[prewarm] detail snapshot {ds.value}: {elapsed:.1f}s ✓ "
                  f"(header {len(snap['header'])} pilots, upg keys {n_upg})")
            _warm_state["detail_snapshots"][ds.value] = {
                "elapsed_s": round(elapsed, 2),
                "pilots": len(snap["header"]),
                "upg_keys": n_upg,
                "at": datetime.now(timezone.utc).isoformat(),
            }
        except Exception as e:
            print(f"[prewarm] detail snapshot {ds.value}: FAILED ({e})")
            _warm_state["detail_snapshots"][ds.value] = {"error": str(e)}


def _warm_ship_details() -> None:
    """Prewarm all ship detail pages (xwa/legacy × epic × 4 endpoints) **in-process**.

    Each ship has 4 cached aggregates:
      ship_info|{xws}|{ds}|..., ship_pilots|{xws}|..., ship_lists|{xws}|..., ship_squadrons|{xws}|...
    All via backend.cache.get_cached_or_compute. The previous version warmed
    via HTTP GET to http://127.0.0.1:8888 — with 2 uvicorn workers that put the
    in-memory cache (per-process dict) out of sync and deadlocked in_flight
    across processes. This version computes directly in this process's cache,
    touching no HTTP and no cross-worker coordination. Runs on a background
    thread so the server accepts traffic immediately.

    Covers 92 ships × 4 combos (xwa/legacy × epic) × 4 endpoints = 1472 keys.
    Sequential HTTP timeout (30s) is gone; DB work is the only cost, shared via
    cache dedup if multiple threads compute the same key.
    """
    import time as _t
    from datetime import datetime, timezone

    if os.getenv("SHIP_DETAIL_WARM", "true").lower() != "true":
        print("[prewarm] ship details: skipped (SHIP_DETAIL_WARM=false)")
        _warm_state["ship_details"] = {"skipped": True}
        return

    try:
        from .utils.xwing_data.ships import load_all_ships
        from .data_structures.data_source import DataSource
        from .cache import get_cached_or_compute
        from .analytics.ships import aggregate_ship_stats
        from .analytics.core import aggregate_card_stats
        from .analytics.lists import aggregate_list_stats, fetch_list_pilots
        from .analytics.squadrons import aggregate_squadron_stats
        from .data_structures.sorting_order import SortingCriteria, SortDirection
        from .api.ship_detail import _build_filters, _ship_filter_cache_suffix
        from .api.formatters import enrich_list_data
    except Exception as e:
        print(f"[prewarm] ship details: FAILED to load deps ({e})")
        _warm_state["ship_details"] = {"error": str(e)}
        return

    all_xws: set[str] = set()
    for ds in (DataSource.XWA, DataSource.LEGACY):
        try:
            all_xws.update(load_all_ships(ds).keys())
        except Exception:
            pass

    if not all_xws:
        print("[prewarm] ship details: no ships found")
        _warm_state["ship_details"] = {"error": "no ships"}
        return

    # 4 combos: xwa/legacy × epic — must match ship_detail.py cache keys exactly
    # (which use _ship_filter_cache_suffix). Otherwise warm misses and click stays cold.
    combos: list[tuple[DataSource, bool]] = [
        (DataSource.XWA, False),
        (DataSource.XWA, True),
        (DataSource.LEGACY, False),
        (DataSource.LEGACY, True),
    ]

    t0 = _t.time()
    ok = 0
    fail = 0
    for xws in sorted(all_xws):
        for ds, epic in combos:
            # Build the canonical suffix exactly as the endpoint does (all None except epic)
            suffix = _ship_filter_cache_suffix(
                formats=None, factions=None, ships=None, continent=None, country=None, city=None,
                platforms=None, sources=None, date_start=None, date_end=None,
                player_count_min=None, player_count_max=None, search=None, epic=epic, faction=None,
            )
            # ship_info — key: ship_info|{xws}|{ds}|suffix ; value: single dict (stats[0])
            try:
                cache_key_info = f"ship_info|{xws}|{ds.value}{suffix}"
                flt = _build_filters(ship_xws=xws, formats=None, factions=None, faction=None, ships=None, continent=None, country=None, city=None, platforms=None, sources=None, date_start=None, date_end=None, player_count_min=None, player_count_max=None, search=None, epic=epic)
                def _compute_info(flt=flt, ds=ds):
                    stats = aggregate_ship_stats(flt, SortingCriteria.GAMES, SortDirection.DESCENDING, ds)
                    return stats[0] if stats else {}
                get_cached_or_compute(cache_key_info, _compute_info)
                ok += 1
            except Exception as e:
                print(f"[prewarm] ship details {xws}/{ds.value}/epic={epic}/info: FAILED ({e})")
                fail += 1
            # ship_pilots — key: ship_pilots|{xws}|{ds}|Lists|desc|suffix ; default sort Lists desc
            try:
                cache_key_pilots = f"ship_pilots|{xws}|{ds.value}|Lists|desc{suffix}"
                flt = _build_filters(ship_xws=xws, formats=None, factions=None, faction=None, ships=None, continent=None, country=None, city=None, platforms=None, sources=None, date_start=None, date_end=None, player_count_min=None, player_count_max=None, search=None, epic=epic)
                get_cached_or_compute(cache_key_pilots, lambda flt=flt, ds=ds: aggregate_card_stats(flt, SortingCriteria.LISTS, SortDirection.DESCENDING, "pilots", ds))
                ok += 1
            except Exception as e:
                print(f"[prewarm] ship details {xws}/{ds.value}/epic={epic}/pilots: FAILED ({e})")
                fail += 1
            # ship_lists — key: ship_lists|{xws}|{ds}|10|suffix ; compute is raw aggregate before enrichment
            try:
                cache_key_lists = f"ship_lists|{xws}|{ds.value}|10{suffix}"
                flt = _build_filters(ship_xws=xws, formats=None, factions=None, faction=None, ships=None, continent=None, country=None, city=None, platforms=None, sources=None, date_start=None, date_end=None, player_count_min=None, player_count_max=None, search=None, epic=epic)
                get_cached_or_compute(cache_key_lists, lambda flt=flt, ds=ds: aggregate_list_stats(flt, data_source=ds))
                ok += 1
            except Exception as e:
                print(f"[prewarm] ship details {xws}/{ds.value}/epic={epic}/lists: FAILED ({e})")
                fail += 1
            # ship_squadrons — key: ship_squadrons|{xws}|{ds}|10|suffix
            try:
                cache_key_sq = f"ship_squadrons|{xws}|{ds.value}|10{suffix}"
                flt = _build_filters(ship_xws=xws, formats=None, factions=None, faction=None, ships=None, continent=None, country=None, city=None, platforms=None, sources=None, date_start=None, date_end=None, player_count_min=None, player_count_max=None, search=None, epic=epic)
                get_cached_or_compute(cache_key_sq, lambda flt=flt, ds=ds: aggregate_squadron_stats(flt, SortingCriteria.WINRATE, SortDirection.DESCENDING, ds))
                ok += 1
            except Exception as e:
                print(f"[prewarm] ship details {xws}/{ds.value}/epic={epic}/squadrons: FAILED ({e})")
                fail += 1

    elapsed = _t.time() - t0
    print(f"[prewarm] ship details (in-process): {ok} ok, {fail} fail in {elapsed:.1f}s ({len(all_xws)} ships × 4 combos × 4 kinds) ✓")
    _warm_state["ship_details"] = {
        "ok": ok, "fail": fail, "elapsed_s": round(elapsed, 1),
        "total_urls": len(all_xws) * len(combos) * 4, "ships": len(all_xws), "workers": 1,
        "mode": "in-process",
        "at": datetime.now(timezone.utc).isoformat(),
    }


def _probe_warm_endpoints(base: str, endpoints: list[str]) -> None:
    """Sequentially GET each endpoint; logs timing or failure and records warm state."""
    import urllib.request
    import json
    from datetime import datetime, timezone

    t0_all = time.time()
    ok = 0
    fail = 0
    items: list[dict] = []
    for path in endpoints:
        name = path.split("?")[0].split("/")[-1] or "root"
        try:
            t0 = time.time()
            req = urllib.request.Request(f"{base}/api/{path}")
            resp = urllib.request.urlopen(req, timeout=150)
            data = json.loads(resp.read())
            count = data.get("total", len(data.get("items", [])))
            elapsed = time.time() - t0
            print(f"[prewarm] {name}: {count} items in {elapsed:.1f}s ✓")
            ok += 1
            items.append({"path": path, "count": count, "elapsed_s": round(elapsed, 2)})
        except Exception as e:
            print(f"[prewarm] {name}: FAILED ({e})")
            fail += 1
            items.append({"path": path, "error": str(e)})
    elapsed_all = time.time() - t0_all
    _warm_state["endpoints"] = {
        "ok": ok, "fail": fail, "elapsed_s": round(elapsed_all, 1),
        "total": len(endpoints), "items": items,
        "at": datetime.now(timezone.utc).isoformat(),
    }


def _prewarm_cache():
    """Hit the API endpoints via HTTP so cache keys exactly match what users request.

    Runs in a daemon thread so startup returns immediately. Uses internal
    HTTP requests (no external port needed) via the same uvicorn worker.
    Also eagerly builds the card-detail snapshots (xwa + legacy) so detail pages
    are warm on first visit, and all ship detail pages (xwa/legacy × epic).
    """
    import threading

    def _run():
        import datetime as _dt
        t0 = time.time()
        time.sleep(1.5)  # wait for uvicorn to finish binding
        _warm_detail_snapshots()
        _probe_warm_endpoints("http://127.0.0.1:8888", _warm_endpoint_list())
        _warm_ship_details()
        elapsed = time.time() - t0
        now = _dt.datetime.now(_dt.timezone.utc).isoformat()
        _warm_state["last_warm_at"] = now
        _warm_state["last_warm_duration_s"] = round(elapsed, 1)
        _record_warm_history({
            "at": now, "elapsed_s": round(elapsed, 1),
            "endpoints": dict(_warm_state["endpoints"]),
            "ship_details": dict(_warm_state["ship_details"]),
            "detail_snapshots": dict(_warm_state["detail_snapshots"]),
            "trigger": "startup",
        })
        print(f"[prewarm] done in {elapsed:.1f}s")

    thread = threading.Thread(target=_run, daemon=True, name="cache-prewarm")
    thread.start()


def _start_cache_auto_rewarm():
    """Poll scrape_meta.data_version; when it changes, clear + re-probe hot keys.

    This runs in a daemon thread and makes the cache automatically recompute
    after *any* DB mutation that bumps data_version (scraper, promote script,
    manual SQL). Without this, lazy invalidation alone leaves the next user's
    request to pay the cold recompute cost (~3-8s for meta-snapshot).

    Env:
      CACHE_AUTO_REWARM_POLL_SECONDS (default 10): poll interval.
      CACHE_AUTO_REWARM_DEBOUNCE_SECONDS (default 3): wait after version bump
        before rewarming (lets scraper transactions settle).
    """
    import threading

    poll_s = float(os.getenv("CACHE_AUTO_REWARM_POLL_SECONDS", "10"))
    debounce_s = float(os.getenv("CACHE_AUTO_REWARM_DEBOUNCE_SECONDS", "3"))

    def _loop():
        from backend.cache import get_db_version  # local import avoids cycle; available after engine init
        import datetime as _dt

        # Seed last_seen so we don't rewarm immediately on startup (startup
        # already did _prewarm_cache). Wait one poll so data_version is readable.
        time.sleep(poll_s)
        last_seen = get_db_version()
        while True:
            try:
                time.sleep(poll_s)
                cur = get_db_version()
                if cur is not None and cur != last_seen:
                    print(f"[auto-rewarm] data_version {last_seen} -> {cur}, rewarming cache…")
                    if debounce_s > 0:
                        time.sleep(debounce_s)
                    t0 = time.time()
                    _warm_detail_snapshots()
                    _probe_warm_endpoints("http://127.0.0.1:8888", _warm_endpoint_list())
                    _warm_ship_details()
                    elapsed = time.time() - t0
                    now = _dt.datetime.now(_dt.timezone.utc).isoformat()
                    _warm_state["last_warm_at"] = now
                    _warm_state["last_warm_duration_s"] = round(elapsed, 1)
                    _record_warm_history({
                        "at": now, "elapsed_s": round(elapsed, 1),
                        "endpoints": dict(_warm_state["endpoints"]),
                        "ship_details": dict(_warm_state["ship_details"]),
                        "detail_snapshots": dict(_warm_state["detail_snapshots"]),
                        "trigger": f"auto-rewarm {last_seen}->{cur}",
                    })
                    print(f"[auto-rewarm] done in {elapsed:.1f}s")
                    last_seen = cur
                elif cur is not None:
                    last_seen = cur
            except Exception as e:
                # Never kill the daemon; log and continue polling.
                print(f"[auto-rewarm] poll error: {e}")

    thread = threading.Thread(target=_loop, daemon=True, name="cache-auto-rewarm")
    thread.start()


@app.get("/api/cache/stats")
def cache_stats_endpoint():
    """Live cache inspection: entries, warm history, timings, memory estimate.

    No auth — read-only. Use to verify that all caches are loaded in prod/preview:
      curl https://162.dev.m3tacron.com/api/cache/stats | jq
    """
    from .cache import cache_stats as _cache_stats
    cs = _cache_stats()
    # _warm_state is populated by _prewarm_cache / _start_cache_auto_rewarm
    return {
        "cache": cs,
        "warm": dict(_warm_state),
        "config": {
            "warm_endpoints": len(_warm_endpoint_list()),
            "ship_detail_total_urls": 1472,  # 92 ships × 4 combos × 4 endpoints
            "max_cache_entries": 1000,
        },
    }


@app.get("/")
def read_root():
    return {"status": "Backend is running"}


@app.get("/api/meta-snapshot", response_model=MetaSnapshotResponse)
def get_snapshot(
    data_source: str = Query("xwa", description="Data source: xwa or legacy"),
    epic: bool = Query(False, description="Include epic content"),
):
    ds_enum = DataSource.XWA if data_source == "xwa" else DataSource.LEGACY
    def compute():
        # Source -> formats mapping. Must stay in sync with frontend's
        # filters.svelte / +page.svelte formatsForSource.
        if ds_enum == DataSource.XWA:
            allowed_formats = ["xwa", "amg"] if epic else ["xwa"]
        else:
            allowed_formats = ["legacy_x2po", "legacy_xlc", "legacy_pandorum"] if epic else ["legacy_x2po", "legacy_xlc", "legacy_pandorum"]

        # Runs the 5 aggregations + 2 count queries. Cached by (data_source, epic),
        # so the dashboard (which hits this on every load / filter toggle)
        # only pays the cost once per data_version.
        from .api.formatters import enrich_list_data
        snapshot = get_meta_snapshot(ds_enum, allowed_formats=allowed_formats, include_epic=epic)

        # Enrich list data with pilot/ship metadata (names, ship icons,
        # pack captions, upgrade names) before serving to the dashboard.
        raw_lists = snapshot.get("lists", [])
        enriched_lists = [enrich_list_data(l, source=ds_enum) for l in raw_lists]

        total_tournaments = 0
        total_players = 0

        try:
            with Session(engine) as session:
                start_date = datetime.now() - timedelta(days=90)

                total_tournaments_query = (
                    select(func.count(Tournament.id))
                    .where(Tournament.date >= start_date)
                    .where(Tournament.format.in_(allowed_formats))
                )
                res_tournaments = session.exec(total_tournaments_query).one_or_none()
                total_tournaments = res_tournaments if res_tournaments else 0

                total_players_query = (
                    select(func.count(PlayerStanding.id))
                    .join(Tournament)
                    .where(Tournament.date >= start_date)
                    .where(Tournament.format.in_(allowed_formats))
                )
                res_players = session.exec(total_players_query).one_or_none()
                total_players = res_players if res_players else 0
        except Exception as e:
            # Fallback to 0 if database fails or is empty initially
            print(f"Error reading DB: {e}")

        return {
            "factions": snapshot.get("factions", []),
            "ships": snapshot.get("ships", []),
            "lists": enriched_lists,
            "pilots": snapshot.get("pilots", []),
            "upgrades": snapshot.get("upgrades", []),
            "last_sync": snapshot.get("last_sync", "Never"),
            "date_range": snapshot.get("date_range", "Unknown"),
            "total_tournaments": total_tournaments,
            "total_players": total_players,
        }

    cached = get_cached_or_compute(f"meta_snapshot|{ds_enum.value}|{epic}", compute)
    return MetaSnapshotResponse(**cached)
