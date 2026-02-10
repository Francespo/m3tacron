"""
Tournament Filters Component.
Combines Date Range, Location, and Format filters.
"""
import reflex as rx
from ..theme import TEXT_PRIMARY, TEXT_SECONDARY, BORDER_COLOR, INPUT_STYLE, RADIUS
from ..components.format_filter import hierarchical_format_filter, FormatFilterMixin
from ..components.location_filter import location_filter

class TournamentFilterMixin(FormatFilterMixin):
    """
    Mixin for managing Tournament-related filters:
    - Date Range
    - Location (Continent -> Country -> City)
    - Formats (via FormatFilterMixin)
    """
    
    # --- DATE RANGE ---
    date_range_start: str = ""
    date_range_end: str = ""

    def set_date_start(self, date: str):
        self.date_range_start = date
        self.on_tournament_filter_change()
    
    def set_date_end(self, date: str):
        self.date_range_end = date
        self.on_tournament_filter_change()

    # --- LOCATION ---
    # Location State Logic (Merged from LocationFilterState)
    # {Continent: {Country: [Cities]}}
    _all_locations: dict[str, dict[str, list[str]]] = {}
    
    # Selection Maps
    selected_continents: dict[str, bool] = {}
    selected_countries: dict[str, bool] = {}
    selected_cities: dict[str, bool] = {}
    
    # Search Texts
    continent_search: str = ""
    country_search: str = ""
    city_search: str = ""
    
    def load_locations(self):
        """Load locations from DB."""
        from ..backend.utils.locations import get_all_locations
        self._all_locations = get_all_locations()
        
    @rx.var
    def continent_options(self) -> list[list[str]]:
        """List of [Label, Value] for continents."""
        all_conts =  sorted(list(self._all_locations.keys()))
        query = self.continent_search.lower()
        filtered = []
        for c in all_conts:
            if query in c.lower():
                filtered.append([c, c])
        return filtered

    @rx.var
    def country_options(self) -> list[list[str]]:
        active_continents = [k for k, v in self.selected_continents.items() if v]
        pool = []
        if not active_continents:
            for countries in self._all_locations.values():
                pool.extend(countries.keys())
        else:
            for cont in active_continents:
                countries = self._all_locations.get(cont, {})
                pool.extend(countries.keys())
        pool = sorted(list(set(pool)))
        
        query = self.country_search.lower()
        filtered = []
        for c in pool:
            if query in c.lower():
                filtered.append([c, c])
        return filtered

    @rx.var
    def city_options(self) -> list[list[str]]:
        active_countries = [k for k, v in self.selected_countries.items() if v]
        pool = []
        if not active_countries:
            for countries in self._all_locations.values():
                for cities in countries.values():
                    pool.extend(cities)
        else:
            for countries in self._all_locations.values():
                for country, cities in countries.items():
                    if country in active_countries:
                        pool.extend(cities)
        pool = sorted(list(set(pool)))
        
        query = self.city_search.lower()
        filtered = []
        for c in pool:
             if query in c.lower():
                 filtered.append([c, c])
        return filtered

    def toggle_continent(self, val: str, checked: bool):
        new_sel = self.selected_continents.copy()
        new_sel[val] = checked
        self.selected_continents = new_sel
        self.on_location_change()

    def toggle_country(self, val: str, checked: bool):
        new_sel = self.selected_countries.copy()
        new_sel[val] = checked
        self.selected_countries = new_sel
        self.on_location_change()

    def toggle_city(self, val: str, checked: bool):
        new_sel = self.selected_cities.copy()
        new_sel[val] = checked
        self.selected_cities = new_sel
        self.on_location_change()
        
    def set_continent_search(self, val: str):
        self.continent_search = val
        
    def set_country_search(self, val: str):
        self.country_search = val
        
    def set_city_search(self, val: str):
        self.city_search = val

    def on_location_change(self):
        """Handle location filter changes."""
        self.on_tournament_filter_change()

    # --- FORMAT (Override Mixin Hook) ---
    def on_filter_change(self):
        """Handle format filter changes from FormatFilterMixin."""
        self.on_tournament_filter_change()

    # --- HOOK ---
    def on_tournament_filter_change(self):
        """Hook for sub-classes to reload data."""
        pass


def tournament_filters(state: any) -> rx.Component:
    """
    Render the reusable tournament filters section.
    Includes Header, Date Range, Location, and Format.
    """
    return rx.vstack(
        rx.text("TOURNAMENT FILTERS", size="2", weight="bold", letter_spacing="1px", color=TEXT_PRIMARY),
        
        # Date Range
        rx.vstack(
            rx.text("Date Range", size="1", weight="bold", color=TEXT_SECONDARY),
            rx.vstack(
                rx.input(
                    type="date",
                    value=state.date_range_start,
                    on_change=state.set_date_start,
                    style=INPUT_STYLE,
                    width="100%"
                ),
                rx.text("to", size="1", color=TEXT_SECONDARY, text_align="center"),
                rx.input(
                    type="date",
                    value=state.date_range_end,
                    on_change=state.set_date_end,
                    style=INPUT_STYLE,
                    width="100%"
                ),
                spacing="1",
                width="100%",
                padding="8px",
                border=f"1px solid {BORDER_COLOR}",
                border_radius=RADIUS
            ),
            spacing="1",
            width="100%"
        ),
        
        # Location Filter
        rx.box(
            location_filter(state),
            width="100%",
        ),

        # Format Filter
        rx.box(
            hierarchical_format_filter(state),
            width="100%",
        ),
        
        spacing="4",
        width="100%"
    )
