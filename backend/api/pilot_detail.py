from fastapi import APIRouter, Query, Depends
from .filters import BaseFilterParams
from ..analytics.core import aggregate_card_stats
from ..analytics.charts import get_card_usage_history
from ..data_structures.sorting_order import SortingCriteria, SortDirection
from ..data_structures.data_source import DataSource
from ..utils.xwing_data.pilots import load_all_pilots
from ..utils.xwing_data.upgrades import load_all_upgrades
from ..database import engine
from ..models import PlayerResult, Tournament
from sqlmodel import Session, select
from .schemas import (
    PilotInfo, PaginatedUpgradesResponse, CardChartResponse, 
    PilotConfigurationsResponse, PilotConfiguration, UpgradeRow
)

router = APIRouter(prefix="/api/pilot", tags=["Pilot Detail"])

@router.get("/{pilot_xws}", response_model=PilotInfo)
def get_pilot_info(
    pilot_xws: str,
    filters: BaseFilterParams = Depends(),
):
    ds = DataSource(filters.data_source) if filters.data_source in ("xwa", "legacy") else DataSource.XWA
    all_pilots = load_all_pilots(ds)
    info = all_pilots.get(pilot_xws, {"name": pilot_xws, "xws": pilot_xws, "image": ""})
    return PilotInfo(**info)

@router.get("/{pilot_xws}/upgrades", response_model=PaginatedUpgradesResponse)
def get_pilot_upgrades(
    pilot_xws: str,
    filters: BaseFilterParams = Depends(),
    sort_metric: str = Query("Popularity"),
    sort_direction: str = Query("desc"),
    upgrade_types: list[str] | None = Query(None),
):
    ds = DataSource(filters.data_source) if filters.data_source in ("xwa", "legacy") else DataSource.XWA
    criteria = SortingCriteria.from_label(sort_metric)
    direction = SortDirection(sort_direction)

    api_filters = {
        "allowed_formats": filters.formats,
        "search_text": filters.search_text,
        "upgrade_type": upgrade_types or [],
        "pilot_id": pilot_xws,
        "include_epic": False,
    }
    data = aggregate_card_stats(api_filters, criteria, direction, "upgrades", ds)
    total = len(data)
    items = data[filters.page * filters.size : (filters.page + 1) * filters.size]
    
    rows = [UpgradeRow(**item) for item in items]
    return PaginatedUpgradesResponse(items=rows, total=total, page=filters.page, size=filters.size)

@router.get("/{pilot_xws}/chart", response_model=CardChartResponse)
def get_pilot_chart(
    pilot_xws: str,
    filters: BaseFilterParams = Depends(),
    comparison: list[str] | None = Query(None),
):
    chart_data = get_card_usage_history(
        {"allowed_formats": filters.formats, "include_epic": False},
        pilot_xws,
        comparison or [],
        is_upgrade=False,
    )
    return CardChartResponse(data=chart_data, series=[pilot_xws] + (comparison or []))

@router.get("/{pilot_xws}/configurations", response_model=PilotConfigurationsResponse)
def get_pilot_configurations(
    pilot_xws: str,
    filters: BaseFilterParams = Depends(),
    limit: int = Query(10, ge=1, le=50),
):
    ds = DataSource(filters.data_source) if filters.data_source in ("xwa", "legacy") else DataSource.XWA
    all_upgrades = load_all_upgrades(ds)
    allowed = set(filters.formats) if filters.formats else None
    config_stats = {}

    with Session(engine) as session:
        query = select(PlayerResult, Tournament).where(PlayerResult.tournament_id == Tournament.id)
        rows = session.exec(query).all()
        for result, tournament in rows:
            t_fmt = tournament.format
            fmt_val = t_fmt.value if hasattr(t_fmt, "value") else (t_fmt or "other")
            if allowed and fmt_val not in allowed: continue
            xws = result.list_json
            if not xws or not isinstance(xws, dict): continue
            for p in xws.get("pilots", []):
                if (p.get("id") or p.get("name")) != pilot_xws: continue
                raw_upgrades = p.get("upgrades", {}) or {}
                upgrade_ids = []
                for slot_list in raw_upgrades.values(): upgrade_ids.extend(slot_list)
                upgrade_ids.sort()
                key = "|".join(upgrade_ids)
                if key not in config_stats:
                    config_stats[key] = {"upgrade_ids": upgrade_ids, "count": 0, "wins": 0}
                config_stats[key]["count"] += 1
                won = False
                if getattr(result, "winner", False): won = True
                elif getattr(result, "swiss_standing", 0) == 1: won = True
                if won: config_stats[key]["wins"] += 1

    sorted_configs = sorted(config_stats.values(), key=lambda x: x["count"], reverse=True)[:limit]
    results = []
    for cfg in sorted_configs:
        enriched_upgrades = []
        for uid in cfg["upgrade_ids"]:
            info = all_upgrades.get(uid, {})
            # We need to match UpgradeRow schema
            enriched_upgrades.append(UpgradeRow(
                name=info.get("name", uid),
                xws=uid,
                type=info.get("type", "unknown"),
                count=0, popularity=0, wins=0, games=0, lists=0,
                image=info.get("image", ""),
                cost=info.get("cost", 0) if isinstance(info.get("cost"), int) else 0,
                win_rate=0.0
            ))
        wr = round((cfg["wins"] / cfg["count"]) * 100, 1) if cfg["count"] > 0 else 0
        results.append(PilotConfiguration(
            upgrades=enriched_upgrades,
            count=cfg["count"],
            wins=cfg["wins"],
            win_rate=wr
        ))
    return PilotConfigurationsResponse(configurations=results, total=len(config_stats))
