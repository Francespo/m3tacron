"""
Upgrade Detail Page.
"""
import reflex as rx
from ..components.format_filter import hierarchical_format_filter, FormatFilterMixin
from ..ui_utils.pagination import PaginationMixin
from ..components.pagination import pagination_controls
from ..components.sidebar import layout, dashboard_layout
from ..backend.data_structures.factions import Faction
from ..backend.data_structures.upgrade_types import UpgradeType
from ..backend.data_structures.data_source import DataSource
from ..backend.data_structures.formats import Format, MacroFormat
from ..backend.utils import load_all_upgrades, load_all_ships, load_all_pilots
from ..backend.data_structures.sorting_order import SortingCriteria, SortDirection
from ..backend.analytics.core import aggregate_card_stats
from ..backend.analytics.charts import get_card_usage_history
from ..theme import (
    TEXT_PRIMARY, TEXT_SECONDARY, BORDER_COLOR, TERMINAL_PANEL, TERMINAL_PANEL_STYLE,
    HEADER_FONT, MONOSPACE_FONT, SANS_FONT, INPUT_STYLE, RADIUS, FACTION_COLORS
)
from ..components.icons import ship_icon
from ..components.filter_accordion import filter_accordion
from ..components.searchable_filter_accordion import searchable_filter_accordion
from ..components.initiative_grid import initiative_grid
from ..components.usage_chart import usage_chart

