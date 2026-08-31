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
    try:
        from .cache import get_db_version, set_cached_version
        set_cached_version(get_db_version())
    except Exception as exc:
        print(f"[startup] initial set_cached_version failed: {exc}")

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

    Epic is always included site-wide (no epic param). Covers: dashboard
    (2 combos xwa/legacy), ships (2 combos, all pages via single aggregation
    page/size excluded), lists/squadrons page 0 (2 combos each), cards
    (4 combos), tournaments page 0 (1 entry). Total ~11 keys. Per-ship detail
    is warmed separately via _warm_ship_details() in-process.
    """
    endpoints: list[str] = [
        # Dashboard meta-snapshot (xwa + legacy, epic always on)
        "meta-snapshot?data_source=xwa",
        "meta-snapshot?data_source=legacy",
    ]
    # Lists page 0 — 2 combos (epic always on).
    for ds in ("xwa", "legacy"):
        endpoints.append(f"lists?page=0&size=20&sort_metric=Games&sort_direction=desc&min_games=3&data_source={ds}")
    # Squadrons page 0 — 2 combos (epic always on).
    for ds in ("xwa", "legacy"):
        endpoints.append(f"squadrons?page=0&size=20&sort_metric=Games&sort_direction=desc&data_source={ds}")
    # Tournaments page 0 — 1 entry.
    endpoints.append("tournaments?page=0&size=20&sort_metric=Date&sort_direction=desc")
    endpoints.extend([
        # Cards/Pilots - 2 combos (epic always on)
        "cards/pilots?page=0&size=20&sort_metric=Lists&sort_direction=desc&data_source=xwa",
        "cards/pilots?page=0&size=20&sort_metric=Lists&sort_direction=desc&data_source=legacy",
        # Cards/Upgrades - 2 combos (epic always on)
        "cards/upgrades?page=0&size=20&sort_metric=Lists&sort_direction=desc&data_source=xwa",
        "cards/upgrades?page=0&size=20&sort_metric=Lists&sort_direction=desc&data_source=legacy",
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
    """Bulk-prewarm all ship detail pages (xwa/legacy) **in-process**.

    Phase 1 (bulk, ~28s): 4 queries fan-out to 368 `ship_info` + `ship_pilots`
    keys so the header + pilot breakdown are instant on first paint.
    Phase 2 (per-ship, ~35s): prewarm `ship_lists` + `ship_squadrons` for
    all 92 ships × 2 DS so the below-fold Top Lists/Squadrons are also
    instant at build time and not on first user click. Total 736 keys.
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

    combos: list[DataSource] = [DataSource.XWA, DataSource.LEGACY]

    t0 = _t.time()
    ok = 0
    fail = 0

    # --- Bulk path: 4 queries total, then fan-out into 368 cache keys ---
    try:
        from backend.utils.xwing_data.pilots import load_all_pilots
    except Exception as e:
        print(f"[prewarm] ship details bulk: FAILED to load pilots ({e})")
        _warm_state["ship_details"] = {"error": str(e)}
        return

    # The detail page is reached from /ships which appends ?formats=xwa (or
    # legacy). That produces a different cache suffix than the bare
    # `formats=None` key. To make the first click fast regardless of format
    # filtering, fan-out into 3 suffixes per ship/DS: no-format + xwa + legacy.
    def _suffixes_for_ds(ds: DataSource) -> list[tuple[str, dict]]:
        base = _ship_filter_cache_suffix(
            formats=None, factions=None, ships=None, continent=None, country=None, city=None,
            platforms=None, sources=None, date_start=None, date_end=None,
            player_count_min=None, player_count_max=None, search=None, epic=False, faction=None,
        )
        xwa = _ship_filter_cache_suffix(
            formats=["xwa"], factions=None, ships=None, continent=None, country=None, city=None,
            platforms=None, sources=None, date_start=None, date_end=None,
            player_count_min=None, player_count_max=None, search=None, epic=False, faction=None,
        )
        legacy = _ship_filter_cache_suffix(
            formats=["legacy_x2po"], factions=None, ships=None, continent=None, country=None, city=None,
            platforms=None, sources=None, date_start=None, date_end=None,
            player_count_min=None, player_count_max=None, search=None, epic=False, faction=None,
        )
        return [(base, {"epic": True, "include_epic": True}), (xwa, {"epic": True, "include_epic": True, "allowed_formats": ["xwa"]}), (legacy, {"epic": True, "include_epic": True, "allowed_formats": ["legacy_x2po"]})]

    for ds in combos:
        # Phase 1: ship_info and ship_pilots per suffix
        for suffix, flt in _suffixes_for_ds(ds):
            try:
                bulk_ships = aggregate_ship_stats(flt, SortingCriteria.GAMES, SortDirection.DESCENDING, ds)
                by_xws = {s["xws"]: s for s in bulk_ships}
                for xws in sorted(all_xws):
                    cache_key = f"ship_info|{xws}|{ds.value}{suffix}"
                    val = by_xws.get(xws, {})
                    get_cached_or_compute(cache_key, lambda v=val: v, force=True)
                    ok += 1
            except Exception as e:
                print(f"[prewarm] ship info bulk {ds.value}{suffix}: FAILED ({e})")
                fail += len(all_xws)

            try:
                bulk_pilots = aggregate_card_stats(flt, SortingCriteria.LISTS, SortDirection.DESCENDING, "pilots", ds)
                pilots_map = load_all_pilots(ds)
                by_ship: dict[str, list[dict]] = {}
                for p in bulk_pilots:
                    p_xws = p.get("xws")
                    ship = pilots_map.get(p_xws, {}).get("ship_xws", "") if p_xws else ""
                    if not ship:
                        continue
                    by_ship.setdefault(ship, []).append(p)
                for xws in sorted(all_xws):
                    cache_key = f"ship_pilots|{xws}|{ds.value}|Lists|desc{suffix}"
                    val = by_ship.get(xws, [])
                    get_cached_or_compute(cache_key, lambda v=val: list(v), force=True)
                    ok += 1
            except Exception as e:
                print(f"[prewarm] ship pilots bulk {ds.value}{suffix}: FAILED ({e})")
                fail += len(all_xws)

            # Phase 2: lists and squadrons bulk partition per suffix
            try:
                bulk_lists = aggregate_list_stats(flt, data_source=ds)
                lists_by_ship: dict[str, list[dict]] = {}
                for item in bulk_lists:
                    sl = item.get("ship_list", "")
                    ships_in_list = sl.split(",") if isinstance(sl, str) else (sl if isinstance(sl, list) else [])
                    for s in set(ships_in_list):
                        if s:
                            lists_by_ship.setdefault(s, []).append(item)
                for xws in sorted(all_xws):
                    cache_key = f"ship_lists|{xws}|{ds.value}|10{suffix}"
                    val = lists_by_ship.get(xws, [])
                    get_cached_or_compute(cache_key, lambda v=val: list(v), force=True)
                    ok += 1
            except Exception as e:
                print(f"[prewarm] ship lists bulk {ds.value}{suffix}: FAILED ({e})")
                fail += len(all_xws)

            try:
                bulk_sq = aggregate_squadron_stats(flt, SortingCriteria.WINRATE, SortDirection.DESCENDING, ds)
                sq_by_ship: dict[str, list[dict]] = {}
                for item in bulk_sq:
                    sl = item.get("ship_list", "")
                    ships_in_sq = sl.split(",") if isinstance(sl, str) else (sl if isinstance(sl, list) else [])
                    for s in set(ships_in_sq):
                        if s:
                            sq_by_ship.setdefault(s, []).append(item)
                for xws in sorted(all_xws):
                    cache_key = f"ship_squadrons|{xws}|{ds.value}|10{suffix}"
                    val = sq_by_ship.get(xws, [])
                    get_cached_or_compute(cache_key, lambda v=val: list(v), force=True)
                    ok += 1
            except Exception as e:
                print(f"[prewarm] ship squadrons bulk {ds.value}{suffix}: FAILED ({e})")
                fail += len(all_xws)

    elapsed = _t.time() - t0
    total_keys = len(all_xws) * len(combos) * 3 * 4
    print(f"[prewarm] ship details bulk: {ok} ok, {fail} fail in {elapsed:.1f}s ({len(all_xws)} ships × 2 DS × 3 suffixes × 4 sections = {total_keys} keys) ✓")
    _warm_state["ship_details"] = {
        "ok": ok, "fail": fail, "elapsed_s": round(elapsed, 1),
        "total_urls": total_keys, "ships": len(all_xws), "workers": 1,
        "mode": "bulk",
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
            resp = urllib.request.urlopen(req, timeout=15)
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
    are warm on first visit, and all ship detail pages (xwa/legacy).
    Fix 2: sync the in-memory cache version after warm so the next request
    does not re-clear (the 2026-08-31 prod incident stayed at entries:0).
    """
    import threading

    def _run():
        import datetime as _dt
        t0 = time.time()
        time.sleep(1.5)  # wait for uvicorn to finish binding
        _warm_detail_snapshots()
        _warm_ship_details()
        _probe_warm_endpoints("http://127.0.0.1:8888", _warm_endpoint_list())
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
        # Sync the cache version and persist warm cache to disk
        try:
            from .cache import get_db_version, set_cached_version, save_cache
            set_cached_version(get_db_version())
            save_cache()
        except Exception as exc:
            print(f"[prewarm] set_cached_version / save_cache failed: {exc}")
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
                    # Seal the new version and persist to disk
                    try:
                        from .cache import set_cached_version, save_cache
                        set_cached_version(cur)
                        save_cache()
                    except Exception as exc:
                        print(f"[auto-rewarm] set_cached_version / save_cache failed: {exc}")
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
    from .cache import cache_stats as _cache_stats, MAX_CACHE_ENTRIES
    cs = _cache_stats()
    # _warm_state is populated by _prewarm_cache / _start_cache_auto_rewarm
    return {
        "cache": cs,
        "warm": dict(_warm_state),
        "config": {
            "warm_endpoints": len(_warm_endpoint_list()),
            "ship_detail_total_urls": 1472,  # 92 ships × 2 DS × 8 keys: info×3 + pilots×3 + lists + squadrons (epic always on)
            "max_cache_entries": MAX_CACHE_ENTRIES,
        },
    }


@app.get("/")
def read_root():
    return {"status": "Backend is running"}


@app.get("/api/meta-snapshot", response_model=MetaSnapshotResponse)
def get_snapshot(
    data_source: str = Query("xwa", description="Data source: xwa or legacy"),
    days: int | None = Query(90, description="Time window in days (7, 30, 90, 180, 365, or 0/None for all time)"),
    date_start: str | None = Query(None, description="Start date (YYYY-MM-DD)"),
    date_end: str | None = Query(None, description="End date (YYYY-MM-DD)"),
):
    ds_enum = DataSource.XWA if data_source == "xwa" else DataSource.LEGACY
    normalized_days = None if (days == 0 or days is None) else days
    if date_start:
        normalized_days = None

    def compute():
        # Source -> formats mapping. Epic content is always included.
        if ds_enum == DataSource.XWA:
            allowed_formats = ["xwa", "amg"]
        else:
            allowed_formats = ["legacy_x2po"]

        # Runs the 5 aggregations + 2 count queries. Cached by data_source + days + date range
        # (epic always on) so the dashboard only pays the cost once per data_version.
        from .api.formatters import enrich_list_data
        snapshot = get_meta_snapshot(
            ds_enum,
            allowed_formats=allowed_formats,
            include_epic=True,
            days_back=normalized_days,
            date_start=date_start,
            date_end=date_end,
        )

        # Enrich list data with pilot/ship metadata (names, ship icons,
        # pack captions, upgrade names) before serving to the dashboard.
        raw_lists = snapshot.get("lists", [])
        enriched_lists = [enrich_list_data(l, source=ds_enum) for l in raw_lists]

        total_tournaments = 0
        total_players = 0
        try:
            with Session(engine) as session:
                total_tournaments_query = (
                    select(func.count(Tournament.id))
                    .where(Tournament.format.in_(allowed_formats))
                )
                total_players_query = (
                    select(func.count(PlayerStanding.id))
                    .join(Tournament)
                    .where(Tournament.format.in_(allowed_formats))
                )

                if snapshot.get("date_start"):
                    s_date = datetime.strptime(snapshot["date_start"], "%Y-%m-%d").date()
                    total_tournaments_query = total_tournaments_query.where(Tournament.date >= s_date)
                    total_players_query = total_players_query.where(Tournament.date >= s_date)
                if snapshot.get("date_end"):
                    e_date = datetime.strptime(snapshot["date_end"], "%Y-%m-%d").date()
                    total_tournaments_query = total_tournaments_query.where(Tournament.date <= e_date)
                    total_players_query = total_players_query.where(Tournament.date <= e_date)

                res_tournaments = session.exec(total_tournaments_query).one_or_none()
                total_tournaments = res_tournaments if res_tournaments else 0

                res_players = session.exec(total_players_query).one_or_none()
                total_players = res_players if res_players else 0
        except Exception as e:
            print(f"Error reading DB: {e}")

        total_lists = 0
        total_games = 0
        try:
            factions = snapshot.get("factions", []) or []
            total_lists = sum(int(f.get("list_count", 0) or 0) for f in factions)
            total_games = sum(int(f.get("games_count", 0) or 0) for f in factions)
        except Exception:
            try:
                ships = snapshot.get("ships", []) or []
                total_lists = sum(int(s.get("list_count", 0) or 0) for s in ships)
                total_games = sum(int(s.get("games_count", 0) or 0) for s in ships)
            except Exception:
                total_lists = 0
                total_games = 0

        return {
            "factions": snapshot.get("factions", []),
            "ships": snapshot.get("ships", []),
            "lists": enriched_lists,
            "pilots": snapshot.get("pilots", []),
            "upgrades": snapshot.get("upgrades", []),
            "last_sync": snapshot.get("last_sync", "Never"),
            "date_range": snapshot.get("date_range", "Unknown"),
            "date_start": snapshot.get("date_start"),
            "date_end": snapshot.get("date_end"),
            "total_tournaments": total_tournaments,
            "total_players": total_players,
            "total_lists": total_lists,
            "total_games": total_games,
        }

    cached = get_cached_or_compute(
        f"meta_snapshot|{ds_enum.value}|True|{normalized_days}|{date_start or ''}|{date_end or ''}",
        compute,
    )
    return MetaSnapshotResponse(**cached)
