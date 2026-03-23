from fastapi import APIRouter, Query, HTTPException
from sqlmodel import Session, select, func
from ..database import engine
from ..models import Tournament, PlayerResult, Match
from ..data_structures.formats import Format
from ..data_structures.source import Source
from ..data_structures.factions import Faction
from .schemas import (
    PaginatedTournamentsResponse,
    TournamentData,
    TournamentDetailResponse,
    PlayerResultData,
    MatchData
)

router = APIRouter(prefix="/api/tournaments", tags=["Tournaments"])

def _get_location_string(location) -> str:
    loc_str = "Unknown Location"
    if location:
        parts = []
        if location.city: parts.append(location.city)
        if location.country: parts.append(location.country)
        # continent usually omitted if country present, but let's keep it simple
        
        # Deduplicate
        seen = set()
        unique_parts = [p for p in parts if not (p in seen or seen.add(p))]
        if unique_parts:
            loc_str = ", ".join(unique_parts)
    return loc_str

@router.get("/locations", response_model=dict[str, dict[str, list[str]]])
def get_locations():
    """
    Get all unique available locations structured as Continent -> Country -> list of Cities.
    """
    with Session(engine) as session:
        stmt = select(
            func.json_extract(Tournament.location, '$.continent').label('continent'),
            func.json_extract(Tournament.location, '$.country').label('country'),
            func.json_extract(Tournament.location, '$.city').label('city')
        ).distinct()
        
        rows = session.exec(stmt).all()
        
        locations = {}
        for row in rows:
            continent = row.continent or 'Unknown'
            country = row.country or 'Unknown'
            city = row.city or 'Unknown'
            
            if continent == 'Unknown' and country == 'Unknown' and city == 'Unknown':
                continue
                
            if continent not in locations:
                locations[continent] = {}
            if country not in locations[continent]:
                locations[continent][country] = set()
            if city != 'Unknown':
                locations[continent][country].add(city)
                
        # Convert sets to sorted lists
        result = {}
        for cont, countries in locations.items():
            result[cont] = {}
            for country, cities in sorted(countries.items()):
                result[cont][country] = sorted(list(cities))
                
        return result

@router.get("", response_model=PaginatedTournamentsResponse)
def get_tournaments(
    page: int = Query(0, ge=0),
    size: int = Query(20, ge=1, le=100),
    sort_metric: str = Query("Date"),
    sort_direction: str = Query("desc"),
    search: str | None = None,
    formats: list[str] | None = Query(None),
    sources: list[str] | None = Query(None), 
    continent: list[str] | None = Query(None),
    country: list[str] | None = Query(None),
    city: list[str] | None = Query(None),
    date_start: str | None = Query(None),
    date_end: str | None = Query(None),
    player_count_min: int | None = Query(None),
    player_count_max: int | None = Query(None),
):
    with Session(engine) as session:
        query = select(Tournament)
        
        if search:
            query = query.where(Tournament.name.ilike(f"%{search}%"))
        if formats:
            query = query.where(Tournament.format.in_(formats))
        if sources:
            query = query.where(Tournament.source.in_(sources))
        if continent:
            query = query.where(func.json_extract(Tournament.location, '$.continent').in_(continent))
        if country:
            query = query.where(func.json_extract(Tournament.location, '$.country').in_(country))
        if city:
            query = query.where(func.json_extract(Tournament.location, '$.city').in_(city))
        if date_start:
            query = query.where(Tournament.date >= date_start)
        if date_end:
            query = query.where(Tournament.date <= date_end)
        if player_count_min is not None:
            query = query.where(Tournament.player_count >= player_count_min)
        if player_count_max is not None:
            query = query.where(Tournament.player_count <= player_count_max)
            
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

            loc_str = _get_location_string(t.location)

            # Ensure valid format and platform enums
            fmt_str = t.format.lower() if t.format else "other"
            try:
                # Direct match first (for case sensitivity if StrEnum requires it)
                # StrEnum usually keeps case, let's try lower() if values are lower
                # Checking formats.py earlier, values were lowercase mostly: "amg", "xwa"
                fmt = Format(fmt_str)
            except ValueError:
                fmt = Format.OTHER

            src_str = t.source.lower() if t.source else "unknown"
            try:
                src = Source(src_str)
            except ValueError:
                src = Source.UNKNOWN

            items.append(TournamentData(
                id=t.id,
                name=t.name,
                date=t.date.strftime("%Y-%m-%d") if t.date else "Unknown",
                players=player_count,
                format=fmt,
                source=src,
                location=loc_str,
                url=t.url or ""
            ))
            
        return PaginatedTournamentsResponse(items=items, total=total, page=page, size=size)