class UpgradeDetailState(FormatFilterMixin):
    """
    State for the Upgrade Detail page.
    """
    # ID State
    upgrade_info: dict = {}
    upgrade_xws: str = ""
    loading: bool = True
    error: str = ""
    active_tab: str = "pilots" # pilots, paired_upgrades

    # Common Filters
    date_range_start: str = ""
    date_range_end: str = ""
    
    # Inverted Filters (Context: Upgrade -> Filter Pilots)
    selected_factions: dict[str, bool] = {}
    selected_initiatives: dict[str, bool] = {}
    ship_search_text: str = ""
    selected_ships: dict[str, bool] = {} 
    text_filter: str = ""
    
    # Sorting
    sort_metric: str = "Popularity"
    sort_direction: str = "desc"
    
    # Data Source (XWA vs Legacy)
    data_source: str = "xwa" # xwa, legacy
    
    # Comparison State
    comparison_selection: list[str] = [] # List of XWS IDs to compare on chart
    
    # Data
    results: list[dict] = []
    
    # Chart Data
    chart_data: list[dict] = []
    
    @rx.var
    def upgrade_type_options(self) -> list[list[str]]:
        return [[t.label, t.value] for t in UpgradeType]

    @rx.var
    def sort_metric_options(self) -> list[str]:
        """Available metrics."""
        opts = [
            "Cost",
            "Games",
            "Name",
            "Popularity",
            "Win Rate"
        ]
        # Pilot Detail upgrades so generally "Upgrades" might not have loadout.
        if self.data_source == "xwa" and self.active_tab == "pilots":
             opts.append("Loadout")
             opts.sort()
        return opts
        
    @rx.var
    def chart_series_list(self) -> list[dict]:
        series = [
             {"data_key": self.upgrade_xws, "name": self.upgrade_info.get("name", self.upgrade_xws), "color": "#00E0FF" if self.upgrade_info else "#00E0FF"}
        ]
        # Add comparisons
        colors = ["#FF5733", "#33FF57", "#FFFF33", "#FF33FF"]
        for i, comp in enumerate(self.comparison_selection):
             c = colors[i % len(colors)]
             series.append({"data_key": comp, "name": comp, "color": c})
        return series

    # Static Options
    faction_options: list[list[str]] = [["Rebel Alliance", "Rebel Alliance"], ["Galactic Empire", "Galactic Empire"], ["Scum and Villainy", "Scum and Villainy"], ["Resistance", "Resistance"], ["First Order", "First Order"], ["Galactic Republic", "Galactic Republic"], ["Separatist Alliance", "Separatist Alliance"]]

    def load_upgrade(self):
        # 1. Get ID from params
        uid_str = ""
        if hasattr(self.router.page, "params") and isinstance(self.router.page.params, dict):
            uid_str = self.router.page.params.get("id", "")

        # Fallback to URL parsing if params are empty
        if not uid_str:
             raw_path = self.router.page.raw_path
             if "/upgrade/" in raw_path:
                 uid_str = raw_path.split("/upgrade/")[1].split("?")[0].split("/")[0]

        if not uid_str:
            self.error = "No upgrade ID provided"
            self.loading = False
            return
            
        self.upgrade_xws = uid_str.strip('"').strip("'")
        print(f"DEBUG: Loading upgrade details for XWS: {self.upgrade_xws}")
        
        # 2. Convert Data Source
        try:
            ds_enum = DataSource(self.data_source)
        except ValueError:
             ds_enum = DataSource.XWA

        # 3. Load Info
        all_upgrades = load_all_upgrades(ds_enum)
        print(f"DEBUG: All upgrades loaded. Count: {len(all_upgrades)}")
        
        info = all_upgrades.get(self.upgrade_xws)
        if info:
            self.upgrade_info = info
            print(f"DEBUG: Found upgrade info for {self.upgrade_xws}: {info.get('name')}")
        else:
            print(f"DEBUG: Upgrade {self.upgrade_xws} NOT FOUND in data source {ds_enum}")
            self.upgrade_info = {"name": self.upgrade_xws, "xws": self.upgrade_xws, "image": ""}
        
        # 4. Initialize Formats if empty
        if not self.selected_formats:
             self.selected_formats = {m.value: True for m in MacroFormat} | {f.value: True for f in Format}
             
        self.load_data()
        self.loading = False

    def set_active_tab(self, tab: str):
        self.active_tab = tab
        self.results = []
        self.current_page = 0
        self.load_data()

    def load_data(self):
        if not self.upgrade_xws: return

        # Map UI Sort Mode to Backend Sort Mode
        criteria = SortingCriteria.from_label(self.sort_metric)
        direction = SortDirection(self.sort_direction)

        # Construction Allowed Formats List
        allowed = []
        for k, v in self.selected_formats.items():
            if v and k in Format._value2member_map_:
                allowed.append(k)
        
        # Prepare filters
        active_factions = [k for k, v in self.selected_factions.items() if v]
        active_initiatives = [k for k, v in self.selected_initiatives.items() if v]
        active_ships = [k for k, v in self.selected_ships.items() if v]

        filters = {
            "allowed_formats": allowed,
            "date_start": self.date_range_start,
            "date_end": self.date_range_end,
            "search_text": self.text_filter,
            "faction": active_factions,
            "ship": active_ships, 
            "initiative": active_initiatives,
            "upgrade_id": self.upgrade_xws # KEY: Filter Pilots/Upgrades for this Upgrade
        }
        
        # Convert Data Source
        try:
            ds_enum = DataSource(self.data_source)
        except ValueError:
            ds_enum = DataSource.XWA

        # 1. Load Stats based on Tab
        mode = "pilots" if self.active_tab == "pilots" else "upgrades"
        data = aggregate_card_stats(filters, criteria, direction, mode, ds_enum)
        
        self.total_items_count = len(data)
        
        # Pagination
        start = self.current_page * self.page_size
        self.results = data[start:start + self.page_size]
        
        # 2. Load Chart Data
        # Chart shows usage of MAIN UPGRADE + Selected Comparisons (Pilots or Upgrades)
        self.chart_data = get_card_usage_history(filters, self.upgrade_xws, self.comparison_selection, is_upgrade=True)
    
    @rx.var
    def all_ships(self) -> list[dict]:
        """Load all ships based on data source. Cached by backend lru_cache."""
        source_enum = DataSource(self.data_source) if isinstance(self.data_source, str) else self.data_source
        return load_all_ships(source_enum)

    @rx.var
    def available_ships(self) -> list[list[str]]:
        # Reuse logic from card_analyzer basically
        ships = self.all_ships
        active_factions = {k for k, v in self.selected_factions.items() if v}
        filtered = []
        if not active_factions:
            filtered = ships
        else:
             def norm(s): return s.lower().replace(" ", "").replace("-", "")
             norm_active = {norm(f) for f in active_factions}
             for s in ships:
                 s_factions_norm = {norm(f) for f in s["factions"]}
                 if not s_factions_norm.isdisjoint(norm_active):
                     filtered.append(s)
        
        final = []
        query = self.ship_search_text.lower()
        for s in filtered:
            if query in s["name"].lower():
                 final.append([s["name"], s["xws"]])
        return final

    def toggle_comparison(self, xws: str):
        if xws in self.comparison_selection:
            self.comparison_selection.remove(xws)
        else:
            if len(self.comparison_selection) < 4:
                self.comparison_selection.append(xws)
        self.load_data()

    def set_sort_metric(self, metric: str):
        self.sort_metric = metric
        self.load_data()

    def toggle_sort_direction(self):
        self.sort_direction = "asc" if self.sort_direction == "desc" else "desc"
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

    def set_text_filter(self, text: str):
        self.text_filter = text
        self.current_page = 0
        self.load_data() 
        
    def set_date_start(self, date: str):
        self.date_range_start = date
        self.load_data()
        
    def set_date_end(self, date: str):
        self.date_range_end = date
        self.load_data()
    
    def on_filter_change(self):
        self.current_page = 0
        self.load_data()
        
    def set_data_source(self, source: str | list[str]):
        if isinstance(source, list): source = source[0]
        self.data_source = source 
        self.load_upgrade()

    def on_page_change(self):
        self.load_data()

    def toggle_format_macro(self, macro_val: str, checked: bool):
        super().toggle_format_macro(macro_val, checked)

    def toggle_format_child(self, child_val: str, checked: bool):
        super().toggle_format_child(child_val, checked)

