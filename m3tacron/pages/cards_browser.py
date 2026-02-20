"""
Card Analyzer Page.
"""
import reflex as rx
from ..components.content_source_filter import content_source_filter
from ..components.tournament_filters import tournament_filters
from ..backend.state.global_filter_state import GlobalFilterState
from ..ui_utils.pagination import PaginationMixin
from ..components.pagination import pagination_controls
# from ..components.multi_filter import collapsible_checkbox_group # Deprecated
from ..components.sidebar import layout, dashboard_layout
from ..backend.data_structures.factions import Faction
from ..backend.data_structures.upgrade_types import UpgradeType
from ..backend.data_structures.data_source import DataSource
from ..backend.data_structures.formats import Format, MacroFormat
from ..backend.utils.xwing_data.ships import load_all_ships
from ..backend.analytics.core import aggregate_card_stats
from ..backend.data_structures.sorting_order import SortingCriteria, SortDirection
from ..backend.data_structures.view_mode import ViewMode
from ..theme import (
    TEXT_PRIMARY, TEXT_SECONDARY, BORDER_COLOR, TERMINAL_PANEL_STYLE,
    MONOSPACE_FONT, SANS_FONT, INPUT_STYLE, TERMINAL_BG, RADIUS, FACTION_COLORS
)
from ..components.ui import empty_state
from ..components.icons import ship_icon
from ..components.filter_accordion import filter_accordion
from ..components.searchable_filter_accordion import searchable_filter_accordion
from ..components.initiative_grid import initiative_grid
from ..components.advanced_filters import advanced_filters

