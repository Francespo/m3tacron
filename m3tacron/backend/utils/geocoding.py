
import json
import time
import logging
import httpx
from pathlib import Path

# Assume we can import Location model, or return dicts if circular import is risky.
# For now, let's return a dict and let the caller create the Location object, 
# or import Location inside the function.
from ..data_structures.location import Location

logger = logging.getLogger(__name__)

CACHE_FILE = Path(__file__).parent.parent / "data" / "geocoding_cache.json"
CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)

# Nominatim requires a User-Agent
USER_AGENT = "M3taCronDataScraper/1.0" 
LAST_REQUEST_TIME = 0
MIN_DELAY_SECONDS = 1.1

# Country code to Continent mapping
COUNTRY_TO_CONTINENT = {
    # Europe
    "gb": "Europe", "uk": "Europe", "de": "Europe", "fr": "Europe", "it": "Europe",
    "es": "Europe", "pl": "Europe", "nl": "Europe", "be": "Europe", "at": "Europe",
    "ch": "Europe", "se": "Europe", "no": "Europe", "dk": "Europe", "fi": "Europe",
    "ie": "Europe", "pt": "Europe", "cz": "Europe", "hu": "Europe", "ro": "Europe",
    "gr": "Europe", "sk": "Europe", "bg": "Europe", "hr": "Europe", "si": "Europe",
    "ee": "Europe", "lv": "Europe", "lt": "Europe", "lu": "Europe", "mt": "Europe",
    "cy": "Europe", "is": "Europe", "rs": "Europe", "ua": "Europe", "by": "Europe",
    "md": "Europe", "al": "Europe", "mk": "Europe", "ba": "Europe", "me": "Europe",
    # North America
    "us": "North America", "ca": "North America", "mx": "North America",
    # South America
    "br": "South America", "ar": "South America", "cl": "South America", "co": "South America",
    "pe": "South America", "ve": "South America", "ec": "South America", "uy": "South America",
    # Asia
    "cn": "Asia", "jp": "Asia", "kr": "Asia", "in": "Asia", "sg": "Asia", "th": "Asia",
    "my": "Asia", "ph": "Asia", "id": "Asia", "vn": "Asia", "tw": "Asia", "hk": "Asia",
    "ae": "Asia", "il": "Asia", "sa": "Asia", "tr": "Asia", "ru": "Asia",
    # Oceania
    "au": "Oceania", "nz": "Oceania",
    # Africa
    "za": "Africa", "eg": "Africa", "ng": "Africa", "ke": "Africa", "ma": "Africa",
}

# Country code to full name mapping for common short codes
COUNTRY_CODE_TO_NAME = {
    "gb": "United Kingdom", "uk": "United Kingdom", "us": "United States",
    "de": "Germany", "fr": "France", "it": "Italy", "es": "Spain", "pl": "Poland",
    "nl": "Netherlands", "be": "Belgium", "at": "Austria", "ch": "Switzerland",
    "se": "Sweden", "no": "Norway", "dk": "Denmark", "fi": "Finland", "ie": "Ireland",
    "pt": "Portugal", "cz": "Czech Republic", "hu": "Hungary", "ro": "Romania",
    "gr": "Greece", "au": "Australia", "nz": "New Zealand", "ca": "Canada",
    "mx": "Mexico", "br": "Brazil", "ar": "Argentina", "jp": "Japan", "cn": "China",
    "kr": "South Korea", "in": "India", "sg": "Singapore", "ru": "Russia",
}

def _load_cache() -> dict:
    if CACHE_FILE.exists():
        try:
            return json.loads(CACHE_FILE.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}

def _save_cache(cache: dict):
    try:
        CACHE_FILE.write_text(json.dumps(cache, indent=2), encoding="utf-8")
    except Exception as e:
        logger.warning(f"Failed to save geocoding cache: {e}")

# In-memory cache loaded once
_GEO_CACHE = _load_cache()

