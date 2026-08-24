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
    # from key, see backend/api/ships.py). Warm 4 combos: xwa/legacy x epic.
    for ds in ("xwa", "legacy"):
        for epic in ("", "&epic=true"):
            endpoints.append(f"ships?page=0&size=21&sort_metric=Lists&sort_direction=desc&data_source={ds}{epic}")
    # Lists page 0 — 4 combos. page/size/sort excluded from cache key, so
    # page 1..9 are already warm if page 0 is.
    for ds in ("xwa", "legacy"):
        for epic in ("", "&epic=true"):
            endpoints.append(f"lists?page=0&size=20&sort_metric=Games&sort_direction=desc&min_games=3&data_source={ds}{epic}")
    # Squadrons page 0 — 4 combos (same page-excluded caching)
    for ds in ("xwa", "legacy"):
        for epic in ("", "&epic=true"):
            endpoints.append(f"squadrons?page=0&size=20&sort_metric=Games&sort_direction=desc&data_source={ds}{epic}")
    # Tournaments page 0 — 2 entries (tournaments key DOES include page, but
    # only page 0 is warmed; page 1..4 are on-demand ~80ms each).
    for ds in ("xwa", "legacy"):
        endpoints.append(f"tournaments?page=0&size=20&sort_metric=Date&sort_direction=desc&data_source={ds}")
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
    from .analytics.precompute import get_snapshot
    from .data_structures.data_source import DataSource

    for ds in (DataSource.XWA, DataSource.LEGACY):
        t0 = _t.time()
        try:
            snap = get_snapshot(ds)
            n_upg = sum(len(v) for f, v in snap["pilot_upgrades"].items() if f == ds.value)
            print(f"[prewarm] detail snapshot {ds.value}: {_t.time() - t0:.1f}s ✓ "
                  f"(header {len(snap['header'])} pilots, upg keys {n_upg})")
        except Exception as e:
            print(f"[prewarm] detail snapshot {ds.value}: FAILED ({e})")


def _warm_ship_details(base: str = "http://127.0.0.1:8888") -> None:
    """Prewarm all ship detail pages (xwa/legacy × epic × 4 endpoints) in parallel.

    Each ship has 4 endpoints: /ship/{xws}, /{xws}/pilots, /{xws}/lists, /{xws}/squadrons
    All are cached via get_cached_or_compute with key ship_*|{xws}|ds|...|epic
    Sequential would be ~320 ships × 0.3s = ~100s; parallel with 8 workers ~12s.
    This is the most impactful warm for perceived navigability: click on a ship
    in /ships otherwise pays 1-2.5s cold for 4 parallel GROUP BYs.
    Controlled by env SHIP_DETAIL_WARM (default true) and SHIP_DETAIL_WARM_WORKERS.
    """
    import time as _t
    import urllib.request
    import urllib.error
    from concurrent.futures import ThreadPoolExecutor, as_completed

    if os.getenv("SHIP_DETAIL_WARM", "true").lower() != "true":
        print("[prewarm] ship details: skipped (SHIP_DETAIL_WARM=false)")
        return

    try:
        from .utils.xwing_data.ships import load_all_ships
        from .data_structures.data_source import DataSource
    except Exception as e:
        print(f"[prewarm] ship details: FAILED to load ship list ({e})")
        return

    # Collect unique ship xws across both data sources
    all_xws: set[str] = set()
    for ds in (DataSource.XWA, DataSource.LEGACY):
        try:
            all_xws.update(load_all_ships(ds).keys())
        except Exception:
            pass

    if not all_xws:
        print("[prewarm] ship details: no ships found")
        return

    workers = int(os.getenv("SHIP_DETAIL_WARM_WORKERS", "4"))
    endpoints = ["", "/pilots", "/lists?limit=10", "/squadrons?limit=10"]
    # 4 combos: xwa/xwa+epic/legacy/legacy+epic — but pilot/lists/squadrons
    # also vary by epic param. Warm all 4.
    combos = [
        ("xwa", ""),
        ("xwa", "&epic=true"),
        ("legacy", ""),
        ("legacy", "&epic=true"),
    ]

    # Build URL list
    urls: list[str] = []
    for xws in sorted(all_xws):
        for ds, epic_qs in combos:
            for ep in endpoints:
                # ep already contains ?limit, so append &data_source
                sep = "&" if "?" in ep else "?"
                urls.append(f"{base}/api/ship/{xws}{ep}{sep}data_source={ds}{epic_qs}")

    t0 = _t.time()
    ok = 0
    fail = 0

    def fetch_one(url: str) -> bool:
        try:
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=30) as resp:
                resp.read()  # consume
            return True
        except Exception:
            return False

    # Bound concurrency to avoid overwhelming the DB pool (default 8)
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(fetch_one, u): u for u in urls}
        for fut in as_completed(futures):
            if fut.result():
                ok += 1
            else:
                fail += 1

    elapsed = _t.time() - t0
    print(f"[prewarm] ship details: {ok} ok, {fail} fail in {elapsed:.1f}s ({len(all_xws)} ships × 4 combos × 4 endpoints, {workers} workers) ✓")


def _probe_warm_endpoints(base: str, endpoints: list[str]) -> None:
    """Sequentially GET each endpoint; logs timing or failure."""
    import urllib.request
    import json

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
        except Exception as e:
            print(f"[prewarm] {name}: FAILED ({e})")


def _prewarm_cache():
    """Hit the API endpoints via HTTP so cache keys exactly match what users request.

    Runs in a daemon thread so startup returns immediately. Uses internal
    HTTP requests (no external port needed) via the same uvicorn worker.
    Also eagerly builds the card-detail snapshots (xwa + legacy) so detail pages
    are warm on first visit, and all ship detail pages (xwa/legacy × epic).
    """
    import threading

    def _run():
        time.sleep(1.5)  # wait for uvicorn to finish binding
        _warm_detail_snapshots()
        _probe_warm_endpoints("http://127.0.0.1:8888", _warm_endpoint_list())
        _warm_ship_details("http://127.0.0.1:8888")
        print("[prewarm] done")

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
                    _warm_detail_snapshots()
                    _probe_warm_endpoints("http://127.0.0.1:8888", _warm_endpoint_list())
                    _warm_ship_details("http://127.0.0.1:8888")
                    print("[auto-rewarm] done")
                    last_seen = cur
                elif cur is not None:
                    last_seen = cur
            except Exception as e:
                # Never kill the daemon; log and continue polling.
                print(f"[auto-rewarm] poll error: {e}")

    thread = threading.Thread(target=_loop, daemon=True, name="cache-auto-rewarm")
    thread.start()


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