class CardAnalyzerState(PaginationMixin):
    """
    State for the Card Analyzer page.
    """
    # Content Source State Logic (Manually Implemented to avoid Mixin conflicts) - REMOVED for Global State
    
    # Active Tab
    # Active Tab
    active_tab: str = "pilots" # pilots, upgrades
    
    # Common Filters
    text_filter: str = ""
    
    
    # Pilot Specific
    # Map of value -> boolean
    selected_factions: dict[str, bool] = {}
    
    # Ship Filter (Searchable Multi-select)
    ship_search_text: str = ""
    # We use a dict for selection just like other filters. 
    # Key = XWS ID (value), Value = True/False.
    selected_ships: dict[str, bool] = {} 
    
    # Legacy string filter (deprecated in UI but kept for compatibility logic/url?)
    # ship_filter: str = "" # Comma separated -> We replace this with selected_ships logic.
    
    selected_initiatives: dict[str, bool] = {}
    
    # Upgrade Specific
    selected_upgrade_types: dict[str, bool] = {}
    
    # --- Accordion States (Smart Persistence) ---
    faction_acc_val: list[str] = []
    ship_acc_val: list[str] = []
    upgrade_acc_val: list[str] = []
    
    def set_faction_acc_val(self, val):
        self.faction_acc_val = val
        
    def set_ship_acc_val(self, val):
        self.ship_acc_val = val
        
    def set_upgrade_acc_val(self, val):
        self.upgrade_acc_val = val
    
    # Static info for filters
    faction_options: list[list[str]] = [[f.label, f.value] for f in Faction if f != Faction.UNKNOWN]
    initiative_options: list[list[str]] = [[str(i), str(i)] for i in range(7)]
    
    @rx.var
    def faction_display_options(self) -> list[list[str]]:
        """
        Return faction options, adding 'Unrestricted' if in upgrades tab.
        """
        options = self.faction_options.copy()
        if self.active_tab == "upgrades":
            options.append(["Unrestricted", "unrestricted"])
        return options
    
    # --- NEW ADDITIONS FOR ADVANCED MODE ---
    mode: str = ViewMode.BASIC.value
    
    @rx.var
    def active_mode(self) -> str:
        return self.mode
    
    # numeric filters (min/max)
    points_min: int | None = None
    points_max: int | None = None
    
    loadout_min: int | None = None
    loadout_max: int | None = None
    
    hull_min: int | None = None
    hull_max: int | None = None
    
    shields_min: int | None = None
    shields_max: int | None = None
    
    agility_min: int | None = None
    agility_max: int | None = None
    
    # booleans for Limited/Unique
    is_unique: bool = False  # limited == 1
    is_limited: bool = False  # limited != 0
    is_not_limited: bool = False  # limited == 0
    
    # Attack range
    attack_min: int | None = None
    attack_max: int | None = None
    
    # Initiative range (replaces grid)
    init_min: int | None = None
    init_max: int | None = None
    
    # Base sizes - empty dict means no filter (all sizes)
    base_sizes: dict[str, bool] = {}

    # Epic Content
    # include_epic: bool = False
    
    def reset_card_filters(self):
        """Reset only card-specific filters."""
        self.selected_factions = {}
        self.selected_ships = {}
        self.ship_search_text = ""
        self.selected_initiatives = {}
        self.selected_upgrade_types = {}
        self.text_filter = ""
        self.base_sizes = {"Small": False, "Medium": False, "Large": False, "Huge": False}
        self.points_min = None
        self.points_max = None
        self.loadout_min = None
        self.loadout_max = None
        self.hull_min = None
        self.hull_max = None
        self.shields_min = None
        self.shields_max = None
        self.agility_min = None
        self.agility_max = None
        self.attack_min = None
        self.attack_max = None
        self.init_min = None
        self.init_max = None
        self.is_unique = False
        self.is_limited = False
        self.is_not_limited = False
        self.current_page = 0
        self.load_data()

    async def reset_tournament_filters_wrapper(self):
        """Reset only global tournament filters."""
        gs = await self.get_state(GlobalFilterState)
        gs.reset_tournament_filters()
        self.current_page = 0
        self.load_data()

    def set_mode(self, mode: str | list[str]):
        if isinstance(mode, list):
            mode = mode[0]
        # Ensure valid mode
        if mode not in [m.value for m in ViewMode]:
            mode = ViewMode.BASIC.value
        self.mode = mode

    def set_points_min(self, val: str):
        try: self.points_min = int(val)
        except ValueError: self.points_min = None
        self.load_data()
        
    def set_points_max(self, val: str):
        try: self.points_max = int(val)
        except ValueError: self.points_max = None
        self.load_data()

    def set_loadout_min(self, val: str):
        try: self.loadout_min = int(val)
        except ValueError: self.loadout_min = None
        self.load_data()

    def set_loadout_max(self, val: str):
        try: self.loadout_max = int(val)
        except ValueError: self.loadout_max = None
        self.load_data()
        
    def set_hull_min(self, val: str):
        try: self.hull_min = int(val)
        except ValueError: self.hull_min = None
        self.load_data()

    def set_hull_max(self, val: str):
        try: self.hull_max = int(val)
        except ValueError: self.hull_max = None
        self.load_data()

    def set_shields_min(self, val: str):
        try: self.shields_min = int(val)
        except ValueError: self.shields_min = None
        self.load_data()

    def set_shields_max(self, val: str):
        try: self.shields_max = int(val)
        except ValueError: self.shields_max = None
        self.load_data()

    def set_agility_min(self, val: str):
        try: self.agility_min = int(val)
        except ValueError: self.agility_min = None
        self.load_data()

    def set_agility_max(self, val: str):
        try: self.agility_max = int(val)
        except ValueError: self.agility_max = None
        self.load_data()

    def set_is_unique(self, val: bool):
        self.is_unique = val
        self.load_data()

    def set_is_limited(self, val: bool):
        self.is_limited = val
        self.load_data()

    def set_is_not_limited(self, val: bool):
        self.is_not_limited = val
        self.load_data()
        
    def set_attack_min(self, val: str):
        try: self.attack_min = int(val)
        except ValueError: self.attack_min = None
        self.load_data()

    def set_attack_max(self, val: str):
        try: self.attack_max = int(val)
        except ValueError: self.attack_max = None
        self.load_data()
        
    def set_init_min(self, val: str):
        try: self.init_min = int(val)
        except ValueError: self.init_min = None
        self.load_data()

    def set_init_max(self, val: str):
        try: self.init_max = int(val)
        except ValueError: self.init_max = None
        self.load_data()

    def toggle_base_size(self, size: str, checked: bool):
        self.base_sizes[size] = checked
        self.load_data()

    def set_include_epic(self, val: bool):
        self.include_epic = val
        self.load_data()

    
    @rx.var
    def upgrade_type_options(self) -> list[list[str]]:
        return [[t.label, t.value] for t in UpgradeType]
    
    
    # Sorting
    sort_metric: str = "Popularity" # Label
    sort_direction: str = "desc" # asc, desc

    @rx.var
    def sort_metric_options(self) -> list[str]:
        return self._sort_metric_options

    _sort_metric_options: list[str] = ["Cost", "Games", "Name", "Popularity", "Win Rate", "Loadout"]
    
    def set_sort_metric(self, metric: str):
        self.sort_metric = metric
        self.load_data()

    def toggle_sort_direction(self):
        self.sort_direction = "asc" if self.sort_direction == "desc" else "desc"
        self.load_data()
    
    # Data Source (XWA vs Legacy) - Handled by ContentSourceState
    # data_source: str = "xwa" # xwa, legacy
    
    # Epic Content - Handled by ContentSourceState
    # include_epic: bool = False

    # Data
    results: list[dict] = []
    
    # Cache for full filtered results
    _all_results_cached: list[dict] = []

    # Location State Logic Handled by TournamentFilterMixin


    
    def on_mount(self):
        # Location Filters
        self.load_locations()
        
        # Initialize selected_formats to True for all if empty - logic handled in set_data_source now
        # Enforce default format logic based on current data_source (XWA)
        self.set_data_source(self.data_source)
        
        # Handle query params for pre-selecting filters (e.g., from Ships page)
        try:
            if hasattr(self.router.page, "params") and isinstance(self.router.page.params, dict):
                ship_param = self.router.page.params.get("ship", "")
                faction_param = self.router.page.params.get("faction", "")
                
                if ship_param:
                    self.selected_ships = {ship_param: True}
                    
                if faction_param:
                    self.selected_factions = {faction_param: True}
                    
                if ship_param or faction_param:
                    self.load_data()
        except Exception:
            pass  # Ignore errors from query param handling


        
    def set_active_tab(self, tab: str):
        self.active_tab = tab
        self.results = []
        self.current_page = 0
        self.load_data()
        
    def set_sort_mode(self, mode: str):
        self.sort_mode = mode
        self.load_data()
        
    def toggle_faction(self, faction: str, checked: bool):
        # Removing yield toast to ensure reliable state update
        # print(f"DEBUG: toggle_faction called for {faction} -> {checked}")
        new_factions = self.selected_factions.copy()
        new_factions[faction] = checked
        self.selected_factions = new_factions
        
        # Determine if we should keep accordion open (usually yes if user interacting)
        # But if they uncheck all, we might want to manually close? No, let user close.
        # But if they check one, ensure it's open (it is, they clicked it).
        # We generally update the underlying filter state here.
        
        self.current_page = 0
        self.load_data()

    def set_ship_search(self, text: str):
        self.ship_search_text = text

    def toggle_ship(self, xws: str, checked: bool):
        new_ships = self.selected_ships.copy()
        new_ships[xws] = checked
        self.selected_ships = new_ships
        
        self.current_page = 0
        self.load_data()
        
    def toggle_initiative(self, init: str, checked: bool):
        new_inits = self.selected_initiatives.copy()
        new_inits[init] = checked
        self.selected_initiatives = new_inits
        
        self.current_page = 0
        self.load_data()

    def toggle_upgrade_type(self, u_type: str, checked: bool):
        new_types = self.selected_upgrade_types.copy()
        new_types[u_type] = checked
        self.selected_upgrade_types = new_types
        
        self.current_page = 0
        self.load_data()

    def set_text_filter(self, text: str):
        self.text_filter = text
        self.current_page = 0
        self.load_data()
        
    def set_date_start(self, date: str):
        self.date_range_start = date
        self.load_data()
        
    async def set_date_end(self, date: str):
        self.date_range_end = date
        await self.load_data()
        
    @rx.var
    def all_ships(self) -> list[dict]:
        return self._all_ships

    _all_ships: list[dict] = []


    # Hooks
    async def on_content_source_change(self):
        self.current_page = 0
        self.set_default_formats_for_source(self.data_source)
        await self.load_data()

    async def on_tournament_filter_change(self):
        self.current_page = 0
        await self.load_data()
        self.set_default_formats_for_source(self.data_source)
        self.load_data()

    def on_tournament_filter_change(self):
        self.current_page = 0
        self.load_data()

    def toggle_format_macro(self, macro_val: str):
        """Toggle a macro format. Overrides mixin for proper reactivity."""
        from ..backend.data_structures.formats import MacroFormat
        
        # Logic: If checked or indeterminate -> Uncheck all. If unchecked -> Check all.
        current_state = self.macro_states.get(macro_val, "unchecked")
        
        target_checked = True
        if current_state == "checked" or current_state == "indeterminate":
            target_checked = False
            
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
        self.current_page = 0
        self.load_data()

    def toggle_format_child(self, child_val: str):
        """Toggle a specific format child. Overrides mixin for proper reactivity."""
        checked = not self.selected_formats.get(child_val, False)

        new_formats = self.selected_formats.copy()
        new_formats[child_val] = checked
        self.selected_formats = new_formats
        self.current_page = 0
        self.load_data()

    # set_data_source removed - handled by GlobalFilterState

    @rx.var
    def available_ships(self) -> list[list[str]]:
        """
        Filter ships based on:
        1. Selected Factions (Dependency)
        2. Search Text
        
        Returns list of [name, xws] for the filter component.
        """
        ships = self.all_ships
        
        # 1. Faction Filter
        active_factions = {k for k, v in self.selected_factions.items() if v}
        
        filtered_by_faction = []
        if not active_factions:
            filtered_by_faction = ships
        else:
            def norm(s): return s.lower().replace(" ", "").replace("-", "")
            norm_active = {norm(f) for f in active_factions}
            
            for s in ships:
                s_factions_norm = {norm(f) for f in s.get("factions", [])}
                if not s_factions_norm.isdisjoint(norm_active):
                    filtered_by_faction.append(s)
                    
        # 2. Search Text
        final_list = []
        query = self.ship_search_text.lower()
        
        for s in filtered_by_faction:
            if query in s["name"].lower():
                 final_list.append([s["name"], s["xws"]])
                 
        return final_list
    


    def on_page_change(self):
        """Handle page change by slicing existing results."""
        self.update_view()

    def next_page(self):
        """Handle next page click."""
        # Calculate total pages
        total_pages = (self.total_items_count + self.page_size - 1) // self.page_size if self.total_items_count > 0 else 1
        if self.current_page < total_pages - 1:
            self.current_page += 1
            self.update_view()
            
    def prev_page(self):
        """Handle prev page click."""
        if self.current_page > 0:
            self.current_page -= 1
            self.update_view()

    def jump_to_page(self, val: str):
        """Handle manual page input."""
        try:
            p = int(val)
            idx = p - 1
            total_pages = (self.total_items_count + self.page_size - 1) // self.page_size if self.total_items_count > 0 else 1
            if 0 <= idx < total_pages:
                self.current_page = idx
                self.update_view()
        except ValueError:
            pass

    def handle_page_submit(self, key: str):
        """Handle Enter key in pagination input."""
        if key == "Enter":
            self.update_view()

    def update_view(self):
        """Slice the full dataset for the current page."""
        start = self.current_page * self.page_size
        end = start + self.page_size
        self.results = self._all_results_cached[start:end]



    async def on_mount(self):
        gs = await self.get_state(GlobalFilterState)
        gs.load_locations()
        # Initialize default formats if needed
        if not gs.selected_formats:
             gs.set_default_formats_for_source(gs.data_source)
             
        # Initialize selected_factions keys
        if not self.selected_factions:
             for f_list in self.faction_options:
                 self.selected_factions[f_list[1]] = False

        # --- Smart Accordion Logic ---
        # If filters are active (persisted), open the corresponding accordion.
        
        # Faction
        has_faction = any(self.selected_factions.values())
        if has_faction:
            self.faction_acc_val = ["Faction"]
            
        # Ship
        has_ship = any(self.selected_ships.values()) or self.ship_search_text
        if has_ship:
            self.ship_acc_val = ["Ship Chassis"]
            
        # Upgrade
        has_upgrade = any(self.selected_upgrade_types.values())
        if has_upgrade:
            self.upgrade_acc_val = ["Upgrade Type"]
             
        await self.load_data()

    async def load_data(self):
        """
        Full data reload:
        1. Aggregates stats from DB based on filters.
        2. Sorts data.
        3. Updates cache.
        4. Resets pagination to 0.
        5. Updates view.
        """
        gs = await self.get_state(GlobalFilterState)
        criteria = SortingCriteria.from_label(self.sort_metric)
        direction = SortDirection(self.sort_direction)

        print(f"DEBUG: load_data called. Source: {gs.data_source}")

        # Construction Allowed Formats List
        allowed = []
        for k, v in gs.selected_formats.items():
            # Check if k is a valid Format value (exclude macros)
            is_valid_format = False
            for f in Format:
                if f.value == k:
                    is_valid_format = True
                    break
            
            if v and is_valid_format:
                allowed.append(k)
        
        # Prepare multi-select lists
        active_factions = [k for k, v in self.selected_factions.items() if v]
        active_initiatives = [k for k, v in self.selected_initiatives.items() if v]
        active_upgrade_types = [k for k, v in self.selected_upgrade_types.items() if v]
        active_ships = [k for k, v in self.selected_ships.items() if v]

        filters = {
            "allowed_formats": allowed,
            "date_start": gs.date_range_start,
            "date_end": gs.date_range_end,
            "search_text": self.text_filter,
            "faction": active_factions,
            "ship": active_ships,
            "initiative": active_initiatives,
            "upgrade_type": active_upgrade_types,
            # Advanced Filters
            "points_min": self.points_min,
            "points_max": self.points_max,
            "loadout_min": self.loadout_min,
            "loadout_max": self.loadout_max,
            "hull_min": self.hull_min,
            "hull_max": self.hull_max,
            "shields_min": self.shields_min,
            "shields_max": self.shields_max,
            "agility_min": self.agility_min,
            "agility_max": self.agility_max,
            "attack_min": self.attack_min,
            "attack_max": self.attack_max,
            "init_min": self.init_min,
            "init_max": self.init_max,
            "is_unique": self.is_unique,
            "is_limited": self.is_limited,
            "is_not_limited": self.is_not_limited,
            "base_sizes": self.base_sizes,
            "include_epic": gs.include_epic,
            # Location
            "continent": [k for k, v in gs.selected_continents.items() if v],
            "country": [k for k, v in gs.selected_countries.items() if v],
            "city": [k for k, v in gs.selected_cities.items() if v],
        }
        # print(f"DEBUG: Active Filters: {filters}")
        
        # Convert data_source string to Enum
        try:
            ds_enum = DataSource(gs.data_source)
        except ValueError:
            ds_enum = DataSource.XWA

        # Update sort options based on source
        opts = ["Cost", "Games", "Name", "Popularity", "Win Rate"]
        if gs.data_source == "xwa":
             opts.append("Loadout")
             opts.sort()
        self._sort_metric_options = opts

        # Update all ships for current source
        self._all_ships = list(load_all_ships(ds_enum).values())

        data = aggregate_card_stats(filters, criteria, direction, self.active_tab, ds_enum)
        
        self._all_results_cached = data
        self.total_items_count = len(data)
        self.current_page = 0
        
        self.update_view()

