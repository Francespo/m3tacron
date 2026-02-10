"""
Ships Browser Page.

Displays all ships with aggregated statistics per faction.
"""
import reflex as rx
from ..components.content_source_filter import content_source_filter, ContentSourceState
from ..components.tournament_filters import tournament_filters, TournamentFilterMixin
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
from ..backend.utils import load_all_ships


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


class ShipsBrowserState(TournamentFilterMixin):
    """
    State for the Ships Browser page.
    """
    # Content Source State Logic (Manually Implemented to avoid Mixin conflicts)
    data_source: str = "xwa" # xwa, legacy
    include_epic: bool = False

    def set_data_source(self, *args):
        source = args[0]
        if isinstance(source, list):
            source = source[0]
        self.data_source = source
        self.on_content_source_change()

    def set_include_epic(self, val: bool):
        self.include_epic = val
        self.on_content_source_change()

    def on_content_source_change(self):
        """Handle content source changes."""
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
    
    @rx.var
    def all_ships(self) -> list[dict]:
        """Load all ships based on data source."""
        source_enum = DataSource(self.data_source) if isinstance(self.data_source, str) else self.data_source
        return load_all_ships(source_enum)
    
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
                s_factions_norm = {norm(f) for f in s["factions"]}
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
    
    def set_data_source_override(self, source: str | list[str]):
        # Overriding to add default format logic manually if needed, 
        # but ContentSourceState + Hook handles basic set.
        # This function seems redundant if using Mixin's set_data_source.
        # However, we need to init formats.
        pass

    def on_mount(self):
        self.load_locations()
        if not self.data_source: self.data_source = "xwa"
        self.set_default_formats_for_source(self.data_source)
        self.load_data()
    
    # Hooks
    def on_content_source_change(self):
        self.current_page = 0
        self.set_default_formats_for_source(self.data_source)
        self.load_data()

    def on_tournament_filter_change(self):
        self.current_page = 0
        self.load_data()
    
    def on_page_change(self):
        self.load_data()
    
    def load_data(self):
        # Build sort criteria
        criteria_map = {
            "Popularity": SortingCriteria.POPULARITY,
            "Win Rate": SortingCriteria.WINRATE,
            "Games": SortingCriteria.GAMES,
        }
        criteria = criteria_map.get(self.sort_metric, SortingCriteria.POPULARITY)
        direction = SortDirection(self.sort_direction)
        
        # Build allowed formats
        allowed = []
        for k, v in self.selected_formats.items():
            is_valid_format = False
            for f in Format:
                if f.value == k:
                    is_valid_format = True
                    break
            if v and is_valid_format:
                allowed.append(k)
        
        # Build faction filter
        active_factions = [k for k, v in self.selected_factions.items() if v]
        active_ships = [k for k, v in self.selected_ships.items() if v]
        
        filters = {
            "allowed_formats": allowed,
            "date_start": self.date_range_start,
            "date_end": self.date_range_end,
            "faction": active_factions,
            "ship": active_ships,
            # Location
            "continent": [k for k, v in self.selected_continents.items() if v],
            "country": [k for k, v in self.selected_countries.items() if v],
            "city": [k for k, v in self.selected_cities.items() if v],
        }
        
        try:
            ds_enum = DataSource(self.data_source)
        except ValueError:
            ds_enum = DataSource.XWA
        
        data = aggregate_ship_stats(filters, criteria, direction, ds_enum)
        
        self.total_items_count = len(data)
        
        # Pagination
        start = self.current_page * self.page_size
        end = start + self.page_size
        self.ships = data[start:end]


def render_filters() -> rx.Component:
    """Render the sidebar filters."""
    return rx.vstack(
        # Data Source
        rx.box(
            content_source_filter(ShipsBrowserState),
            width="100%"
        ),
        
        rx.divider(border_color=BORDER_COLOR, flex_shrink="0"),
        
        # Tournament Filters
        rx.box(
            tournament_filters(ShipsBrowserState),
            width="100%"
        ),
        
        rx.divider(border_color=BORDER_COLOR, flex_shrink="0"),
        
        # Ship Filters Section
        rx.text("SHIP FILTERS", size="2", weight="bold", letter_spacing="1px", color=TEXT_PRIMARY),
        
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
            ShipsBrowserState.toggle_faction
        ),
        
        # Chassis Filter
        searchable_filter_accordion(
            "Ship Chassis",
            ShipsBrowserState.available_ships,
            ShipsBrowserState.selected_ships,
            ShipsBrowserState.toggle_ship,
            ShipsBrowserState.ship_search_text,
            ShipsBrowserState.set_ship_search
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
