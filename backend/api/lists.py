from fastapi import APIRouter, Query, Depends
from sqlmodel import Session, select, func
from typing import Optional, List
import json

from ..database import engine
from ..models import PlayerResult, Tournament
from ..data_structures.factions import Faction
from ..data_structures.formats import Format
from ..utils.squadron import get_list_signature
from ..utils.xwing_data.pilots import get_pilot_info
from ..utils.xwing_data.ships import get_ship_icon_name
from ..utils.xwing_data.upgrades import get_upgrade_info, get_upgrade_slot
from .schemas import PaginatedListsResponse, ListData, PilotData, UpgradeData

router = APIRouter(prefix="/api/lists", tags=["Lists"])

@router.get("", response_model=PaginatedListsResponse)
def get_lists(
    page: int = Query(0, ge=0),
    size: int = Query(20, ge=1, le=100),
    data_source: str = Query("xwa"),
    factions: Optional[List[str]] = Query(None),
    formats: Optional[List[int]] = Query(None),
    points_min: int = Query(0),
    points_max: int = Query(200),
    min_games: int = Query(0),
    loadout_min: int = Query(0),
    loadout_max: int = Query(50),
    sort_metric: str = Query("Games"),  # Games, Win Rate, Points Cost, Total Loadout
    sort_direction: str = Query("desc") # desc, asc
):
    with Session(engine) as session:
        query = select(PlayerResult, Tournament).where(PlayerResult.tournament_id == Tournament.id)
        
        # SQL Filters
        if formats:
            query = query.where(Tournament.format.in_(formats))
            
        rows = session.exec(query).all()
        
        list_signatures = {}
        
        for result, tournament in rows:
            xws = result.list_json
            if not xws or not isinstance(xws, dict):
                continue
                
            signature = get_list_signature(xws)
            if not signature:
                continue
                
            faction_xws = xws.get("faction", "unknown")
            if factions and faction_xws not in factions:
                continue
                
            points = xws.get("points")
            if points is None:
                points = 0
            if points < points_min:
                continue
            if points_max < 200 and points > points_max:
                continue
                
            if signature not in list_signatures:
                list_signatures[signature] = {
                    "faction": faction_xws,
                    "points": points,
                    "count": 0,
                    "games": 0,
                    "wins": 0,
                    "win_rate": 0.0,
                    "raw_xws": xws,
                    "total_loadout": 0
                }
                
            stats = list_signatures[signature]
            stats["count"] += 1
            
            # Loadout init
            if stats["total_loadout"] == 0 and data_source == "xwa":
                total_loadout = 0
                pilots_data = xws.get("pilots", [])
                for p in pilots_data:
                    pid = p.get("id") or p.get("name")
                    if not pid: continue
                    p_info = get_pilot_info(pid)
                    if p_info:
                        total_loadout += p_info.get("loadout", 0)
                stats["total_loadout"] = total_loadout
                
            # Filter Loadout
            if data_source == "xwa":
                if loadout_min > 0 and stats["total_loadout"] < loadout_min:
                    stats["count"] -= 1 # rollback
                    continue
                if loadout_max > 0 and stats["total_loadout"] > loadout_max:
                    stats["count"] -= 1
                    continue
                    
            games_played = 0
            wins = 0
            if result.swiss_rank and result.swiss_rank > 0:
                wins += result.swiss_wins if result.swiss_wins >= 0 else 0
                games_played += (result.swiss_wins or 0) + (result.swiss_losses or 0) + (result.swiss_draws or 0)
                if games_played == 0: games_played = 3
                
            stats["games"] += games_played
            stats["wins"] += wins

        final_list = []
        for sig, stats in list_signatures.items():
            if stats["games"] < min_games or stats["count"] == 0:
                continue
                
            win_rate = (stats["wins"] / stats["games"] * 100) if stats["games"] > 0 else 0.0
            
            raw_xws = stats["raw_xws"]
            pilots = raw_xws.get("pilots", [])
            rich_pilots = []
            
            for p in pilots:
                pid = p.get("id") or p.get("name")
                pilot_info = get_pilot_info(pid) or {}
                
                pilot_name = pilot_info.get("name", pid)
                ship_xws = pilot_info.get("ship_xws", "")
                ship_name = pilot_info.get("ship", "Unknown Ship")
                ship_icon_name = get_ship_icon_name(ship_xws)
                pilot_image = pilot_info.get("image") or ""
                pilot_points = p.get("points", pilot_info.get("cost", 0))
                
                rich_upgrades = []
                upgrades_data = p.get("upgrades", {})
                
                if isinstance(upgrades_data, dict):
                    for slot, items in upgrades_data.items():
                        if not isinstance(items, list): continue
                        for item_id in items:
                            upg_info = get_upgrade_info(item_id) or {}
                            norm_slot = slot.lower()
                            if norm_slot == "configuration": norm_slot = "config"
                            
                            raw_cost = upg_info.get("cost", {})
                            if isinstance(raw_cost, dict):
                                upg_points = raw_cost.get("value", 0)
                            else:
                                upg_points = raw_cost if isinstance(raw_cost, int) else 0

                            rich_upgrades.append(UpgradeData(
                                name=upg_info.get("name", item_id),
                                xws=item_id,
                                slot=norm_slot,
                                slot_icon="",
                                image=upg_info.get("image") or "",
                                points=upg_points
                            ))
                elif isinstance(upgrades_data, list):
                    for item_id in upgrades_data:
                        upg_info = get_upgrade_info(item_id) or {}
                        slot = get_upgrade_slot(item_id)
                        norm_slot = slot.lower()
                        if norm_slot == "configuration": norm_slot = "config"
                        
                        raw_cost = upg_info.get("cost", {})
                        if isinstance(raw_cost, dict):
                            upg_points = raw_cost.get("value", 0)
                        else:
                            upg_points = raw_cost if isinstance(raw_cost, int) else 0

                        rich_upgrades.append(UpgradeData(
                            name=upg_info.get("name", item_id),
                            xws=item_id,
                            slot=norm_slot,
                            slot_icon="",
                            image=upg_info.get("image") or "",
                            points=upg_points
                        ))
                
                rich_pilots.append(PilotData(
                    name=pilot_name,
                    xws=pid,
                    ship_name=ship_name,
                    ship_icon=ship_icon_name or "",
                    image=pilot_image,
                    points=pilot_points,
                    loadout=pilot_info.get("loadout", 0),
                    upgrades=rich_upgrades
                ))

            try:
                fac_label = Faction.from_xws(stats["faction"]).label
            except:
                fac_label = stats["faction"].capitalize()

            final_list.append(ListData(
                signature=sig,
                faction=fac_label,
                faction_key=stats["faction"],
                points=stats["points"],
                count=stats["count"],
                games=stats["games"],
                win_rate=round(win_rate, 1),
                total_loadout=stats["total_loadout"],
                pilots=rich_pilots
            ))

        # Sort
        reverse = sort_direction == "desc"
        if sort_metric == "Win Rate":
            final_list.sort(key=lambda x: x.win_rate, reverse=reverse)
        elif sort_metric == "Points Cost":
            final_list.sort(key=lambda x: x.points, reverse=reverse)
        elif sort_metric == "Total Loadout":
            final_list.sort(key=lambda x: sum(p.loadout for p in x.pilots), reverse=reverse)
        else:
            final_list.sort(key=lambda x: x.games, reverse=reverse)
            
        total = len(final_list)
        paginated_items = final_list[page * size : (page + 1) * size]
        
        return PaginatedListsResponse(
            items=paginated_items,
            total=total,
            page=page,
            size=size
        )