def render_filters() -> rx.Component:
    """Render the sidebar filters."""
    return rx.vstack(
        # 1. Content Source
        rx.box(
            content_source_filter(CardAnalyzerState.load_data),
            width="100%"
        ),

        
        rx.divider(border_color=BORDER_COLOR, flex_shrink="0"),
        
        # 2. Tournament Filters
        tournament_filters(
            on_change=CardAnalyzerState.load_data,
            reset_handler=CardAnalyzerState.reset_tournament_filters_wrapper
        ),
        
        rx.divider(border_color=BORDER_COLOR, flex_shrink="0"),
        
        # 3. Filters Header
        rx.vstack(
            rx.hstack(
                rx.text("CARD FILTERS", size="2", weight="bold", letter_spacing="1px", color=TEXT_PRIMARY),
                rx.spacer(),
                rx.icon_button(
                    rx.icon(tag="rotate-ccw"),
                    on_click=CardAnalyzerState.reset_card_filters,
                    variable="ghost",
                    color_scheme="gray",
                    size="1",
                    tooltip="Reset Card Filters"
                ),
                rx.segmented_control.root(
                    rx.segmented_control.item("Basic", value=ViewMode.BASIC.value),
                    rx.segmented_control.item("Advanced", value=ViewMode.ADVANCED.value),
                    value=CardAnalyzerState.mode,
                    on_change=CardAnalyzerState.set_mode,
                    size="1",
                ),
                width="100%",
                align_items="center"
            ),
            
            # Sort By (Common)
            rx.vstack(
                rx.text("Sort By", size="1", weight="bold", letter_spacing="1px", color=TEXT_SECONDARY),
                rx.hstack(
                    rx.select(
                        CardAnalyzerState.sort_metric_options,
                        value=CardAnalyzerState.sort_metric,
                        on_change=CardAnalyzerState.set_sort_metric,
                        style=INPUT_STYLE,
                        flex="1",
                        color_scheme="gray",
                    ),
                    rx.icon_button(
                        rx.cond(
                            CardAnalyzerState.sort_direction == "asc",
                            rx.icon(tag="arrow-up"),
                            rx.icon(tag="arrow-down")
                        ),
                        on_click=CardAnalyzerState.toggle_sort_direction,
                        variant="soft",
                        color_scheme="gray",
                        size="2",
                        width="40px"
                    ),
                    width="100%",
                    spacing="2"
                ),
                spacing="1",
                width="100%"
            ),

            # --- SHARED FILTERS (Always visible in both Basic and Advanced) ---

            # Text Search
            rx.vstack(
                rx.text("Text Search", size="1", weight="bold", color=TEXT_SECONDARY),
                rx.input(
                    placeholder="Search card text",
                    value=CardAnalyzerState.text_filter,
                    on_change=CardAnalyzerState.set_text_filter,
                    style=INPUT_STYLE,
                    width="100%",
                    color_scheme="gray",
                ),
                spacing="1",
                width="100%"
            ),

            # Faction (Pilots only)
            rx.cond(
                CardAnalyzerState.active_tab == "pilots",
                filter_accordion(
                    "Faction",
                    CardAnalyzerState.faction_options,
                    CardAnalyzerState.selected_factions,
                    CardAnalyzerState.toggle_faction,
                    accordion_value=CardAnalyzerState.faction_acc_val,
                    on_accordion_change=CardAnalyzerState.set_faction_acc_val,
                ),
            ),

            # Ship Chassis (Pilots only)
            rx.cond(
                CardAnalyzerState.active_tab == "pilots",
                searchable_filter_accordion(
                    "Ship Chassis",
                    CardAnalyzerState.available_ships,
                    CardAnalyzerState.selected_ships,
                    CardAnalyzerState.toggle_ship,
                    CardAnalyzerState.ship_search_text,
                    CardAnalyzerState.set_ship_search,
                    accordion_value=CardAnalyzerState.ship_acc_val,
                    on_accordion_change=CardAnalyzerState.set_ship_acc_val,
                ),
            ),

            # Upgrade Type (Upgrades only)
            rx.cond(
                CardAnalyzerState.active_tab == "upgrades",
                filter_accordion(
                    "Upgrade Type",
                    CardAnalyzerState.upgrade_type_options,
                    CardAnalyzerState.selected_upgrade_types,
                    CardAnalyzerState.toggle_upgrade_type,
                    accordion_value=CardAnalyzerState.upgrade_acc_val,
                    on_accordion_change=CardAnalyzerState.set_upgrade_acc_val,
                ),
            ),

            # --- ADVANCED MODE EXTRAS (Only visible in Advanced) ---
            rx.cond(
                CardAnalyzerState.mode == ViewMode.ADVANCED.value,
                advanced_filters(CardAnalyzerState)
            ),
            
            width="100%",
            align_items="start",
            spacing="3"
        ),
        
        spacing="4",
        width="100%", 
        min_width="250px",
        height="100%",
        # Layout handles scrolling and positioning
    )

