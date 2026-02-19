"""
Global Filter State.
Manages persistent filters across the application (Content Source, Tournaments, etc).
"""
import reflex as rx
from ...backend.data_structures.data_source import DataSource
from ...backend.data_structures.formats import Format, MacroFormat

class GlobalFilterState(rx.State):
    """
    Shared state for global filters.
    Persists:
    - Content Source (XWA/Legacy)
    - Tournament Date Range
    - Tournament Location
    - Formats
    """
    # --- Content Source ---
    data_source: str = "xwa" # xwa, legacy
    include_epic: bool = False

    def set_data_source(self, val: str | list[str]):
        if isinstance(val, list):
            val = val[0]
        self.data_source = val
        self.set_default_formats_for_source(val)

    def set_include_epic(self, val: bool):
        self.include_epic = val

    # --- Tournament Filters ---
    
    # Date Range
    date_range_start: str = ""
    date_range_end: str = ""

    def set_date_start(self, date: str):
        self.date_range_start = date
    
    def set_date_end(self, date: str):
        self.date_range_end = date

    # Formats (Using Map for checkbox group logic)
    # Key: Format Enum Value, Value: Boolean
    selected_formats: dict[str, bool] = {} 
    
    # Locations
    selected_continents: dict[str, bool] = {}
    selected_countries: dict[str, bool] = {}
    selected_cities: dict[str, bool] = {}
    
    # Location Search
    continent_search: str = ""
    country_search: str = ""
    city_search: str = ""

    def on_mount(self):
        """Initialize defaults if needed."""
        if not self.selected_formats:
            self.set_default_formats_for_source(self.data_source)

    def set_default_formats_for_source(self, source: str):
        """Set default format selection based on source."""
        new_formats = {}
        # Reset all
        for m in MacroFormat:
            new_formats[m.value] = False
            for f in m.formats():
                new_formats[f.value] = False
        
        target_macro = MacroFormat.V2_5 if source == "xwa" else MacroFormat.V2_0
        new_formats[target_macro.value] = True
        for f in target_macro.formats():
             new_formats[f.value] = True
             
        self.selected_formats = new_formats

    def toggle_format_macro(self, macro_val: str):
        """Toggle a macro format."""
        # Logic: If checked or indeterminate -> Uncheck all. If unchecked -> Check all.
        # We need to calculate current state first.
        # Simplified: Just check if the macro key itself is true? 
        # Or better check all children.
        # For simple toggle:
        target_checked = not self.selected_formats.get(macro_val, False)
        
        new_formats = self.selected_formats.copy()
        
        # Update children
        try:
            macro = MacroFormat(macro_val)
            for f in macro.formats():
                new_formats[f.value] = target_checked
        except ValueError:
            pass
            
        # Update macro itself
        new_formats[macro_val] = target_checked
        self.selected_formats = new_formats

    def toggle_format_child(self, child_val: str):
        """Toggle a specific format child."""
        checked = not self.selected_formats.get(child_val, False)
        new_formats = self.selected_formats.copy()
        new_formats[child_val] = checked
        self.selected_formats = new_formats

    # --- Computed Vars for UI ---
    
    _all_locations: dict[str, dict[str, list[str]]] = {}

    def load_locations(self):
        """Load locations from DB."""
        from ...backend.utils.locations import get_all_locations
        self._all_locations = get_all_locations()

    @rx.var
    def macro_states(self) -> dict[str, str]:
        """
        Compute the state of each macro: 'checked', 'unchecked', or 'indeterminate'.
        """
        states = {}
        for m in MacroFormat:
            children = [f.value for f in m.formats()]
            if not children:
                states[m.value] = "unchecked"
                continue
            
            # Count how many children are checked
            checked_count = sum(1 for c in children if self.selected_formats.get(c, False))
            
            if checked_count == len(children):
                states[m.value] = "checked"
            elif checked_count == 0:
                states[m.value] = "unchecked"
            else:
                states[m.value] = "indeterminate"
        return states

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
        active_continents = [k for k, v in self.selected_countries.items() if v] # BUG IN ORIGINAL MIXIN: was self.selected_continents
        # Re-reading mixin logic: 
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

    # --- Location Actions ---
    def toggle_continent(self, val: str, checked: bool):
        new_sel = self.selected_continents.copy()
        new_sel[val] = checked
        self.selected_continents = new_sel

    def toggle_country(self, val: str, checked: bool):
        new_sel = self.selected_countries.copy()
        new_sel[val] = checked
        self.selected_countries = new_sel

    def toggle_city(self, val: str, checked: bool):
        new_sel = self.selected_cities.copy()
        new_sel[val] = checked
        self.selected_cities = new_sel
        
    def set_continent_search(self, val: str):
        self.continent_search = val
        
    def set_country_search(self, val: str):
        self.country_search = val
        
    def set_city_search(self, val: str):
        self.city_search = val

    # --- Reset ---
    def reset_filters(self, *args):
        """Reset all filters (Event Handler)."""
        self._reset_logic(reset_source=True)

    def reset_tournament_filters(self, *args):
        """Reset only tournament filters (Event Handler)."""
        self._reset_logic(reset_source=False)

    def _reset_logic(self, reset_source: bool = True):
        """Internal logic for resetting filters."""
        if reset_source:
            self.data_source = "xwa"
            
        # Always reset formats based on current data source
        self.set_default_formats_for_source(self.data_source)
        
        self.include_epic = False
        self.date_range_start = ""
        self.date_range_end = ""
        self.selected_continents = {}
        self.selected_countries = {}
        self.selected_cities = {}
        self.continent_search = ""
        self.country_search = ""
        self.city_search = ""
