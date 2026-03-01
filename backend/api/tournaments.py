from fastapi import APIRouter, Query, Depends
from sqlmodel import Session, select, func
from typing import Optional, List
import json

from ..database import engine
from ..models import Tournament, PlayerResult
from ..data_structures.formats import Format
from ..data_structures.platforms import Platform
from .schemas import PaginatedTournamentsResponse, TournamentRow

router = APIRouter(prefix="/api/tournaments", tags=["Tournaments"])

def _split_format_badge(format_label: str) -> tuple[str, str]:
    """Helper to split format label into 2 short rows for the square badge"""
    label = format_label.upper() if format_label else "UNK"
    
    if "STANDARD" in label:
        label = label.replace("STANDARD", "").strip()
    if "EXTENDED" in label:
        label = label.replace("EXTENDED", "").strip()
    
    if label == "AMG": return "AMG", ""
    if label == "XWA": return "XWA", ""
    if "LEGACY (X2PO)" in label:
        return "LGCY", "X2PO"
    if "LEGACY (XLC)" in label:
        return "LGCY", "XLC"
    if "LEGACY" in label: 
        return "LGCY", "2.0"
    if "FFG" in label:
        return "FFG", "2.0"
    if "WILD" in label:
        return "WILD", "CARD"
    if "EPIC" in label:
        return "EPIC", "PLAY"
        
    words = label.split()
    if len(words) >= 2:
        return words[0][:4], words[1][:4]
    
    if len(label) > 4:
        return label[:4], label[4:8]
        
    return label, ""

@router.get("", response_model=PaginatedTournamentsResponse)
def get_tournaments(
    page: int = Query(0, ge=0),
    size: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    format: Optional[List[int]] = Query(None),
):
    with Session(engine) as session:
        query = select(Tournament).order_by(Tournament.date.desc())
        
        if search:
            query = query.where(Tournament.name.ilike(f"%{search}%"))
        if format:
            query = query.where(Tournament.format.in_(format))
            
        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total = session.exec(count_query).one()
        
        # Paginate
        query = query.offset(page * size).limit(size)
        results = session.exec(query).all()
        
        items = []
        for t in results:
            player_count = t.player_count
            if player_count == 0:
                player_count = session.exec(
                    select(func.count(PlayerResult.id)).where(PlayerResult.tournament_id == t.id)
                ).one_or_none() or 0

            # Format Location
            loc_str = "Unknown Location"
            if t.location:
                # Need to handle JSON dict of location
                try:
                    loc_dict = json.loads(t.location) if isinstance(t.location, str) else t.location
                    parts = []
                    if "city" in loc_dict and loc_dict["city"]: parts.append(loc_dict["city"])
                    if "country" in loc_dict and loc_dict["country"]: parts.append(loc_dict["country"])
                    if "continent" in loc_dict and loc_dict["continent"]: parts.append(loc_dict["continent"])
                    
                    seen = set()
                    unique_parts = []
                    for p in parts:
                        if p not in seen:
                            unique_parts.append(p)
                            seen.add(p)
                            
                    if unique_parts:
                        loc_str = ", ".join(unique_parts)
                except:
                    loc_str = str(t.location)

            # Format Badge
            f_label = Format(t.format).label if t.format in {f.value for f in Format} else (t.format or "Other")
            b1, b2 = _split_format_badge(f_label)

            platform_label = Platform(t.platform).label if t.platform in Platform._value2member_map_ else str(t.platform)

            items.append(
                TournamentRow(
                    id=t.id,
                    name=t.name,
                    date=t.date.strftime("%Y-%m-%d") if t.date else "Unknown",
                    players=player_count,
                    format_label=f_label,
                    badge_l1=b1,
                    badge_l2=b2,
                    platform_label=platform_label,
                    location=loc_str,
                    url=t.url or ""
                )
            )

        return PaginatedTournamentsResponse(
            items=items,
            total=total,
            page=page,
            size=size
        )