def pilot_card(p: dict) -> rx.Component:
    normalized_faction = p["faction"].to(str).lower().replace(" ", "").replace("-", "")
    color = FACTION_COLORS.get(normalized_faction, TEXT_SECONDARY)
    
    return rx.link(
        rx.box(
            rx.vstack(
                rx.cond(
                    p["image"].to(str) != "",
                    rx.image(src=p["image"].to(str), width="100%", height="auto", border_radius="12px", max_height="300px", object_fit="contain"),
                    rx.box(rx.text("NO IMAGE", color=TEXT_SECONDARY, size="1"), height="200px", width="100%", bg="rgba(255,255,255,0.05)", border_radius="12px", display="flex", align_items="center", justify_content="center")
                ),
                rx.vstack(
                    rx.text(p["name"].to(str), weight="bold", color=TEXT_PRIMARY, size="3", text_align="center"),
                    rx.text(p["ship"].to(str), size="1", color=color, font_family=MONOSPACE_FONT, text_align="center"),
                    rx.hstack(
                        rx.badge(p["count"].to(str) + " LISTS", color_scheme="gray", variant="solid", radius="full"),
                        rx.badge(p["games"].to(str) + " GAMES", color_scheme="gray", variant="solid", radius="full"), # NEW: Games Count
                        rx.cond(
                            p["win_rate"].to(str) == "NA",
                            rx.badge("NA WR", color_scheme="gray", variant="solid", radius="full"),
                            rx.badge(p["win_rate"].to(float).to(int).to(str) + "% WR", color_scheme=rx.cond(p["win_rate"].to(float) >= 50, "green", "orange"), variant="solid", radius="full")
                        ),
                        rx.badge(p["cost"].to(str) + " PTS", color_scheme="blue", variant="solid", radius="full"),
                        rx.cond(
                            GlobalFilterState.data_source == "xwa",
                            rx.badge(p["loadout"].to(str) + " LV", color_scheme="purple", variant="solid", radius="full"),
                            rx.fragment()
                        ),
                        spacing="2",
                        justify="center",
                        width="100%",
                        wrap="wrap"
                    ),
                    width="100%",
                    padding="8px",
                    align="center",
                    spacing="2"
                ),
                spacing="0",
                width="100%",
                align="center"
            ),
            padding="12px",
            style=TERMINAL_PANEL_STYLE,
            border_radius=RADIUS,
            width="100%",
            min_height="420px",
            transition="transform 0.2s",
            _hover={"transform": "translateY(-4px)"}
        ),
        href="/pilot/" + p["xws"].to_string(),
        width="100%"
    )

