"""
Ships Browser Page.

Displays all ships with aggregated statistics per faction.
"""
import reflex as rx
from ..components.content_source_filter import content_source_filter
from ..components.tournament_filters import tournament_filters
from ..backend.state.global_filter_state import GlobalFilterState
from ..ui_utils.pagination import PaginationMixin
from ..components.pagination import pagination_controls
from ..components.sidebar import layout, dashboard_layout
from ..backend.data_structures.data_source import DataSource
from ..backend.data_structures.factions import Faction
from ..backend.data_structures.formats import Format, MacroFormat
from ..backend.analytics.ships import aggregate_ship_stats
from ..backend.data_structures.sorting_order import SortingCriteria, SortDirection
from ..theme import (
    TEXT_PRIMARY, TEXT_SECONDARY, BORDER_COLOR, TERMINAL_PANEL_STYLE,
    SANS_FONT, MONOSPACE_FONT, INPUT_STYLE, RADIUS, FACTION_COLORS
)
from ..components.icons import ship_icon
from ..ui_utils.factions import faction_icon, get_faction_color
from ..components.filter_accordion import filter_accordion
from ..components.searchable_filter_accordion import searchable_filter_accordion
from ..backend.utils.xwing_data.ships import load_all_ships


# Faction label mapping for display
FACTION_LABELS = {
    "rebelalliance": "Rebel Alliance",
    "galacticempire": "Galactic Empire",
    "scumandvillainy": "Scum and Villainy",
    "resistance": "Resistance",
    "firstorder": "First Order",
    "galacticrepublic": "Galactic Republic",
    "separatistalliance": "Separatist Alliance",
}


