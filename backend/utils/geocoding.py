
import json
import time
import logging
import httpx
import re
import unicodedata
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
    "py": "South America", "bo": "South America", "gy": "South America",
    # Asia
    "cn": "Asia", "jp": "Asia", "kr": "Asia", "in": "Asia", "sg": "Asia", "th": "Asia",
    "my": "Asia", "ph": "Asia", "id": "Asia", "vn": "Asia", "tw": "Asia", "hk": "Asia",
    "ae": "Asia", "il": "Asia", "sa": "Asia", "tr": "Asia", "ru": "Asia",
    "pk": "Asia", "bd": "Asia", "lk": "Asia", "np": "Asia", "kh": "Asia", "la": "Asia",
    "mm": "Asia", "kz": "Asia", "uz": "Asia", "qa": "Asia", "kw": "Asia", "bh": "Asia",
    "om": "Asia", "jo": "Asia", "lb": "Asia", "ir": "Asia", "iq": "Asia", "af": "Asia",
    "mn": "Asia", "ge": "Asia", "am": "Asia", "az": "Asia",
    # Oceania
    "au": "Oceania", "nz": "Oceania", "fj": "Oceania", "pg": "Oceania",
    # Africa
    "za": "Africa", "eg": "Africa", "ng": "Africa", "ke": "Africa", "ma": "Africa",
    "gh": "Africa", "tz": "Africa", "et": "Africa", "ug": "Africa", "dz": "Africa",
    "tn": "Africa", "ci": "Africa", "cm": "Africa", "zm": "Africa", "zw": "Africa",
    "mw": "Africa", "mz": "Africa", "na": "Africa", "bw": "Africa", "sn": "Africa",
    "rw": "Africa", "sd": "Africa", "ly": "Africa", "mg": "Africa", "ao": "Africa",
    "cd": "Africa", "bf": "Africa", "ml": "Africa", "ne": "Africa", "tg": "Africa",
    "bj": "Africa", "gm": "Africa", "gn": "Africa", "sl": "Africa", "lr": "Africa",
    "mr": "Africa", "so": "Africa", "er": "Africa", "dj": "Africa", "cf": "Africa",
    "ga": "Africa", "gq": "Africa", "cg": "Africa", "td": "Africa", "ss": "Africa",
    # Caribbean / Central America (map to North America for simplicity)
    "cu": "North America", "do": "North America", "jm": "North America",
    "ht": "North America", "tt": "North America", "bs": "North America",
    "bb": "North America", "bz": "North America", "cr": "North America",
    "gt": "North America", "hn": "North America", "ni": "North America",
    "pa": "North America", "sv": "North America", "pr": "North America",
    "gd": "North America", "lc": "North America", "vc": "North America",
    "kn": "North America", "ag": "North America", "dm": "North America",
}

# Continent aliases that sometimes appear in partial location strings.
CONTINENT_ALIASES = {
    "north america": "North America",
    "south america": "South America",
    "central america": "North America",
    "europe": "Europe",
    "asia": "Asia",
    "oceania": "Oceania",
    "australia": "Oceania",
    "africa": "Africa",
    "antarctica": "Antarctica",
}


