"""
Card Analyzer Page.
"""
import reflex as rx
from ..components.format_filter import hierarchical_format_filter, FormatFilterMixin
from ..ui_utils.pagination import PaginationMixin
from ..components.pagination import pagination_controls
# from ..components.multi_filter import collapsible_checkbox_group # Deprecated
from ..components.sidebar import layout, dashboard_layout
from ..backend.data_structures.factions import Faction
from ..backend.data_structures.upgrade_types import UpgradeType
from ..backend.data_structures.data_source import DataSource
from ..backend.utils import load_all_ships
from ..theme import (
    TEXT_PRIMARY, TEXT_SECONDARY, BORDER_COLOR, TERMINAL_PANEL, TERMINAL_PANEL_STYLE,
    HEADER_FONT, MONOSPACE_FONT, SANS_FONT, INPUT_STYLE, RADIUS, FACTION_COLORS
)
from ..components.icons import ship_icon
from ..components.filter_accordion import filter_accordion
from ..components.searchable_filter_accordion import searchable_filter_accordion

class CardAnalyzerState(rx.State, FormatFilterMixin, PaginationMixin):
    """
    State for the Card Analyzer page.
    """
    # Active Tab
    active_tab: str = "pilots" # pilots, upgrades
    
    # Common Filters
    date_range_start: str = ""
    date_range_end: str = ""
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
    
    # Static info for filters
    faction_options: list[list[str]] = [["Rebel Alliance", "Rebel Alliance"], ["Galactic Empire", "Galactic Empire"], ["Scum and Villainy", "Scum and Villainy"], ["Resistance", "Resistance"], ["First Order", "First Order"], ["Galactic Republic", "Galactic Republic"], ["Separatist Alliance", "Separatist Alliance"]]
    initiative_options: list[list[str]] = [[str(i), str(i)] for i in range(7)]
    
    @rx.var
    def upgrade_type_options(self) -> list[list[str]]:
        return [[t.label, t.value] for t in UpgradeType]
    
    
    # Sorting
    sort_mode: str = "Popularity"
    
    # Data Source (XWA vs Legacy)
    data_source: str = "xwa" # xwa, legacy

    # Data
    results: list[dict] = []
    total_count: int = 0

    def toggle_format_macro(self, macro_val: str, checked: bool):
        super().toggle_format_macro(macro_val, checked)

    def toggle_format_child(self, child_val: str, checked: bool):
        super().toggle_format_child(child_val, checked)
    
    def on_mount(self):
        # Initialize selected_formats to True for all if empty
        if not self.selected_formats:
            self.selected_formats = {m.value: True for m in MacroFormat} | {f.value: True for f in Format}
        
        # Initialize other multi-selects to empty (all) or full?
        # Logic is: empty/None = All. 
        # So we can leave them empty.
        
        # Trigger initial load
        self.load_data()
        
    def set_active_tab(self, tab: str):
        self.active_tab = tab
        self.results = []
        self.current_page = 0
        self.load_data()
        
    def set_sort_mode(self, mode: str):
        self.sort_mode = mode
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
        
    def toggle_initiative(self, init: str, checked: bool):
        self.selected_initiatives[init] = checked
        self.current_page = 0
        self.load_data()

    def toggle_upgrade_type(self, u_type: str, checked: bool):
        self.selected_upgrade_types[u_type] = checked
        self.current_page = 0
        self.load_data()

    def set_text_filter(self, text: str):
        self.text_filter = text
        self.current_page = 0
        self.load_data() # Debounce? Reflex handles debounce on input usually if configured
        
    def set_date_start(self, date: str):
        self.date_range_start = date
        self.load_data()
        
    def set_date_end(self, date: str):
        self.date_range_end = date
        self.load_data()
        
    @rx.var
    def all_ships(self) -> list[dict]:
        """Load all ships based on data source. Cached by backend lru_cache."""
        source_enum = DataSource(self.data_source) if isinstance(self.data_source, str) else self.data_source
        return load_all_ships(source_enum)

    def on_filter_change(self):
        """Handle format filter changes."""
        self.current_page = 0
        self.load_data()

    def set_data_source(self, source: str | list[str]):
        if isinstance(source, list):
            source = source[0]
        # Store as string for UI state simplicity if needed, but backend needs Enum
        # Segmented control returns string value.
        self.data_source = source 
        self.load_data()

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
    
    @rx.var
    def total_items_count(self) -> int:
         return self.total_count

    def on_page_change(self):
        self.load_data()

    def load_data(self):
        # Map UI Sort Mode to Backend Sort Mode
        sort_mapping = {
            "Popularity": "popularity",
            "Win Rate": "win_rate"
        }
        backend_sort = sort_mapping.get(self.sort_mode, "popularity")

        # Construction Allowed Formats List
        # Iterate selected_formats, if true add to list.
        # Note: Backend expects specific formats, not macros.
        allowed = []
        for k, v in self.selected_formats.items():
            if v and k in Format._value2member_map_:
                allowed.append(k)
        
        # If all formats are selected, we can pass None to optimize?
        # Or just pass the list.
        
        
        # Prepare multi-select lists
        active_factions = [k for k, v in self.selected_factions.items() if v]
        active_initiatives = [k for k, v in self.selected_initiatives.items() if v]
        active_upgrade_types = [k for k, v in self.selected_upgrade_types.items() if v]
        active_ships = [k for k, v in self.selected_ships.items() if v]

        filters = {
            "allowed_formats": allowed,
            "date_start": self.date_range_start,
            "date_end": self.date_range_end,
            "search_text": self.text_filter,
            "faction": active_factions,
            "ship": active_ships, # List of XWS IDs
            "initiative": active_initiatives,
            "upgrade_type": active_upgrade_types
        }
        
        # ... (inside load_data)
        # Convert data_source string to Enum
        try:
            ds_enum = DataSource(self.data_source)
        except ValueError:
            ds_enum = DataSource.XWA

        data = aggregate_card_stats(filters, backend_sort, self.active_tab, ds_enum)
        
        self.total_count = len(data)
        
        # Pagination
        # Pagination
        start = self.current_page * self.page_size
        self.results = data[start:start + self.page_size]