def render_filters() -> rx.Component:
    """Render the sidebar filters (Context: Upgrade Details)."""
    return rx.vstack(
        # 1. Content Source
        rx.vstack(
            rx.text("GAME CONTENT SOURCE", size="2", weight="bold", letter_spacing="1px", color=TEXT_PRIMARY),
            rx.segmented_control.root(
                rx.segmented_control.item("XWA", value="xwa"),
                rx.segmented_control.item("Legacy", value="legacy"),
                value=UpgradeDetailState.data_source,
                on_change=UpgradeDetailState.set_data_source,
                width="100%",
                color_scheme="gray",
            ),
            spacing="1",
            width="100%"
        ),

        rx.divider(border_color=BORDER_COLOR),

        # 2. Tournament Data Filters (Group Header)
        rx.text("TOURNAMENT FILTERS", size="2", weight="bold", letter_spacing="1px", color=TEXT_PRIMARY),
        
        # Date Range
        rx.vstack(
            rx.text("Date Range", size="1", weight="bold", color=TEXT_SECONDARY),
            rx.vstack(
                rx.input(type="date", value=UpgradeDetailState.date_range_start, on_change=UpgradeDetailState.set_date_start, style=INPUT_STYLE, width="100%"),
                rx.text("to", size="1", color=TEXT_SECONDARY, text_align="center"),
                rx.input(type="date", value=UpgradeDetailState.date_range_end, on_change=UpgradeDetailState.set_date_end, style=INPUT_STYLE, width="100%"),
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
            hierarchical_format_filter(UpgradeDetailState),
            width="100%",
        ),
        
        # 3. Context Filters (Pilots using this Upgrade)
        rx.vstack(
            rx.text("PILOT FILTERS", size="2", weight="bold", letter_spacing="1px", color=TEXT_PRIMARY),
            
            # Sort By
            rx.vstack(
                rx.text("Sort By", size="1", weight="bold", letter_spacing="1px", color=TEXT_SECONDARY),
                rx.hstack(
                     rx.select(
                        UpgradeDetailState.sort_metric_options,
                        value=UpgradeDetailState.sort_metric,
                        on_change=UpgradeDetailState.set_sort_metric,
                        style=INPUT_STYLE,
                        flex="1",
                        color_scheme="gray",
                    ),
                    rx.icon_button(
                        rx.cond(
                            UpgradeDetailState.sort_direction == "asc",
                            rx.icon(tag="arrow-up"),
                            rx.icon(tag="arrow-down")
                        ),
                        on_click=UpgradeDetailState.toggle_sort_direction,
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

            # Text Search
            rx.vstack(
                rx.text("Text Search", size="1", weight="bold", color=TEXT_SECONDARY),
                rx.input(
                    placeholder="Search Pilot/Upgrade...",
                    value=UpgradeDetailState.text_filter,
                    on_change=UpgradeDetailState.set_text_filter,
                    style=INPUT_STYLE,
                    width="100%",
                    color_scheme="gray",
                ),
                spacing="1",
                width="100%"
            ),

            # Pilot Filters (Only relevant for Pilots Tab really, but keeping logic simpler)
            # Faction
            filter_accordion(
                "Faction",
                UpgradeDetailState.faction_options,
                UpgradeDetailState.selected_factions,
                UpgradeDetailState.toggle_faction
            ),
            
            # Ship 
            searchable_filter_accordion(
                "Ships",
                UpgradeDetailState.available_ships,
                UpgradeDetailState.selected_ships,
                UpgradeDetailState.toggle_ship,
                UpgradeDetailState.ship_search_text,
                UpgradeDetailState.set_ship_search
            ),
            
            # Initiative Grid
            initiative_grid(
                "Initiative",
                UpgradeDetailState.selected_initiatives,
                UpgradeDetailState.toggle_initiative
            ),
            
            width="100%",
            align_items="start",
            spacing="3"
        ),
        
        spacing="4",
        width="100%", 
        min_width="250px",
        height="100%",
    )

def comparison_button(item: dict) -> rx.Component:
    is_selected = UpgradeDetailState.comparison_selection.contains(item["xws"])
    return rx.button(
       rx.cond(is_selected, "REMOVE COMPARISON", "COMPARE"),
       variant=rx.cond(is_selected, "solid", "outline"),
       color_scheme=rx.cond(is_selected, "red", "gray"),
       size="1",
       on_click=lambda: UpgradeDetailState.toggle_comparison(item["xws"]),
       width="100%"
   )

def pilot_card_item(p: dict) -> rx.Component:
    normalized_faction = p["faction"].to(str).lower().replace(" ", "").replace("-", "")
    color = FACTION_COLORS.get(normalized_faction, TEXT_SECONDARY)
    is_selected = UpgradeDetailState.comparison_selection.contains(p["xws"])
    
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
                    rx.badge(p["cost"].to(str) + " PTS", color_scheme="blue", variant="solid", radius="full"),
                    rx.cond(
                         UpgradeDetailState.data_source == "xwa",
                         rx.badge(p["loadout"].to(str) + " LV", color_scheme="purple", variant="solid", radius="full"),
                         rx.fragment()
                    ),
                    spacing="2",
                    justify="center",
                    width="100%",
                    wrap="wrap"
                ),
                comparison_button(p),
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
        border=rx.cond(is_selected, "1px solid #00E0FF", f"1px solid {BORDER_COLOR}"),
        transition="transform 0.2s",
        _hover={"transform": "translateY(-4px)"}
    )

def paired_upgrade_card_item(u: dict) -> rx.Component:
    is_selected = UpgradeDetailState.comparison_selection.contains(u["xws"])
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
                    rx.badge(u["cost"].to(str) + " PTS", color_scheme="blue", variant="solid", radius="full"),
                    spacing="2",
                    justify="center",
                    width="100%",
                    wrap="wrap"
                ),
                comparison_button(u),
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
        border=rx.cond(is_selected, "1px solid #00E0FF", f"1px solid {BORDER_COLOR}"),
        transition="transform 0.2s",
        _hover={"transform": "translateY(-4px)"}
    )