@router.get("/{tournament_id}", response_model=TournamentDetailResponse)
def get_tournament_detail(tournament_id: int):
    from ..utils.xwing_data.parser import normalize_faction
    
    with Session(engine) as session:
        t = session.exec(select(Tournament).where(Tournament.id == tournament_id)).first()
        if not t:
            raise HTTPException(status_code=404, detail="Tournament not found")
            
        player_count = session.exec(select(func.count(PlayerResult.id)).where(PlayerResult.tournament_id == t.id)).one_or_none() or 0
        loc_str = _get_location_string(t.location)
        
        fmt_str = t.format.lower() if t.format else "other"
        try:
            fmt = Format(fmt_str)
        except ValueError:
            fmt = Format.OTHER

        src_str = t.source.lower() if t.source else "unknown"
        try:
            src = Source(src_str)
        except ValueError:
            src = Source.UNKNOWN

        t_data = TournamentData(
            id=t.id, 
            name=t.name, 
            date=t.date.strftime("%Y-%m-%d") if t.date else "Unknown",
            players=player_count, 
            format=fmt, 
            source=src, 
            location=loc_str, 
            url=t.url or ""
        )

        query_p = select(PlayerResult).where(PlayerResult.tournament_id == tournament_id).order_by(PlayerResult.swiss_rank)
        all_results = session.exec(query_p).all()
        
        players_swiss = []
        players_cut = []
        
        for p in all_results:
            raw_faction = p.list_json.get("faction", "Unknown") if p.list_json and isinstance(p.list_json, dict) else "Unknown"
            f_xws = normalize_faction(raw_faction)
            
            try:
                faction_enum = Faction(f_xws)
            except ValueError:
                faction_enum = Faction.UNKNOWN
            
            has_list = bool(p.list_json and isinstance(p.list_json, dict) and p.list_json.get("pilots"))
            
            p_res = PlayerResultData(
                id=p.id,
                name=p.player_name,
                rank=p.swiss_rank if p.swiss_rank is not None else 0,
                swiss_rank=p.swiss_rank if p.swiss_rank is not None else 0,
                cut_rank=p.cut_rank,
                wins=(p.swiss_wins or 0) + (p.cut_wins or 0),
                losses=(p.swiss_losses or 0) + (p.cut_losses or 0),
                faction=faction_enum,
                list_json=p.list_json if has_list else None
            )
            
            players_swiss.append(p_res)
            if p.cut_rank is not None:
                p_cut = p_res.copy()
                p_cut.rank = p.cut_rank
                players_cut.append(p_cut)
                
        players_swiss.sort(key=lambda x: x.swiss_rank)
        players_cut.sort(key=lambda x: x.cut_rank)
        
        matches_db = session.exec(select(Match).where(Match.tournament_id == tournament_id).order_by(Match.round_number)).all()
        player_map = {p.id: p.player_name for p in all_results}
        
        matches = [MatchData(
            round=m.round_number or 0,
            type=m.round_type or "",
            player1=player_map.get(m.player1_id, "Unknown"),
            player2=player_map.get(m.player2_id, "Bye") if not m.is_bye else "BYE",
            score1=m.player1_score or 0,
            score2=m.player2_score or 0,
            winner_id=m.winner_id,
            scenario=m.scenario or ""
        ) for m in matches_db]
        
        return TournamentDetailResponse(
            tournament=t_data,
            players_swiss=players_swiss,
            players_cut=players_cut,
            matches=matches
        )
