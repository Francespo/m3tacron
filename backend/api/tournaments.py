from fastapi import APIRouter, Query
from typing import Optional, List
from sqlmodel import Session, select, func
from ..database import engine
from ..models import Tournament, PlayerResult
from ..data_structures.formats import Format
from ..data_structures.platforms import Platform
from .schemas import PaginatedTournamentsResponse, TournamentRow, TournamentDetailResponse

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
    sort_metric: str = Query("Date"),
    sort_direction: str = Query("desc"),
    search: Optional[str] = None,
    formats: Optional[List[str]] = Query(None),
    platforms: Optional[List[str]] = Query(None),
    continents: Optional[List[str]] = Query(None),
    countries: Optional[List[str]] = Query(None),
    cities: Optional[List[str]] = Query(None),
):
    with Session(engine) as session:
        query = select(Tournament)
        
        if search:
            query = query.where(Tournament.name.ilike(f"%{search}%"))
        if formats:
            query = query.where(Tournament.format.in_(formats))
        if platforms:
            query = query.where(Tournament.platform.in_(platforms))
        if continents:
            query = query.where(func.json_extract(Tournament.location, '$.continent').in_(continents))
        if countries:
            query = query.where(func.json_extract(Tournament.location, '$.country').in_(countries))
        if cities:
            query = query.where(func.json_extract(Tournament.location, '$.city').in_(cities))
            
        # Apply sorting
        if sort_metric == "Players":
            sort_attr = Tournament.player_count
        elif sort_metric == "Name":
            sort_attr = Tournament.name
        else: # Default to Date
            sort_attr = Tournament.date
            
        if sort_direction == "asc":
            query = query.order_by(sort_attr.asc())
        else:
            query = query.order_by(sort_attr.desc())
            
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

@router.get("/{tournament_id}", response_model=TournamentDetailResponse)
def get_tournament_detail(tournament_id: int):
    from fastapi import HTTPException
    from .schemas import TournamentDetailResponse, PlayerStandingsRow, MatchRow
    from ..models import Match
    from ..utils.xwing_data.parser import normalize_faction
    from ..utils.xwing_data.core import get_faction_name

    with Session(engine) as session:
        t = session.exec(select(Tournament).where(Tournament.id == tournament_id)).first()
        if not t:
            raise HTTPException(status_code=404, detail="Tournament not found")
            
        # Format the tournament matching PaginatedTournamentsResponse
        player_count = session.exec(select(func.count(PlayerResult.id)).where(PlayerResult.tournament_id == t.id)).one_or_none() or 0
        loc_str = "Unknown Location"
        if t.location:
            parts = []
            if t.location.city: parts.append(t.location.city)
            if t.location.country: parts.append(t.location.country)
            seen = set()
            unique_parts = [p for p in parts if not (p in seen or seen.add(p))]
            if unique_parts: loc_str = ", ".join(unique_parts)
            
        f_label = Format(t.format).label if t.format in {f.value for f in Format} else (t.format or "Other")
        b1, b2 = _split_format_badge(f_label)
        p_label = Platform(t.platform).label if t.platform in Platform._value2member_map_ else str(t.platform)
        
        t_row = TournamentRow(
            id=t.id, name=t.name, date=t.date.strftime("%Y-%m-%d") if t.date else "Unknown",
            players=player_count, format_label=f_label, badge_l1=b1, badge_l2=b2,
            platform_label=p_label, location=loc_str, url=t.url or ""
        )

        query_p = select(PlayerResult).where(PlayerResult.tournament_id == tournament_id).order_by(PlayerResult.swiss_rank)
        all_results = session.exec(query_p).all()
        
        players_swiss = []
        players_cut = []
        
        for p in all_results:
            raw_faction = p.list_json.get("faction", "Unknown") if p.list_json and isinstance(p.list_json, dict) else "Unknown"
            f_xws = normalize_faction(raw_faction)
            f_name = get_faction_name(f_xws)
            has_list = bool(p.list_json and isinstance(p.list_json, dict) and p.list_json.get("pilots"))
            
            p_dict = PlayerStandingsRow(
                id=p.id,
                name=p.player_name,
                rank=p.swiss_rank if p.swiss_rank is not None else 0,
                swiss_rank=p.swiss_rank if p.swiss_rank is not None else 0,
                cut_rank=p.cut_rank,
                wins=(p.swiss_wins or 0) + (p.cut_wins or 0),
                losses=(p.swiss_losses or 0) + (p.cut_losses or 0),
                faction=f_name,
                faction_xws=f_xws,
                has_list=has_list,
                list_json=p.list_json if has_list else None
            )
            
            players_swiss.append(p_dict)
            if p.cut_rank is not None:
                p_cut = p_dict.copy()
                p_cut.rank = p.cut_rank
                players_cut.append(p_cut)
                
        players_swiss.sort(key=lambda x: x.swiss_rank)
        players_cut.sort(key=lambda x: x.cut_rank)
        
        matches_db = session.exec(select(Match).where(Match.tournament_id == tournament_id).order_by(Match.round_number)).all()
        player_map = {p.id: p.player_name for p in all_results}
        
        matches = [MatchRow(
            round=str(m.round_number),
            type=m.round_type or "",
            player1=player_map.get(m.player1_id, "Unknown"),
            player2=player_map.get(m.player2_id, "Bye") if not m.is_bye else "BYE",
            player1_id=m.player1_id or 0,
            player2_id=m.player2_id or 0,
            score1=m.player1_score or 0,
            score2=m.player2_score or 0,
            winner_id=m.winner_id or 0,
            scenario=m.scenario or ""
        ) for m in matches_db]
        
        return TournamentDetailResponse(
            tournament=t_row,
            players_swiss=players_swiss,
            players_cut=players_cut,
            matches=matches
        )