def upgrade_card(u: dict) -> rx.Component:
    return rx.link(
        rx.box(
            rx.vstack(
                rx.cond(
                    u["image"].to(str) != "",
                    rx.image(src=u["image"].to(str), width="100%", height="auto", border_radius="12px", max_height="250px", object_fit="contain"),
                    rx.box(rx.text("NO IMAGE", color=TEXT_SECONDARY, size="1"), height="150px", width="100%", bg="rgba(255,255,255,0.05)", border_radius="12px", display="flex", align_items="center", justify_content="center")
                ),
                rx.vstack(
                    rx.text(u["name"].to(str), weight="bold", color=TEXT_PRIMARY, size="2", text_align="center"),
                    rx.text(u["type"].to(str), size="1", color="cyan", font_family=MONOSPACE_FONT, text_align="center"),
                    rx.hstack(
                        rx.badge(u["count"].to(str) + " USED", color_scheme="gray", variant="solid", radius="full"),
                        rx.badge(u["games"].to(str) + " GAMES", color_scheme="gray", variant="solid", radius="full"),
                        rx.cond(
                            u["win_rate"].to(str) == "NA",
                            rx.badge("NA WR", color_scheme="gray", variant="solid", radius="full"),
                            rx.badge(u["win_rate"].to(float).to(int).to(str) + "% WR", color_scheme=rx.cond(u["win_rate"].to(float) >= 50, "green", "orange"), variant="solid", radius="full")
                        ),
                        rx.badge(u["cost"].to(str) + " PTS", color_scheme="blue", variant="solid", radius="full"),
                        spacing="2",
                        justify="center",
                        width="100%",
                        wrap="wrap"
                    ),
                    width="100%",
                    padding="8px",
                    align="center",
                    spacing="2"
                ),
                spacing="0",
                width="100%",
                align="center"
            ),
            padding="12px",
            style=TERMINAL_PANEL_STYLE,
            border_radius=RADIUS,
            width="100%",
            min_height="420px",
            transition="transform 0.2s",
            _hover={"transform": "translateY(-4px)"}
        ),
        href="/upgrade/" + u["xws"].to_string(),
        width="100%"
    )

