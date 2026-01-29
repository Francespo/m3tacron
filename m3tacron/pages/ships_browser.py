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
from ..backend.data_structures.formats import Format, MacroFormat
from ..backend.analytics.ships import aggregate_ship_stats
from ..backend.data_structures.sorting_order import SortingCriteria, SortDirection
from ..theme import (
    TEXT_PRIMARY, TEXT_SECONDARY, BORDER_COLOR, TERMINAL_PANEL_STYLE,
    SANS_FONT, MONOSPACE_FONT, INPUT_STYLE, RADIUS, FACTION_COLORS
)
from ..components.icons import ship_icon
from ..ui_utils.factions import faction_icon, get_faction_color


class ShipsBrowserState(FormatFilterMixin):
    """State for the Ships Browser page."""
    
    # Data
    ships: list[dict] = []
    
    # Sorting
    sort_metric: str = "Popularity"  # Popularity, Win Rate, Games
    sort_direction: str = "desc"
    
    # Data Source
    data_source: str = "xwa"
    
    @rx.var
    def sort_metric_options(self) -> list[str]:
        return ["Games", "Popularity", "Win Rate"]
    
    def set_sort_metric(self, metric: str):
        self.sort_metric = metric
        self.load_data()
    
    def toggle_sort_direction(self):
        self.sort_direction = "asc" if self.sort_direction == "desc" else "desc"
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
        
        filters = {
            "allowed_formats": allowed,
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
        
        # Format Filter
        rx.box(
            hierarchical_format_filter(ShipsBrowserState),
            width="100%",
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


def ship_card(s: dict) -> rx.Component:
    """Render a single ship card."""
    faction_xws = s["faction_xws"].to(str)
    faction_color = get_faction_color(faction_xws)
    
    return rx.link(
        rx.box(
            rx.vstack(
                # Ship Icon (Large, centered)
                rx.box(
                    ship_icon(s["ship_xws"].to(str), size="4em", color=faction_color),
                    padding="16px",
                    display="flex",
                    justify_content="center",
                    align_items="center",
                    width="100%",
                ),
                
                # Ship Name + Faction
                rx.vstack(
                    rx.hstack(
                        faction_icon(faction_xws, size="1.2em"),
                        rx.text(
                            s["ship_name"].to(str),
                            weight="bold",
                            color=TEXT_PRIMARY,
                            size="3",
                            text_align="center"
                        ),
                        spacing="2",
                        justify="center",
                        align="center",
                    ),
                    rx.text(
                        s["faction"].to(str),
                        size="1",
                        color=faction_color,
                        font_family=MONOSPACE_FONT,
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
                padding="8px"
            ),
            padding="12px",
            style=TERMINAL_PANEL_STYLE,
            border_radius=RADIUS,
            width="100%",
            transition="transform 0.2s",
            _hover={"transform": "translateY(-4px)"}
        ),
        # Link to cards browser with ship and faction filters
        href=rx.Var.create(f"/cards?ship=") + s["ship_xws"].to(str) + rx.Var.create("&faction=") + s["faction_xws"].to(str),
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
