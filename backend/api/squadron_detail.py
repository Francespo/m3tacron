from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select, func
from ..database import engine
from ..models import PlayerResult, Tournament
from ..analytics.filters import filter_query, get_active_formats
from ..analytics.lists import aggregate_list_stats
from ..data_structures.data_source import DataSource
from .formatters import enrich_list_data

router = APIRouter(prefix="/api/squadron", tags=["Squadron Detail"])

@router.get("/{signature:path}/stats")
def get_squadron_stats(
    signature: str,
    data_source: str = Query("xwa", description="Data source: xwa or legacy"),
    allowed_formats: str = Query(None, description="Comma-separated list of allowed formats")
):
    """
    Get aggregated statistics for a specific squadron signature.
    """
    filters = {"allowed_formats": allowed_formats}
    allowed_fmt = get_active_formats(allowed_formats)
    
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
        
        for result, tournament in rows:
            # Format filter optimization
            t_fmt_raw = tournament.format
            t_fmt = t_fmt_raw.value if hasattr(t_fmt_raw, 'value') else (t_fmt_raw or "other")
            
            if allowed_fmt and t_fmt not in allowed_fmt:
                continue

            xws = result.list_json
            if not xws or not isinstance(xws, dict):
                continue
                
            pilots = xws.get("pilots", [])
            if not pilots: continue
            
            ships = []
            for p in pilots:
                s_id = p.get("ship") or "unknown"
                ships.append(s_id)
            
            ships.sort()
            sig = ", ".join(ships)
            
            # Flexible matching (strip spaces/commas for comparison if needed, but start with exact)
            if sig == signature or sig.replace(" ", "") == signature.replace(" ", ""):
                faction = xws.get("faction", faction)
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
                
        if games == 0:
            raise HTTPException(status_code=404, detail="Squadron not found or has no games")
            
        return {
            "signature": signature,
            "faction": faction,
            "games": games,
            "wins": wins,
            "win_rate": round(wins / games * 100, 1),
            "popularity": count
        }

@router.get("/{signature:path}/pilots")
def get_squadron_pilots(
    signature: str,
    data_source: str = Query("xwa", description="Data source: xwa or legacy"),
    allowed_formats: str = Query(None, description="Comma-separated list of allowed formats")
):
    """
    Get pilot breakdown for a specific squadron signature.
    """
    filters = {"allowed_formats": allowed_formats}
    allowed_fmt = get_active_formats(allowed_formats)
    
    pilot_stats = {}
    total_games = 0
    
    with Session(engine) as session:
        query = select(PlayerResult, Tournament).where(
            PlayerResult.tournament_id == Tournament.id
        )
        query = filter_query(query, filters)
        rows = session.exec(query).all()
        
        for result, tournament in rows:
            t_fmt_raw = tournament.format
            t_fmt = t_fmt_raw.value if hasattr(t_fmt_raw, 'value') else (t_fmt_raw or "other")
            
            if allowed_fmt and t_fmt not in allowed_fmt:
                continue

            xws = result.list_json
            if not xws or not isinstance(xws, dict): continue
            pilots = xws.get("pilots", [])
            if not pilots: continue
            
            ships = [p.get("ship") or "unknown" for p in pilots]
            ships.sort()
            sig = ", ".join(ships)
            
            if sig == signature or sig.replace(" ", "") == signature.replace(" ", ""):
                s_wins = result.swiss_wins or 0
                s_losses = result.swiss_losses or 0
                s_draws = result.swiss_draws or 0
                c_wins = result.cut_wins or 0
                c_losses = result.cut_losses or 0
                c_draws = result.cut_draws or 0
                
                w = s_wins + c_wins
                g = w + s_losses + s_draws + c_losses + c_draws
                
                total_games += g
                
                # Each pilot in list gets stats
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
        
        results.append({
            "pilot_xws": stats["pilot_xws"],
            "ship_xws": stats["ship_xws"],
            "name": stats["name"],
            "cost": stats["cost"],
            "games": w_g,
            "win_rate": win_rate,
            "percent_of_squadron": percent_of_squadron
        })
        
    results.sort(key=lambda x: x["games"], reverse=True)
    return results

@router.get("/{signature:path}/lists")
def get_squadron_lists(
    signature: str,
    data_source: str = Query("xwa", description="Data source: xwa or legacy"),
    allowed_formats: str = Query(None, description="Comma-separated list of allowed formats")
):
    """
    Get top performing lists that use exactly this squadron signature.
    """
    try: ds_enum = DataSource(data_source)
    except: ds_enum = DataSource.XWA
    
    filters = {"allowed_formats": allowed_formats}
    all_lists = aggregate_list_stats(filters=filters, limit=1000, data_source=ds_enum)
    
    squadron_lists = []
    for l in all_lists:
        pilots = l.get("pilots", [])
        ships = [p.get("ship") or "unknown" for p in pilots]
        ships.sort()
        sig = ", ".join(ships)
        
        if sig == signature:
            squadron_lists.append(enrich_list_data(l, source=ds_enum))
            
    squadron_lists.sort(key=lambda x: x["games"], reverse=True)
    return squadron_lists[:20]
