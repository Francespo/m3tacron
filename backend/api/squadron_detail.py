from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import Session, select
from typing import List, Dict, Any

from ..database import engine
from ..models import PlayerResult, Tournament
from ..analytics.filters import filter_query, get_active_formats
from ..analytics.lists import aggregate_list_stats
from ..data_structures.data_source import DataSource
from .formatters import enrich_list_data
from .schemas import SquadronRow, SquadronPilotRow, ListData
from .filters import BaseFilterParams

router = APIRouter(prefix="/api/squadron", tags=["Squadron Detail"])

@router.get("/{signature:path}/stats", response_model=SquadronRow)
def get_squadron_stats(
    signature: str,
    filters: BaseFilterParams = Depends(),
):
    """Get aggregated statistics for a specific squadron signature."""
    with Session(engine) as session:
        query = select(PlayerResult, Tournament).where(
            PlayerResult.tournament_id == Tournament.id
        )
        query = filter_query(query, filters.model_dump())
        rows = session.exec(query).all()
        
        wins = 0
        games = 0
        count = 0
        faction = "Unknown"
        
        for result, tournament in rows:
            t_fmt_raw = tournament.format
            t_fmt = t_fmt_raw.value if hasattr(t_fmt_raw, 'value') else (t_fmt_raw or "other")
            
            allowed_fmt = get_active_formats(None)
            if allowed_fmt and t_fmt not in allowed_fmt:
                continue

            xws = result.list_json
            if not xws or not isinstance(xws, dict):
                continue
                
            pilots = xws.get("pilots", [])
            if not pilots: continue
            
            ships = sorted([p.get("ship") or "unknown" for p in pilots])
            sig = ", ".join(ships)
            
            if sig == signature or sig.replace(" ", "") == signature.replace(" ", ""):
                faction = xws.get("faction", faction)
                s_wins = result.swiss_wins or 0
                s_losses = result.swiss_losses or 0
                s_draws = result.swiss_draws or 0
                c_wins = result.cut_wins or 0
                c_losses = result.cut_losses or 0
                c_draws = result.cut_draws or 0
                
                wins += (s_wins + c_wins)
                games += (s_wins + c_wins + s_losses + s_draws + c_losses + c_draws)
                count += 1
                
        if games == 0:
            raise HTTPException(status_code=404, detail="Squadron not found or has no games")
            
        return SquadronRow(
            signature=signature,
            faction=faction,
            faction_xws=faction.lower().replace(" ", "").replace("-", ""),
            games=games,
            win_rate=round(wins / games * 100, 1) if games > 0 else 0.0,
            count=count,
            pilots=[]
        )

@router.get("/{signature:path}/pilots", response_model=List[SquadronPilotRow])
def get_squadron_pilots(
    signature: str,
    filters: BaseFilterParams = Depends(),
):
    """Get pilot breakdown for a specific squadron signature."""
    pilot_stats = {}
    total_games = 0
    
    with Session(engine) as session:
        query = select(PlayerResult, Tournament).where(
            PlayerResult.tournament_id == Tournament.id
        )
        query = filter_query(query, filters.model_dump())
        rows = session.exec(query).all()
        
        for result, tournament in rows:
            t_fmt_raw = tournament.format
            t_fmt = t_fmt_raw.value if hasattr(t_fmt_raw, 'value') else (t_fmt_raw or "other")
            
            allowed_fmt = get_active_formats(None)
            if allowed_fmt and t_fmt not in allowed_fmt:
                continue

            xws = result.list_json
            if not xws or not isinstance(xws, dict): continue
            pilots = xws.get("pilots", [])
            if not pilots: continue
            
            ships = sorted([p.get("ship") or "unknown" for p in pilots])
            sig = ", ".join(ships)
            
            if sig == signature or sig.replace(" ", "") == signature.replace(" ", ""):
                w = (result.swiss_wins or 0) + (result.cut_wins or 0)
                g = w + (result.swiss_losses or 0) + (result.swiss_draws or 0) + \
                    (result.cut_losses or 0) + (result.cut_draws or 0)
                
                total_games += g
                for p in pilots:
                    p_id = p.get("id") or p.get("name") or "unknown"
                    if p_id not in pilot_stats:
                        pilot_stats[p_id] = {
                            "pilot_xws": p_id,
                            "ship_xws": p.get("ship") or "unknown",
                            "name": p.get("name", p_id),
                            "cost": p.get("points", 0),
                            "games": 0,
                            "wins": 0
                        }
                    pilot_stats[p_id]["games"] += g
                    pilot_stats[p_id]["wins"] += w
                    
    results = []
    for p_id, stats in pilot_stats.items():
        w_g = stats["games"]
        win_rate = round(stats["wins"] / w_g * 100, 1) if w_g > 0 else 0.0
        percent_of_squadron = round(w_g / total_games * 100, 1) if total_games > 0 else 0.0
        
        results.append(SquadronPilotRow(
            pilot_xws=stats["pilot_xws"],
            ship_xws=stats["ship_xws"],
            name=stats["name"],
            cost=stats["cost"],
            games=w_g,
            win_rate=win_rate,
            percent_of_squadron=percent_of_squadron
        ))
        
    results.sort(key=lambda x: x.games, reverse=True)
    return results

@router.get("/{signature:path}/lists", response_model=List[ListData])
def get_squadron_lists(
    signature: str,
    filters: BaseFilterParams = Depends(),
):
    """Get top performing lists that use exactly this squadron signature."""
    try:
        ds_enum = DataSource(filters.data_source)
    except ValueError:
        ds_enum = DataSource.XWA
        
    all_lists = aggregate_list_stats(limit=1000, data_source=ds_enum)
    
    squadron_lists = []
    for l in all_lists:
        pilots = l.get("pilots", [])
        ships = sorted([p.get("ship") or "unknown" for p in pilots])
        sig = ", ".join(ships)
        
        if sig == signature or sig.replace(" ", "") == signature.replace(" ", ""):
            squadron_lists.append(enrich_list_data(l))
            
    squadron_lists.sort(key=lambda x: x.games, reverse=True)
    return squadron_lists[:20]
