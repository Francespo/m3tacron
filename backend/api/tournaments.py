from fastapi import APIRouter, Query
from typing import Optional, List
from sqlmodel import Session, select, func
from ..database import engine
from ..models import Tournament, PlayerResult
from ..data_structures.formats import Format
from ..data_structures.platforms import Platform
from .schemas import PaginatedTournamentsResponse, TournamentRow

router = APIRouter(prefix="/api/tournaments", tags=["Tournaments"])

def _split_format_badge(format_label: str) -> tuple[str, str]:
    label = format_label.upper() if format_label else "UNK"
    if "STANDARD" in label:
        label = label.replace("STANDARD", "").strip()
    if "EXTENDED" in label:
        label = label.replace("EXTENDED", "").strip()
    
    if label == "AMG": return "AMG", ""
    if label == "XWA": return "XWA", ""
    if "LEGACY (X2PO)" in label: return "LGCY", "X2PO"
    if "LEGACY (XLC)" in label: return "LGCY", "XLC"
    if "LEGACY" in label: return "LGCY", "2.0"
    if "FFG" in label: return "FFG", "2.0"
    if "WILD" in label: return "WILD", "CARD"
    if "EPIC" in label: return "EPIC", "PLAY"
        
    words = label.split()
    if len(words) >= 2: return words[0][:4], words[1][:4]
    if len(label) > 4: return label[:4], label[4:8]
    return label, ""

@router.get("", response_model=PaginatedTournamentsResponse)
def get_tournaments(
    page: int = Query(0, ge=0),
    size: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    formats: Optional[List[str]] = Query(None),
    continents: Optional[List[str]] = Query(None),
    countries: Optional[List[str]] = Query(None),
    cities: Optional[List[str]] = Query(None),
):
    with Session(engine) as session:
        query = select(Tournament).order_by(Tournament.date.desc())
        
        if search:
            query = query.where(Tournament.name.ilike(f"%{search}%"))
        if formats:
            query = query.where(Tournament.format.in_(formats))
        if continents:
            query = query.where(func.json_extract(Tournament.location, '$.continent').in_(continents))
        if countries:
            query = query.where(func.json_extract(Tournament.location, '$.country').in_(countries))
        if cities:
            query = query.where(func.json_extract(Tournament.location, '$.city').in_(cities))
            
        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total = session.exec(count_query).one()
        
        # Paginate
        results = session.exec(query.offset(page * size).limit(size)).all()
        
        items = []
        for t in results:
            player_count = t.player_count
            if player_count == 0:
                player_count = session.exec(
                    select(func.count(PlayerResult.id)).where(
                        PlayerResult.tournament_id == t.id
                    )
                ).one_or_none() or 0

            # Format Location
            loc_str = "Unknown Location"
            if t.location:
                parts = []
                if t.location.city: parts.append(t.location.city)
                if t.location.country: parts.append(t.location.country)
                if t.location.continent: parts.append(t.location.continent)
                seen = set()
                unique_parts = [p for p in parts if not (p in seen or seen.add(p))]
                if unique_parts:
                    loc_str = ", ".join(unique_parts)

            # Format Badge
            f_label = Format(t.format).label if t.format in {f.value for f in Format} else (t.format or "Other")
            b1, b2 = _split_format_badge(f_label)
            
            p_label = Platform(t.platform).label if t.platform in Platform._value2member_map_ else str(t.platform)

            items.append(TournamentRow(
                id=t.id,
                name=t.name,
                date=t.date.strftime("%Y-%m-%d") if t.date else "Unknown",
                players=player_count,
                format_label=f_label,
                badge_l1=b1,
                badge_l2=b2,
                platform_label=p_label,
                location=loc_str,
                url=t.url or ""
            ))
            
        return PaginatedTournamentsResponse(items=items, total=total, page=page, size=size)