def _continent_from_region(text: str | None) -> str | None:
    """Extract a continent from a partial region string.

    Handles Rollbetter-style strings such as "North America: Eastern",
    "Europe: Central", a bare "Asia", or multi-line metadata that contains a
    region line among other text. Returns the canonical continent name or
    None.
    """
    if not text:
        return None
    low = text.lower().strip()
    # Scan each line AND the whole string: the region may sit on its own
    # line inside a multi-line metadata block.
    for chunk in [low, *low.splitlines()]:
        # Take the part before ':' (e.g. "North America: Eastern" -> "North America")
        region = chunk.split(":")[0].strip()
        for alias, canonical in CONTINENT_ALIASES.items():
            if region == alias or region.startswith(alias) or alias in region:
                return canonical
    return None


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
    "ua": "Ukraine", "tr": "Turkey", "il": "Israel", "sa": "Saudi Arabia",
    "ae": "United Arab Emirates", "za": "South Africa", "eg": "Egypt",
    "ng": "Nigeria", "ke": "Kenya", "th": "Thailand", "vn": "Vietnam",
    "tw": "Taiwan", "ph": "Philippines", "my": "Malaysia", "id": "Indonesia",
    "pk": "Pakistan", "bd": "Bangladesh", "cl": "Chile", "co": "Colombia",
    "pe": "Peru", "ve": "Venezuela", "ec": "Ecuador", "uy": "Uruguay",
    "cz": "Czech Republic", "sk": "Slovakia", "si": "Slovenia", "hr": "Croatia",
    "rs": "Serbia", "bg": "Bulgaria", "ro": "Romania", "lt": "Lithuania",
    "lv": "Latvia", "ee": "Estonia", "is": "Iceland", "ie": "Ireland",
    "cy": "Cyprus", "mt": "Malta", "lu": "Luxembourg", "kr": "South Korea",
    "hk": "Hong Kong", "kz": "Kazakhstan", "ge": "Georgia", "am": "Armenia",
    "az": "Azerbaijan", "qa": "Qatar", "kw": "Kuwait", "bh": "Bahrain",
    "om": "Oman", "jo": "Jordan", "lb": "Lebanon", "ir": "Iran", "iq": "Iraq",
    "af": "Afghanistan", "mn": "Mongolia", "np": "Nepal", "lk": "Sri Lanka",
    "mm": "Myanmar", "kh": "Cambodia", "la": "Laos", "fj": "Fiji",
    "pg": "Papua New Guinea", "gh": "Ghana", "tz": "Tanzania", "et": "Ethiopia",
    "ug": "Uganda", "dz": "Algeria", "tn": "Tunisia", "ma": "Morocco",
    "ci": "Ivory Coast", "cm": "Cameroon", "zm": "Zambia", "zw": "Zimbabwe",
    "mw": "Malawi", "mz": "Mozambique", "na": "Namibia", "bw": "Botswana",
    "sn": "Senegal", "rw": "Rwanda", "sd": "Sudan", "ly": "Libya",
    "mg": "Madagascar", "ao": "Angola", "cu": "Cuba", "do": "Dominican Republic",
    "jm": "Jamaica", "ht": "Haiti", "tt": "Trinidad and Tobago",
    "bs": "Bahamas", "bb": "Barbados", "bz": "Belize", "cr": "Costa Rica",
    "gt": "Guatemala", "hn": "Honduras", "ni": "Nicaragua", "pa": "Panama",
    "sv": "El Salvador", "pr": "Puerto Rico", "py": "Paraguay", "bo": "Bolivia",
    "gy": "Guyana", "md": "Moldova", "al": "Albania", "mk": "North Macedonia",
    "ba": "Bosnia and Herzegovina", "me": "Montenegro", "by": "Belarus",
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

    # Common country-name aliases that Nominatim / the scrapers may return.
    COUNTRY_ALIASES = {
        "brasil": "br", "brazil": "br", "usa": "us",
        "united states of america": "us", "america": "us",
        "uk": "gb", "united kingdom": "gb", "england": "gb",
        "south korea": "kr", "korea": "kr", "russia": "ru",
        "czechia": "cz", "turkiye": "tr", "viet nam": "vn",
        "taiwan": "tw", "hong kong": "hk", "uae": "ae",
        "saudi arabia": "sa", "the netherlands": "nl", "holland": "nl",
    }
    if country_lower in COUNTRY_ALIASES:
        code = COUNTRY_ALIASES[country_lower]
        return COUNTRY_TO_CONTINENT.get(code)

    # Try to find by partial name match
    for code, continent in COUNTRY_TO_CONTINENT.items():
        full_name = COUNTRY_CODE_TO_NAME.get(code, "").lower()
        if full_name and full_name in country_lower:
            return continent
        if country_lower in full_name:
            return continent

    # "Country: Region" pattern (e.g. "United States: East Coast")
    if ":" in country_lower:
        before_colon = country_lower.split(":")[0].strip()
        if before_colon and before_colon != country_lower:
            return _get_continent_from_country(before_colon)

    return None