def render_filters() -> rx.Component:
    """Render the sidebar filters."""
    return rx.vstack(
        # 1. Data Source
        rx.vstack(
            rx.text("Data Source", size="1", color=TEXT_SECONDARY),
            rx.segmented_control.root(
                rx.segmented_control.item("XWA", value="xwa"),
                rx.segmented_control.item("Legacy", value="legacy"),
                value=CardAnalyzerState.data_source,
                on_change=CardAnalyzerState.set_data_source,
                width="100%",
                color_scheme="gray",
            ),
            spacing="1",
            width="100%"
        ),

        # 2. Sort
        rx.vstack(
            rx.text("Sort By", size="1", color=TEXT_SECONDARY),
            rx.select(
                ["Popularity", "Win Rate"],
                value=CardAnalyzerState.sort_mode,
                on_change=CardAnalyzerState.set_sort_mode,
                style=INPUT_STYLE,
                width="100%",
                color_scheme="gray",
            ),
            spacing="1",
            width="100%"
        ),

        rx.divider(border_color=BORDER_COLOR),
        rx.text("FILTERS", size="1", weight="bold", letter_spacing="1px", color=TEXT_SECONDARY),

        # 3. Search
        rx.input(
            placeholder="Search Name / Effect...",
            value=CardAnalyzerState.text_filter,
            on_change=CardAnalyzerState.set_text_filter,
            style=INPUT_STYLE,
            width="100%",
            color_scheme="gray",
        ),
        
        # 4. Date Range
        rx.vstack(
            rx.text("Date Range", size="1", color=TEXT_SECONDARY),
            rx.vstack(
                rx.input(type="date", value=CardAnalyzerState.date_range_start, on_change=CardAnalyzerState.set_date_start, style=INPUT_STYLE, width="100%"),
                rx.text("to", size="1", color=TEXT_SECONDARY, text_align="center"),
                rx.input(type="date", value=CardAnalyzerState.date_range_end, on_change=CardAnalyzerState.set_date_end, style=INPUT_STYLE, width="100%"),
                spacing="1",
                width="100%"
            ),
            spacing="1",
            width="100%"
        ),

        # 5. Format Filter
        rx.box(
            rx.text("Formats", size="1", color=TEXT_SECONDARY, margin_bottom="4px"),
            hierarchical_format_filter(
                CardAnalyzerState.selected_formats,
                CardAnalyzerState.toggle_format_macro,
                CardAnalyzerState.toggle_format_child
            ),
            width="100%",
            padding="8px",
            border=f"1px solid {BORDER_COLOR}",
            border_radius=RADIUS
        ),
        
        # 6. Context Specific Filters
        rx.cond(
            CardAnalyzerState.active_tab == "pilots",
            rx.vstack(
                # Faction
                filter_accordion(
                    "Factions",
                    CardAnalyzerState.faction_options,
                    CardAnalyzerState.selected_factions,
                    CardAnalyzerState.toggle_faction
                ),
                
                # Ship 
                searchable_filter_accordion(
                    "Ships",
                    CardAnalyzerState.available_ships,
                    CardAnalyzerState.selected_ships,
                    CardAnalyzerState.toggle_ship,
                    CardAnalyzerState.ship_search_text,
                    CardAnalyzerState.set_ship_search
                ),
                
                # Initiative
                filter_accordion(
                    "Initiative",
                    CardAnalyzerState.initiative_options,
                    CardAnalyzerState.selected_initiatives,
                    CardAnalyzerState.toggle_initiative
                ),
                spacing="3",
                width="100%"
            ),
            # Upgrade Filters
            filter_accordion(
                "Upgrade Type",
                CardAnalyzerState.upgrade_type_options,
                CardAnalyzerState.selected_upgrade_types,
                CardAnalyzerState.toggle_upgrade_type
            )
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
    
    return rx.box(
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
                    rx.badge(p["win_rate"].to(float).to(int).to(str) + "% WR", color_scheme=rx.cond(p["win_rate"].to(float) >= 50, "green", "orange"), variant="solid", radius="full"),
                    spacing="2",
                    justify="center",
                    width="100%"
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
        transition="transform 0.2s",
        _hover={"transform": "translateY(-4px)"}
    )

def upgrade_card(u: dict) -> rx.Component:
    return rx.box(
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
                    rx.badge(u["win_rate"].to(float).to(int).to(str) + "% WR", color_scheme=rx.cond(u["win_rate"].to(float) >= 50, "green", "orange"), variant="solid", radius="full"),
                    spacing="2",
                    justify="center",
                    width="100%"
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
        transition="transform 0.2s",
        _hover={"transform": "translateY(-4px)"}
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
        padding="20px",
        align="start"
    )

def card_analyzer_page() -> rx.Component:
    return layout(
        dashboard_layout(
             render_filters(),
             render_content()
        )
    )
