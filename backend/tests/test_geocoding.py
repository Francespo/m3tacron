"""Tests for geocoding region/continent handling."""
from backend.utils.geocoding import (
    _continent_from_region,
    _get_continent_from_country,
    resolve_location,
)


def test_continent_from_region():
    assert _continent_from_region("North America: Eastern") == "North America"
    assert _continent_from_region("Europe: Central") == "Europe"
    assert _continent_from_region("Asia") == "Asia"
    assert _continent_from_region("South America: Western") == "South America"
    assert _continent_from_region("Australia") == "Oceania"
    assert _continent_from_region(None) is None


def test_continent_from_region_multiline():
    meta = "\xa0X-Wing XWA\nX-Wing XWA Standard\n\xa0North America: Eastern\n\xa0In Person"
    assert _continent_from_region(meta) == "North America"


def test_continent_from_country():
    assert _get_continent_from_country("Germany") == "Europe"
    assert _get_continent_from_country("Brasil") == "South America"
    assert _get_continent_from_country("USA") == "North America"
    assert _get_continent_from_country("Czechia") == "Europe"
    assert _get_continent_from_country("br") == "South America"
    assert _get_continent_from_country("United States: East Coast") == "North America"


def test_resolve_region_only():
    loc = resolve_location("North America: Eastern")
    assert loc is not None
    assert loc.continent == "North America"
    assert loc.city == "Unknown"


def test_resolve_country_code():
    loc = resolve_location("GB")
    assert loc is not None
    assert loc.country == "United Kingdom"
    assert loc.continent == "Europe"


def test_lookup_country_name():
    from backend.utils.geocoding import _lookup_country_name
    assert _lookup_country_name("Germany") == "Germany"
    assert _lookup_country_name("Brasil") == "Brazil"
    assert _lookup_country_name("USA") == "United States"
    assert _lookup_country_name("gb") == "United Kingdom"
    assert _lookup_country_name("The Outpost, Sheffield, UK") is None


def test_venue_query_no_country_shortcircuit():
    # A comma-joined venue string must NOT be treated as country-only.
    loc = resolve_location("Rogue State Games, Mahwah NJ, US")
    assert loc is not None
    # Nominatim may or may not resolve; but if it does, city should be Mahwah
    # or the whole thing falls through to Photon. We assert it never returns
    # the venue string AS the country.
    assert "Rogue State Games" not in (loc.country or "")