class ShipsBrowserState(PaginationMixin):
    """
    State for the Ships Browser page.
    """
    
    # Global state access
    
    def on_content_source_change(self):
        """Handle content source changes (triggered via load_data chain)."""
        self.current_page = 0
        self.load_data()
    
    # Data
    ships: list[dict] = []
    
    # Sorting
    sort_metric: str = "Popularity"
    sort_direction: str = "desc"
    
    # Data Source - Handled by ContentSourceState
    # data_source: str = "xwa"
    
    # Date Range Filters - Handled by TournamentFilterMixin
    # date_range_start: str = ""
    # date_range_end: str = ""
    
    # Ship Filters
    selected_factions: dict[str, bool] = {}
    selected_ships: dict[str, bool] = {}
    ship_search_text: str = ""
    
    # --- Accordion States (Smart Persistence) ---
    faction_acc_val: list[str] = []
    ship_acc_val: list[str] = []
    
    def set_faction_acc_val(self, val):
        self.faction_acc_val = val
        
    def set_ship_acc_val(self, val):
        self.ship_acc_val = val
    
    # Static faction options
    faction_options: list[list[str]] = [
        ["Rebel Alliance", "Rebel Alliance"],
        ["Galactic Empire", "Galactic Empire"],
        ["Scum and Villainy", "Scum and Villainy"],
        ["Resistance", "Resistance"],
        ["First Order", "First Order"],
        ["Galactic Republic", "Galactic Republic"],
        ["Separatist Alliance", "Separatist Alliance"]
    ]
    
    @rx.var
    def sort_metric_options(self) -> list[str]:
        return ["Games", "Popularity", "Win Rate"]
    
    all_ships: list[dict] = [] # Now a state var set in load_data
    
    @rx.var
    def available_ships(self) -> list[list[str]]:
        """Filter ships based on selected factions and search text."""
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
    
    def set_sort_metric(self, metric: str):
        self.sort_metric = metric
        self.load_data()
    
    def toggle_sort_direction(self):
        self.sort_direction = "asc" if self.sort_direction == "desc" else "desc"
        self.load_data()
    
    # Date setters handled by TournamentFilterMixin
    
    def toggle_faction(self, faction: str, checked: bool):
        self.selected_factions[faction] = checked
        self.current_page = 0
        self.load_data()
    
    def set_ship_search(self, text: str):
        self.ship_search_text = text
    
    def toggle_ship(self, xws: str, checked: bool):
        self.selected_ships[xws] = checked
        self.current_page = 0
        self.load_data()

    async def reset_ship_filters(self):
        """Reset only ship-specific filters."""
        self.selected_factions = {}
        self.selected_ships = {}
        self.ship_search_text = ""
        self.sort_metric = "Popularity"
        self.sort_direction = "desc"
        self.current_page = 0
        await self.load_data()

    async def reset_tournament_filters_wrapper(self):
        """Reset global tournament filters."""
        gs = await self.get_state(GlobalFilterState)
        gs.reset_tournament_filters()
        self.current_page = 0
        await self.load_data()
    
    def set_data_source_override(self, source: str | list[str]):
        # Overriding to add default format logic manually if needed, 
        # but ContentSourceState + Hook handles basic set.
        # This function seems redundant if using Mixin's set_data_source.
        # However, we need to init formats.
        pass

    # Cache for full filtered results
    _all_ships_cached: list[dict] = []

    def on_mount(self):
        self.load_locations()
        if not self.data_source: self.data_source = "xwa"
        self.set_default_formats_for_source(self.data_source)
        
        # --- Smart Accordion Logic ---
        # Faction
        has_faction = any(self.selected_factions.values())
        if has_faction:
            self.faction_acc_val = ["Faction"]
            
        # Ship
        has_ship = any(self.selected_ships.values()) or self.ship_search_text
        if has_ship:
            self.ship_acc_val = ["Ship Chassis"]
            
        self.load_data()
    
    # Hooks
    def on_content_source_change(self):
        self.current_page = 0
        self.set_default_formats_for_source(self.data_source)
        self.load_data()

    # --- Mixin Overrides ---
    # WHY: Reflex silently fails on super() in event handlers.
    # Inlining the logic from FormatFilterMixin + calling load_data directly.
    def on_filter_change(self):
        """Hook override: reload data when format filter changes."""
        self.on_tournament_filter_change()

    def toggle_format_macro(self, macro_val: str):
        """Toggle a macro format and reload ship data."""
        from ..backend.data_structures.formats import MacroFormat
        
        current_state = self.macro_states.get(macro_val, "unchecked")
        target_checked = current_state == "unchecked"
        
        new_formats = self.selected_formats.copy()
        try:
            macro = MacroFormat(macro_val)
            for f in macro.formats():
                new_formats[f.value] = target_checked
        except ValueError:
            pass
        new_formats[macro_val] = target_checked
        
        self.selected_formats = new_formats
        self.on_tournament_filter_change()

    def toggle_format_child(self, child_val: str):
        """Toggle a specific format child and reload ship data."""
        checked = not self.selected_formats.get(child_val, False)
        new_formats = self.selected_formats.copy()
        new_formats[child_val] = checked
        self.selected_formats = new_formats
        self.on_tournament_filter_change()

    # --- Date Range Overrides REMOVED (Handled in load_data via GlobalState) ---

    # --- Location Overrides ---
    def toggle_continent(self, val: str, checked: bool):
        # We don't override global toggle locally, we just use global state
        pass

    async def on_mount(self):
        gs = await self.get_state(GlobalFilterState)
        gs.load_locations()
        # Initialize default formats if needed
        if not gs.selected_formats:
             gs.set_default_formats_for_source(gs.data_source)
        
        # Initialize selected_factions keys
        if not self.selected_factions:
             # Ships browser has hardcoded faction options in `faction_options`
             for f_list in self.faction_options:
                 self.selected_factions[f_list[1]] = False

        await self.load_data()

    async def load_data(self):
        gs = await self.get_state(GlobalFilterState)
        
        # 1. Update All Ships based on Global Source
        try:
            ds_enum = DataSource(gs.data_source)
        except ValueError:
            ds_enum = DataSource.XWA
        self.all_ships = list(load_all_ships(ds_enum).values())

        # Build sort criteria
        criteria_map = {
            "Popularity": SortingCriteria.POPULARITY,
            "Win Rate": SortingCriteria.WINRATE,
            "Games": SortingCriteria.GAMES,
        }
        criteria = criteria_map.get(self.sort_metric, SortingCriteria.POPULARITY)
        direction = SortDirection(self.sort_direction)
        
        # Build allowed formats from GLOBAL STATE
        allowed_set = set()
        valid_format_values = {f.value for f in Format}
        
        for k, v in gs.selected_formats.items():
            if v and k in valid_format_values:
                allowed_set.add(k)
        
        allowed = list(allowed_set)
        
        # Build faction filter
        active_factions = [k for k, v in self.selected_factions.items() if v]
        active_ships = [k for k, v in self.selected_ships.items() if v]
        
        filters = {
            "allowed_formats": allowed,
            "date_start": gs.date_range_start,
            "date_end": gs.date_range_end,
            "faction": active_factions,
            "ship": active_ships,
            # Location
            "continent": [k for k, v in gs.selected_continents.items() if v],
            "country": [k for k, v in gs.selected_countries.items() if v],
            "city": [k for k, v in gs.selected_cities.items() if v],
        }
        
        data = aggregate_ship_stats(filters, criteria, direction, ds_enum)
        
        self.total_items_count = len(data)
        self._all_ships_cached = data
        self.current_page = 0
        
        self.update_view()