def _get_continent_from_country(country: str | None) -> str | None:
    """Derive continent from country name or code."""
    if not country:
        return None
    
    country_lower = country.lower().strip()
    
    # Direct code lookup
    if country_lower in COUNTRY_TO_CONTINENT:
        return COUNTRY_TO_CONTINENT[country_lower]
    
    # Try to find by partial name match
    for code, continent in COUNTRY_TO_CONTINENT.items():
        full_name = COUNTRY_CODE_TO_NAME.get(code, "").lower()
        if full_name and full_name in country_lower:
            return continent
        if country_lower in full_name:
            return continent
    
    return None

def resolve_location(query: str) -> Location | None:
    """
    Resolve a location string to a structured Location using Nominatim.
    Uses local caching and throttling.
    Handles partial queries (e.g., "GB") and derives continent from country.
    """
    global LAST_REQUEST_TIME, _GEO_CACHE

    if not query or len(query.strip()) < 2:
        return None

    query = query.strip()
    
    # Explicit check for Online/Virtual events
    online_keywords = ["online", "virtual", "discord", "tts", "tabletop simulator", "vassal", "webcam"]
    if any(k in query.lower() for k in online_keywords):
        return Location.create(city="Virtual", country="Virtual", continent="Virtual")

    # Check Cache
    if query in _GEO_CACHE:
        cached = _GEO_CACHE[query]
        if cached is None: # Known failure
            return None
        return Location(**cached)

    # Handle very short queries (likely country codes like "GB")
    query_lower = query.lower().strip()
    if len(query_lower) <= 3 and query_lower in COUNTRY_TO_CONTINENT:
        country_name = COUNTRY_CODE_TO_NAME.get(query_lower, query.upper())
        continent = COUNTRY_TO_CONTINENT[query_lower]
        loc_dict = {"city": "Unknown", "country": country_name, "continent": continent}
        _GEO_CACHE[query] = loc_dict
        _save_cache(_GEO_CACHE)
        return Location.create(city="Unknown", country=country_name, continent=continent)

    # Throttle
    now = time.time()
    elapsed = now - LAST_REQUEST_TIME
    if elapsed < MIN_DELAY_SECONDS:
        time.sleep(MIN_DELAY_SECONDS - elapsed)
    
    LAST_REQUEST_TIME = time.time()

    try:
        # Call API
        url = "https://nominatim.openstreetmap.org/search"
        params = {
            "q": query,
            "format": "json",
            "addressdetails": 1,
            "limit": 1
        }
        headers = {"User-Agent": USER_AGENT}
        
        response = httpx.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()

        if not data:
            logger.info(f"Nominatim: No results for '{query}'")
            _GEO_CACHE[query] = None
            _save_cache(_GEO_CACHE)
            return None

        result = data[0]
        address = result.get("address", {})
        
        # Extract City
        city = address.get("city") or address.get("town") or address.get("village") or address.get("hamlet") or address.get("municipality")
        
        # Extract Country (prefer full name, fallback to code)
        country = address.get("country")
        country_code = address.get("country_code", "").lower()
        
        if not country and country_code:
            country = COUNTRY_CODE_TO_NAME.get(country_code, country_code.upper())
        
        # Derive Continent (from country code or Nominatim if available)
        continent = address.get("continent") or _get_continent_from_country(country_code) or _get_continent_from_country(country)
        
        # Validation
        if not city and not country:
            _GEO_CACHE[query] = None
            _save_cache(_GEO_CACHE)
            return None

        loc_dict = {
            "city": city or "Unknown",
            "country": country or "Unknown",
            "continent": continent or "Unknown"
        }
        
        _GEO_CACHE[query] = loc_dict
        _save_cache(_GEO_CACHE)
        
        return Location.create(city=loc_dict['city'], country=loc_dict['country'], continent=loc_dict.get('continent'))

    except Exception as e:
        logger.error(f"Geocoding error for '{query}': {e}")
        return None
