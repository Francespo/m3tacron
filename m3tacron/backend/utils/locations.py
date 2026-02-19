"""
Location utility functions.
"""
from sqlmodel import Session, select, func
from sqlalchemy import distinct, cast, String
from ..database import engine
from ..models import Tournament
from ..data_structures.location import Location

def get_all_locations() -> dict[str, dict[str, list[str]]]:
    """
    Fetch all unique locations from tournaments and organize them hierarchically.
    
    Returns:
        dict: {
            "Continent Name": {
                "Country Name": ["City 1", "City 2", ...]
            }
        }
    """
    with Session(engine) as session:
        # Fetch all non-null locations
        # We fetch the whole object and process in Python for simplicity and DB-agnosticism
        # (SQLite JSON support varies by version/compilation)
        query = select(Tournament.location).where(Tournament.location.is_not(None))
        results = session.exec(query).all()
        
        hierarchy = {}
        
        for loc in results:
            if not loc or not isinstance(loc, Location):
                continue
                
            continent = loc.continent or "Unknown"
            country = loc.country or "Unknown"
            city = loc.city or "Unknown"
            
            if continent not in hierarchy:
                hierarchy[continent] = {}
            
            if country not in hierarchy[continent]:
                hierarchy[continent][country] = set()
            
            hierarchy[continent][country].add(city)
            
        # Convert sets to sorted lists
        final_hierarchy = {}
        for cont, countries in sorted(hierarchy.items()):
            final_hierarchy[cont] = {}
            for country, cities in sorted(countries.items()):
                final_hierarchy[cont][country] = sorted(list(cities))
                
        return final_hierarchy