def _normalize_query(query: str) -> str:
    """Normalize queries by stripping accents and collapsing whitespace."""
    normalized = unicodedata.normalize("NFKD", query)
    ascii_query = normalized.encode("ascii", "ignore").decode("ascii")
    return re.sub(r"\s+", " ", ascii_query).strip()


def _dedupe_candidates(candidates: list[str]) -> list[str]:
    seen = set()
    ordered = []
    for item in candidates:
        key = item.lower()
        if key in seen:
            continue
        seen.add(key)
        ordered.append(item)
    return ordered


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
    normalized_query = _normalize_query(query)
    has_non_ascii = any(ord(ch) > 127 for ch in query)

    # Explicit check for Online/Virtual events
    online_keywords = ["online", "virtual", "discord",
                       "tts", "tabletop simulator", "vassal", "webcam"]
    if any(k in query.lower() for k in online_keywords):
        return Location.create(city="Virtual", country="Virtual", continent="Virtual")

    # Check Cache — skip if any field is "Unknown" so we re-attempt with the API
    if query in _GEO_CACHE:
        cached = _GEO_CACHE[query]
        if cached is None:
            return None
        if any(v == "Unknown" for v in cached.values()):
            logger.info(
                f"Geocoding cache has Unknown for '{query}', re-attempting API…")
        else:
            return Location(**cached)

    if normalized_query in _GEO_CACHE:
        cached = _GEO_CACHE[normalized_query]
        if cached is None:
            return None
        if any(v == "Unknown" for v in cached.values()):
            logger.info(
                f"Geocoding cache (normalized) has Unknown for '{normalized_query}', re-attempting API…")
        else:
            _GEO_CACHE[query] = cached
            return Location(**cached)

    # Build candidate queries (full -> normalized -> fallback segments)
    candidates = [query]
    if normalized_query and normalized_query != query:
        candidates.append(normalized_query)

    parts = [p.strip() for p in query.split(",") if p.strip()]
    if len(parts) > 1:
        for idx in range(1, len(parts)):
            candidate = ", ".join(parts[idx:]).strip()
            if candidate:
                candidates.append(candidate)
                if has_non_ascii:
                    normalized_candidate = _normalize_query(candidate)
                    if normalized_candidate != candidate:
                        candidates.append(normalized_candidate)

    candidates = _dedupe_candidates(candidates)

    # Manual Overrides for known problematic venues
    CUSTOM_OVERRIDES = {
        "torchlight": Location.create(city="Burlington", country="Canada", continent="North America"),
        "tts": Location.create(city="Virtual", country="Virtual", continent="Virtual"),
        "vassal": Location.create(city="Virtual", country="Virtual", continent="Virtual"),
    }

    for candidate in candidates:
        candidate_lower = candidate.lower().strip()

        # Handle region/continent-only strings ("North America: Eastern",
        # "Europe: Central", "Asia") — derive continent, no API needed.
        continent_region = _continent_from_region(candidate_lower)
        if continent_region and not any(
            ch.isdigit() for ch in candidate_lower
        ):
            loc_dict = {"city": "Unknown",
                        "country": "Unknown", "continent": continent_region}
            _GEO_CACHE[candidate] = loc_dict
            _GEO_CACHE[query] = loc_dict
            _save_cache(_GEO_CACHE)
            logger.info(
                f"Geocoding region-only: '{candidate}' -> {continent_region}")
            return Location.create(city="Unknown", country="Unknown", continent=continent_region)

        # Handle very short queries (likely country codes like "GB")
        if len(candidate_lower) <= 3 and candidate_lower in COUNTRY_TO_CONTINENT:
            country_name = COUNTRY_CODE_TO_NAME.get(
                candidate_lower, candidate.upper())
            continent = COUNTRY_TO_CONTINENT[candidate_lower]
            loc_dict = {"city": "Unknown",
                        "country": country_name, "continent": continent}
            _GEO_CACHE[candidate] = loc_dict
            _GEO_CACHE[query] = loc_dict
            _save_cache(_GEO_CACHE)
            return Location.create(city="Unknown", country=country_name, continent=continent)

        # Country-name-only (full or partial, e.g. "Germany", "United States",
        # "Brasil" → "Brazil") — derive continent without an API call.
        country_continent = _get_continent_from_country(candidate_lower)
        if country_continent and len(candidate_lower) > 3 and not any(
            ch.isdigit() for ch in candidate_lower
        ):
            country_name = candidate.strip()
            loc_dict = {"city": "Unknown",
                        "country": country_name, "continent": country_continent}
            _GEO_CACHE[candidate] = loc_dict
            _GEO_CACHE[query] = loc_dict
            _save_cache(_GEO_CACHE)
            logger.info(
                f"Geocoding country-only: '{candidate}' -> {country_name} ({country_continent})")
            return Location.create(city="Unknown", country=country_name, continent=country_continent)

        for key, loc in CUSTOM_OVERRIDES.items():
            if key in candidate_lower:
                logger.info(
                    f"Geocoding Override: '{candidate}' -> {loc.city}, {loc.country}")
                _GEO_CACHE[candidate] = loc.dict()
                _GEO_CACHE[query] = loc.dict()
                _save_cache(_GEO_CACHE)
                return loc

        # Throttle before any external call
        now = time.time()
        elapsed = now - LAST_REQUEST_TIME
        if elapsed < MIN_DELAY_SECONDS:
            time.sleep(MIN_DELAY_SECONDS - elapsed)
        LAST_REQUEST_TIME = time.time()

        try:
            # Call API
            url = "https://nominatim.openstreetmap.org/search"
            params = {
                "q": candidate,
                "format": "json",
                "addressdetails": 1,
                "limit": 1,
                "accept-language": "en",
            }
            headers = {"User-Agent": USER_AGENT}

            response = httpx.get(url, params=params,
                                 headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()

            if not data:
                logger.info(f"Nominatim: No results for '{candidate}'")
                continue

            result = data[0]
            address = result.get("address", {})

            # Extract City (Fallback to state/county/region)
            city = (address.get("city") or
                    address.get("town") or
                    address.get("village") or
                    address.get("hamlet") or
                    address.get("municipality") or
                    address.get("state") or
                    address.get("county") or
                    address.get("region"))

            # Extract Country (prefer full name, fallback to code)
            country = address.get("country")
            country_code = address.get("country_code", "").lower()

            if not country and country_code:
                country = COUNTRY_CODE_TO_NAME.get(
                    country_code, country_code.upper())

            # Derive Continent (from country code or Nominatim if available)
            continent = address.get("continent")
            if not continent:
                continent = _get_continent_from_country(country_code)
            if not continent and country:
                continent = _get_continent_from_country(country)

            # Fallback for known continents of major countries not in map/Nominatim
            if not continent and country_code in ["us", "ca", "mx"]:
                continent = "North America"

            # Validation - Relaxed: Accept if we have a Country, even if City is obscure
            if not country:
                if not city:
                    logger.warning(
                        f"Nominatim returned result but no City/Country for '{candidate}'")
                    continue

            loc_dict = {
                "city": city or "Unknown",
                "country": country or "Unknown",
                "continent": continent or "Unknown"
            }

            _GEO_CACHE[candidate] = loc_dict
            _GEO_CACHE[query] = loc_dict
            _save_cache(_GEO_CACHE)

            return Location.create(city=loc_dict['city'], country=loc_dict['country'], continent=loc_dict['continent'])

        except Exception as e:
            logger.error(f"Geocoding error for '{candidate}': {e}")
            continue

    return None
