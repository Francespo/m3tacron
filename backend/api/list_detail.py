from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select, func
from ..database import engine
from ..models import PlayerResult, Tournament
from ..analytics.filters import filter_query, get_active_formats
from ..data_structures.data_source import DataSource
from .formatters import enrich_list_data

router = APIRouter(prefix="/api/list", tags=["List Detail"])

def get_list_key(xws):
    pilots = xws.get("pilots", [])
    pilot_list = []
    for p in pilots:
        p_id = p.get("id") or p.get("name") or "unknown"
        upgrades = []
        upgrade_data = p.get("upgrades", {})
        if isinstance(upgrade_data, dict):
            for slot, items in upgrade_data.items():
                if isinstance(items, list):
                    upgrades.extend([str(i) for i in items])
        elif isinstance(upgrade_data, list):
            upgrades.extend([str(i) for i in upgrade_data])
        
        upgrades.sort()
        pilot_list.append(f"{p_id}({','.join(upgrades)})")
    
    pilot_list.sort()
    return "|".join(pilot_list)

@router.get("/{list_id:path}/stats")
def get_list_stats(
    list_id: str,
    data_source: str = Query("xwa", description="Data source: xwa or legacy"),
    allowed_formats: str = Query(None, description="Comma-separated list of allowed formats")
):
    """
    Get aggregated statistics and full composition for a specific list.
    """
    filters = {"allowed_formats": allowed_formats}
    
    with Session(engine) as session:
        query = select(PlayerResult, Tournament).where(
            PlayerResult.tournament_id == Tournament.id
        )
        query = filter_query(query, filters)
        rows = session.exec(query).all()
        
        wins = 0
        games = 0
        count = 0
        faction = "Unknown"
        name = "Untitled List"
        pilots = []
        points = 0
        
        for result, tournament in rows:
            t_fmt_raw = tournament.format
            t_fmt = t_fmt_raw.value if hasattr(t_fmt_raw, 'value') else (t_fmt_raw or "other")
            
            allowed_fmt = get_active_formats(filters.get("allowed_formats", None))
            if allowed_fmt and t_fmt not in allowed_fmt:
                continue

            xws = result.list_json
            if not xws or not isinstance(xws, dict):
                continue
                
            sig = get_list_key(xws)
            list_name = xws.get("name", "")
            
            if sig == list_id or list_name == list_id:
                if count == 0:
                    faction = xws.get("faction", "unknown")
                    name = list_name or f"Untitled {faction} List"
                    pilots = xws.get("pilots", [])
                    points = xws.get("points", 0)
                    
                s_wins = result.swiss_wins or 0
                s_losses = result.swiss_losses or 0
                s_draws = result.swiss_draws or 0
                c_wins = result.cut_wins or 0
                c_losses = result.cut_losses or 0
                c_draws = result.cut_draws or 0
                
                w = s_wins + c_wins
                g = w + s_losses + s_draws + c_losses + c_draws
                
                wins += w
                games += g
                count += 1
                
        raw_stats = {
            "signature": list_id,
            "name": name,
            "faction": faction,
            "games": games,
            "wins": wins,
            "win_rate": round(wins / games * 100, 1) if games > 0 else 0.0,
            "popularity": count,
            "points": points,
            "pilots": pilots
        }
        
        try: ds_enum = DataSource(data_source)
        except: ds_enum = DataSource.XWA
        
        return enrich_list_data(raw_stats, source=ds_enum)