def render_content() -> rx.Component:
    return rx.vstack(
        # Controls
        rx.hstack(
            rx.tabs.root(
                rx.tabs.list(
                    rx.tabs.trigger("Pilots", value="pilots", width="120px"),
                    rx.tabs.trigger("Upgrades", value="upgrades", width="120px"),
                ),
                value=CardAnalyzerState.active_tab,
                on_change=CardAnalyzerState.set_active_tab,
                width="100%",
                color_scheme="gray",
            ),
            width="100%",
            margin_bottom="24px",
            border_bottom=f"1px solid {BORDER_COLOR}"
        ),
        
        # Grid
        rx.cond(
            CardAnalyzerState.results.length() > 0,
            rx.vstack(
                rx.grid(
                    rx.cond(
                        CardAnalyzerState.active_tab == "pilots",
                        rx.foreach(CardAnalyzerState.results.to(list[dict]), pilot_card),
                        rx.foreach(CardAnalyzerState.results.to(list[dict]), upgrade_card)
                    ),
                    columns={"initial": "1", "sm": "2", "xl": "3", "2xl": "4"},
                    spacing="4",
                    width="100%"
                ),
                # Pagination
                pagination_controls(CardAnalyzerState),
                width="100%",
                spacing="4"
            ),
            rx.box(
                empty_state(
                    title="0 CARDS FOUND",
                    description="No cards match your current filters or search query.",
                    icon_tag="sticky-note",
                    reset_handler=CardAnalyzerState.reset_card_filters
                ),
                width="100%",
                padding_y="48px"
            ),
        ),
        
        width="100%",
        padding="20px",
        align="start"
    )

def cards_browser_page() -> rx.Component:
    return layout(
        dashboard_layout(
             render_filters(),
             render_content()
        ),
        on_mount=CardAnalyzerState.on_mount
    )