def upgrade_detail_content() -> rx.Component:
    return rx.cond(
        UpgradeDetailState.loading,
        rx.spinner(),
        rx.cond(
            UpgradeDetailState.error != "",
            rx.text(UpgradeDetailState.error, color="red"),
            rx.vstack(
                # Header
                rx.hstack(
                    rx.link(rx.button("< BACK", variant="ghost", size="1", style={"font_family": MONOSPACE_FONT}), href="/cards"),
                    rx.heading(UpgradeDetailState.upgrade_info["name"], size="8", font_family=SANS_FONT, weight="bold"),
                    rx.badge("UPGRADE", color_scheme="cyan", variant="solid", size="2"),
                     spacing="4", width="100%", align="center", margin_bottom="24px"
                ),
                
                # Main Info + Chart Area
                rx.grid(
                    # Left: Upgrade Image
                    rx.box(
                         rx.cond(
                            UpgradeDetailState.upgrade_info["image"].to(str) != "",
                            rx.image(src=UpgradeDetailState.upgrade_info["image"].to(str), width="100%", border_radius="12px", max_width="300px"),
                            rx.box(
                                rx.text("NO IMAGE", color=TEXT_SECONDARY),
                                width="100%", height="400px", bg="rgba(255,255,255,0.05)", border_radius="12px",
                                display="flex", align_items="center", justify_content="center"
                            )
                         ),
                        width="100%",
                        display="flex",
                        justify_content="center"
                    ),
                    
                    # Right: Chart
                    rx.vstack(
                        rx.text("USAGE OVER TIME", size="3", font_family=SANS_FONT, weight="bold", color=TEXT_PRIMARY),
                        rx.box(
                            usage_chart(UpgradeDetailState.chart_data, UpgradeDetailState.chart_series_list),
                            width="100%",
                            height="300px",
                            padding="16px",
                            style=TERMINAL_PANEL_STYLE,
                            border_radius=RADIUS
                        ),
                        rx.text("Select items below to compare usage in combination with this upgrade.", size="1", color=TEXT_SECONDARY),
                        width="100%",
                        spacing="2"
                    ),
                    columns={"initial": "1", "md": "1", "lg": "1fr 2fr"},
                    spacing="6",
                    width="100%",
                    margin_bottom="32px",
                    align_items="start"
                ),

                rx.divider(border_color=BORDER_COLOR, margin_bottom="24px"),
                
                # Tabs for Pilots vs Paired Upgrades
                rx.tabs.root(
                    rx.tabs.list(
                        rx.tabs.trigger("Pilots", value="pilots", width="120px"),
                        rx.tabs.trigger("Paired Upgrades", value="paired_upgrades", width="160px"),
                    ),
                    value=UpgradeDetailState.active_tab,
                    on_change=UpgradeDetailState.set_active_tab,
                    width="100%",
                    color_scheme="gray",
                ),

                rx.spacer(height="16px"),
                
                # Content Grid
                rx.grid(
                    rx.cond(
                        UpgradeDetailState.active_tab == "pilots",
                        rx.foreach(UpgradeDetailState.results.to(list[dict]), pilot_card_item),
                        rx.foreach(UpgradeDetailState.results.to(list[dict]), paired_upgrade_card_item)
                    ),
                    columns={"initial": "1", "sm": "2", "xl": "3", "2xl": "4"},
                    spacing="4",
                    width="100%"
                ),
                
                 # Pagination
                pagination_controls(UpgradeDetailState),
                
                width="100%",
                padding="20px",
                align="start"
            )
        )
    )

def upgrade_detail_page() -> rx.Component:
    return layout(
        dashboard_layout(
             render_filters(),
             upgrade_detail_content()
        ),
        on_mount=UpgradeDetailState.load_upgrade
    )
