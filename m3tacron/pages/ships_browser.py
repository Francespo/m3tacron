"""
Ships Browser Page.

Displays all ships with aggregated statistics per faction.
"""
import reflex as rx
from ..components.format_filter import hierarchical_format_filter, FormatFilterMixin
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


class ShipsBrowserState(FormatFilterMixin):
    """State for the Ships Browser page."""
    
    # Data
    ships: list[dict] = []
    
    # Sorting
    sort_metric: str = "Popularity"
    sort_direction: str = "desc"
    
    # Data Source
    data_source: str = "xwa"
    
    # Date Range Filters
    date_range_start: str = ""
    date_range_end: str = ""
    
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
    
    def set_date_start(self, date: str):
        self.date_range_start = date
        self.load_data()
    
    def set_date_end(self, date: str):
        self.date_range_end = date
        self.load_data()
    
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
    
    def on_mount(self):
        self.set_data_source(self.data_source)
    
    def set_data_source(self, source: str | list[str]):
        if isinstance(source, list):
            source = source[0]
        self.data_source = source
        
        # Set default format based on data source
        new_formats = self.selected_formats.copy()
        for m in MacroFormat:
            new_formats[m.value] = False
            for f in m.formats():
                new_formats[f.value] = False
        
        target_macro = MacroFormat.V2_5 if self.data_source == "xwa" else MacroFormat.V2_0
        new_formats[target_macro.value] = True
        for f in target_macro.formats():
            new_formats[f.value] = True
        
        self.selected_formats = new_formats
        self.current_page = 0
        self.load_data()
    
    def on_filter_change(self):
        """Handle format filter changes."""
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
        rx.vstack(
            rx.text("GAME CONTENT SOURCE", size="2", weight="bold", letter_spacing="1px", color=TEXT_PRIMARY),
            rx.segmented_control.root(
                rx.segmented_control.item("XWA", value="xwa"),
                rx.segmented_control.item("Legacy", value="legacy"),
                value=ShipsBrowserState.data_source,
                on_change=ShipsBrowserState.set_data_source,
                width="100%",
                color_scheme="gray",
            ),
            spacing="1",
            width="100%"
        ),
        
        rx.divider(border_color=BORDER_COLOR),
        
        # Tournament Filters
        rx.text("TOURNAMENT FILTERS", size="2", weight="bold", letter_spacing="1px", color=TEXT_PRIMARY),
        
        # Date Range
        rx.vstack(
            rx.text("Date Range", size="1", weight="bold", color=TEXT_SECONDARY),
            rx.vstack(
                rx.input(
                    type="date",
                    value=ShipsBrowserState.date_range_start,
                    on_change=ShipsBrowserState.set_date_start,
                    style=INPUT_STYLE,
                    width="100%"
                ),
                rx.text("to", size="1", color=TEXT_SECONDARY, text_align="center"),
                rx.input(
                    type="date",
                    value=ShipsBrowserState.date_range_end,
                    on_change=ShipsBrowserState.set_date_end,
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
        
        # Format Filter
        rx.box(
            hierarchical_format_filter(ShipsBrowserState),
            width="100%",
        ),
        
        rx.divider(border_color=BORDER_COLOR),
        
        # Ship Filters Section
        rx.text("SHIP FILTERS", size="2", weight="bold", letter_spacing="1px", color=TEXT_PRIMARY),
        
        # Faction Filter
        filter_accordion(
            "Factions",
            ShipsBrowserState.faction_options,
            ShipsBrowserState.selected_factions,
            ShipsBrowserState.toggle_faction
        ),
        
        # Chassis Filter
        searchable_filter_accordion(
            "Chassis",
            ShipsBrowserState.available_ships,
            ShipsBrowserState.selected_ships,
            ShipsBrowserState.toggle_ship,
            ShipsBrowserState.ship_search_text,
            ShipsBrowserState.set_ship_search
        ),
        
        rx.divider(border_color=BORDER_COLOR),
        
        # Sort By
        rx.vstack(
            rx.text("SORT BY", size="2", weight="bold", letter_spacing="1px", color=TEXT_PRIMARY),
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
                # Ship Icon (Extra Large, centered)
                rx.box(
                    ship_icon(s["ship_xws"].to(str), size="6em", color=faction_color),
                    padding="24px",
                    display="flex",
                    justify_content="center",
                    align_items="center",
                    width="100%",
                ),
                
                # Ship Name + Faction
                rx.vstack(
                    rx.hstack(
                        faction_icon(faction_xws, size="1.4em"),
                        rx.text(
                            s["ship_name"].to(str),
                            weight="bold",
                            color=TEXT_PRIMARY,
                            size="4",
                            text_align="center"
                        ),
                        spacing="2",
                        justify="center",
                        align="center",
                    ),
                    rx.text(
                        faction_label,
                        size="2",
                        color=faction_color,
                        font_family=SANS_FONT,
                        text_align="center"
                    ),
                    spacing="1",
                    align="center",
                    width="100%",
                ),
                
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
                    wrap="wrap"
                ),
                
                spacing="3",
                width="100%",
                align="center",
                padding="12px"
            ),
            padding="16px",
            style=TERMINAL_PANEL_STYLE,
            border_radius=RADIUS,
            width="100%",
            min_height="280px",
            transition="transform 0.2s",
            _hover={"transform": "translateY(-4px)"}
        ),
        # Link to cards browser with ship and faction filters
        href=rx.Var.create(f"/cards?ship=") + s["ship_xws"].to(str) + rx.Var.create("&faction=") + s["faction"].to(str),
        width="100%"
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