def render_filters() -> rx.Component:
    """Render the sidebar filters."""
    return rx.vstack(
        # Data Source
        rx.box(
            content_source_filter(ShipsBrowserState.load_data),
            width="100%"
        ),
        
        rx.divider(border_color=BORDER_COLOR, flex_shrink="0"),
        
        # Tournament Filters
        rx.box(
            tournament_filters(
                on_change=ShipsBrowserState.load_data,
                reset_handler=ShipsBrowserState.reset_tournament_filters_wrapper
            ),
            width="100%"
        ),
        
        rx.divider(border_color=BORDER_COLOR, flex_shrink="0"),
        
        # Ship Filters Section
        rx.hstack(
            rx.text("SHIP FILTERS", size="2", weight="bold", letter_spacing="1px", color=TEXT_PRIMARY),
            rx.spacer(),
            rx.icon_button(
                rx.icon(tag="rotate-ccw"),
                on_click=ShipsBrowserState.reset_ship_filters,
                variable="ghost",
                color_scheme="gray",
                size="1",
                tooltip="Reset Ship Filters"
            ),
            width="100%",
            align_items="center"
        ),
        
        # Sort By (top of SHIP FILTERS)
        rx.vstack(
            rx.text("Sort By", size="1", weight="bold", color=TEXT_SECONDARY),
            rx.hstack(
                rx.select(
                    ShipsBrowserState.sort_metric_options,
                    value=ShipsBrowserState.sort_metric,
                    on_change=ShipsBrowserState.set_sort_metric,
                    style=INPUT_STYLE,
                    flex="1",
                    color_scheme="gray",
                ),
                rx.icon_button(
                    rx.cond(
                        ShipsBrowserState.sort_direction == "asc",
                        rx.icon(tag="arrow-up"),
                        rx.icon(tag="arrow-down")
                    ),
                    on_click=ShipsBrowserState.toggle_sort_direction,
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
        
        # Faction Filter
        filter_accordion(
            "Faction",
            ShipsBrowserState.faction_options,
            ShipsBrowserState.selected_factions,
            ShipsBrowserState.toggle_faction,
            accordion_value=ShipsBrowserState.faction_acc_val,
            on_accordion_change=ShipsBrowserState.set_faction_acc_val,
        ),
        
        # Chassis Filter
        searchable_filter_accordion(
            "Ship Chassis",
            ShipsBrowserState.available_ships,
            ShipsBrowserState.selected_ships,
            ShipsBrowserState.toggle_ship,
            ShipsBrowserState.ship_search_text,
            ShipsBrowserState.set_ship_search,
            accordion_value=ShipsBrowserState.ship_acc_val,
            on_accordion_change=ShipsBrowserState.set_ship_acc_val,
        ),
        
        spacing="4",
        width="100%",
        min_width="250px",
        height="100%",
    )


def get_faction_label(faction_xws: rx.Var) -> rx.Var:
    """Get human-readable label for faction XWS."""
    return rx.match(
        faction_xws,
        ("rebelalliance", "Rebel Alliance"),
        ("galacticempire", "Galactic Empire"),
        ("scumandvillainy", "Scum and Villainy"),
        ("resistance", "Resistance"),
        ("firstorder", "First Order"),
        ("galacticrepublic", "Galactic Republic"),
        ("separatistalliance", "Separatist Alliance"),
        "Unknown"
    )


def ship_card(s: dict) -> rx.Component:
    """Render a single ship card."""
    faction_xws = s["faction_xws"].to(str)
    faction_color = get_faction_color(faction_xws)
    faction_label = get_faction_label(faction_xws)
    
    return rx.link(
        rx.box(
            rx.vstack(
                # Ship Icon Container (Centered)
                rx.center(
                    ship_icon(
                        s["ship_xws"],
                        size="120px !important",
                        color=get_faction_color(s["faction_xws"].to(str)),
                    ),
                    width="100%",
                    height="140px",
                ),
                
                # Info Stack (Centered)
                rx.vstack(
                    rx.text(
                        s["ship_name"].to(str),
                        weight="bold",
                        color=TEXT_PRIMARY,
                        size="5",
                        text_align="center",
                        line_height="1.2"
                    ),
                    rx.text(
                        faction_label,
                        size="2",
                        color=faction_color,
                        font_family=SANS_FONT,
                        text_align="center",
                        weight="bold",
                    ),
                    faction_icon(faction_xws, size="2em"),
                    spacing="2",
                    align="center",
                    width="100%",
                ),
                
                rx.spacer(),
                
                # Stats Badges
                rx.hstack(
                    rx.badge(
                        s["popularity"].to(str) + " LISTS",
                        color_scheme="gray",
                        variant="solid",
                        radius="full"
                    ),
                    rx.badge(
                        s["games"].to(str) + " GAMES",
                        color_scheme="gray",
                        variant="solid",
                        radius="full"
                    ),
                    rx.cond(
                        s["win_rate"].to(str) == "NA",
                        rx.badge("NA WR", color_scheme="gray", variant="solid", radius="full"),
                        rx.badge(
                            s["win_rate"].to(float).to(int).to(str) + "% WR",
                            color_scheme=rx.cond(
                                s["win_rate"].to(float) >= 50,
                                "green",
                                "orange"
                            ),
                            variant="solid",
                            radius="full"
                        )
                    ),
                    spacing="2",
                    justify="center",
                    width="100%",
                    wrap="wrap",
                    padding_top="8px",
                ),
                
                spacing="2",
                align="center",
                width="100%",
                height="100%",
                padding="16px",
            ),
            bg=rx.color("gray", 2),
            border=f"1px solid {BORDER_COLOR}",
            border_radius="12px",
            height="350px",
            width="100%",
            transition="all 0.2s ease",
            _hover={
                "border_color": faction_color,
                "bg": rx.color("gray", 3),
                "transform": "translateY(-4px)",
            },
        ),
        href=rx.Var.create("/cards?ship=") + s["ship_xws"].to(str) + rx.Var.create("&faction=") + faction_xws,
        text_decoration="none",
    )


def render_content() -> rx.Component:
    """Render the main content."""
    return rx.vstack(
        # Header
        rx.box(
            rx.vstack(
                rx.heading(
                    "Ships",
                    size="8",
                    font_family=SANS_FONT,
                    color=TEXT_PRIMARY,
                    weight="bold",
                ),
                rx.text(
                    "Browse all ships with aggregated statistics per faction",
                    size="3",
                    color=TEXT_SECONDARY,
                    font_family=SANS_FONT,
                ),
                align="start",
                spacing="1"
            ),
            padding_bottom="24px",
            width="100%"
        ),
        
        # Ships Grid
        rx.grid(
            rx.foreach(ShipsBrowserState.ships.to(list[dict]), ship_card),
            columns={"initial": "1", "sm": "2", "lg": "3", "xl": "4"},
            spacing="4",
            width="100%"
        ),
        
        # Pagination
        pagination_controls(ShipsBrowserState),
        
        width="100%",
        padding="20px",
        align="start"
    )


def ships_browser_page() -> rx.Component:
    """The Ships Browser page."""
    return layout(
        dashboard_layout(
            render_filters(),
            render_content()
        ),
        on_mount=ShipsBrowserState.on_mount
    )
