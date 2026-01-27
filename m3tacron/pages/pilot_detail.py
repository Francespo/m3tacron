"""
Pilot Detail Page.
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
from ..backend.utils import load_all_pilots
from ..backend.analytics.core import aggregate_card_stats
from ..backend.analytics.charts import get_card_usage_history
from ..theme import (
    TEXT_PRIMARY, TEXT_SECONDARY, BORDER_COLOR, TERMINAL_PANEL, TERMINAL_PANEL_STYLE,
    HEADER_FONT, MONOSPACE_FONT, SANS_FONT, INPUT_STYLE, RADIUS, FACTION_COLORS
)
from ..components.icons import ship_icon
from ..components.filter_accordion import filter_accordion
from ..components.usage_chart import usage_chart

class PilotDetailState(FormatFilterMixin):
    """
    State for the Pilot Detail page.
    """
    # ID State
    pilot_info: dict = {}
    pilot_xws: str = ""
    loading: bool = True
    error: str = ""

    # Common Filters
    date_range_start: str = ""
    date_range_end: str = ""
    
    # Inverted Filters (Context: Pilot -> Filter Upgrades)
    selected_upgrade_types: dict[str, bool] = {}
    text_filter: str = ""
    
    # Sorting
    sort_mode: str = "Popularity"
    
    # Data Source (XWA vs Legacy)
    data_source: str = "xwa" # xwa, legacy
    
    # Comparison State
    comparison_selection: list[str] = [] # List of XWS IDs to compare on chart
    
    # Data
    results: list[dict] = []
    total_count: int = 0
    
    # Chart Data
    chart_data: list[dict] = []
    
    @rx.var
    def upgrade_type_options(self) -> list[list[str]]:
        return [[t.label, t.value] for t in UpgradeType]
    
    @rx.var
    def chart_series_list(self) -> list[dict]:
        series = [
             {"data_key": self.pilot_xws, "name": self.pilot_info.get("name", self.pilot_xws), "color": "#00E0FF" if self.pilot_info else "#00E0FF"}
        ]
        # Add comparisons
        colors = ["#FF5733", "#33FF57", "#FFFF33", "#FF33FF"]
        for i, comp in enumerate(self.comparison_selection):
             c = colors[i % len(colors)]
             series.append({"data_key": comp, "name": comp, "color": c})
        return series

    def load_pilot(self):
        # 1. Get ID from params
        pid_str = ""
        if hasattr(self.router.page, "params") and isinstance(self.router.page.params, dict):
            pid_str = self.router.page.params.get("id", "")
            
        # Fallback to URL parsing if params are empty
        if not pid_str:
             raw_path = self.router.page.raw_path
             if "/pilot/" in raw_path:
                 pid_str = raw_path.split("/pilot/")[1].split("?")[0].split("/")[0]
        
        if not pid_str:
            self.error = "No pilot ID provided"
            self.loading = False
            return
            
        self.pilot_xws = pid_str.strip('"').strip("'")
        print(f"DEBUG: Loading pilot details for XWS: {self.pilot_xws}")
        
        # 2. Convert Data Source
        try:
            ds_enum = DataSource(self.data_source)
        except ValueError:
             ds_enum = DataSource.XWA

        # 3. Load Info
        all_pilots = load_all_pilots(ds_enum)
        print(f"DEBUG: All pilots loaded. Count: {len(all_pilots)}")
        
        info = all_pilots.get(self.pilot_xws)
        if info:
            self.pilot_info = info
            print(f"DEBUG: Found pilot info for {self.pilot_xws}: {info.get('name')}")
        else:
            print(f"DEBUG: Pilot {self.pilot_xws} NOT FOUND in data source {ds_enum}")
            self.pilot_info = {"name": self.pilot_xws, "xws": self.pilot_xws, "image": ""}
        
        # 4. Initialize Formats if empty
        if not self.selected_formats:
             self.selected_formats = {m.value: True for m in MacroFormat} | {f.value: True for f in Format}
             
        self.load_data()
        self.loading = False

    def load_data(self):
        if not self.pilot_xws: return

        # Map UI Sort Mode to Backend Sort Mode
        sort_mapping = {
            "Popularity": "popularity",
            "Win Rate": "win_rate"
        }
        backend_sort = sort_mapping.get(self.sort_mode, "popularity")

        # Construction Allowed Formats List
        allowed = []
        for k, v in self.selected_formats.items():
            if v and k in Format._value2member_map_:
                allowed.append(k)
        
        # Prepare filters
        active_upgrade_types = [k for k, v in self.selected_upgrade_types.items() if v]

        filters = {
            "allowed_formats": allowed,
            "date_start": self.date_range_start,
            "date_end": self.date_range_end,
            "search_text": self.text_filter,
            "upgrade_type": active_upgrade_types,
            "pilot_id": self.pilot_xws # KEY: Filter Upgrades for this Pilot
        }
        
        # Convert Data Source
        try:
            ds_enum = DataSource(self.data_source)
        except ValueError:
            ds_enum = DataSource.XWA

        # 1. Load Upgrade Stats
        data = aggregate_card_stats(filters, backend_sort, "upgrades", ds_enum)
        
        self.total_count = len(data)
        
        # Pagination
        start = self.current_page * self.page_size
        self.results = data[start:start + self.page_size]
        
        # 2. Load Chart Data
        # For chart, we generally ignore pagination but respect date/format filters
        # Comparison logic: compare with selected upgrades? Or user selects comparison?
        # For now, just load main pilot history
        self.chart_data = get_card_usage_history(filters, self.pilot_xws, self.comparison_selection, is_upgrade=False)

    def toggle_comparison(self, xws: str):
        if xws in self.comparison_selection:
            self.comparison_selection.remove(xws)
        else:
            if len(self.comparison_selection) < 4:
                self.comparison_selection.append(xws)
        self.load_data()

    def set_sort_mode(self, mode: str):
        self.sort_mode = mode
        self.load_data()
        
    def toggle_upgrade_type(self, u_type: str, checked: bool):
        self.selected_upgrade_types[u_type] = checked
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
        self.load_pilot()

    def on_page_change(self):
        self.load_data()

    def toggle_format_macro(self, macro_val: str, checked: bool):
        super().toggle_format_macro(macro_val, checked)

    def toggle_format_child(self, child_val: str, checked: bool):
        super().toggle_format_child(child_val, checked)

def render_filters() -> rx.Component:
    """Render the sidebar filters (Context: Pilot Details)."""
    return rx.vstack(
        # 1. Card Images Source
        rx.vstack(
            rx.text("CARD IMAGES SOURCE", size="2", weight="bold", letter_spacing="1px", color=TEXT_PRIMARY),
            rx.segmented_control.root(
                rx.segmented_control.item("XWA", value="xwa"),
                rx.segmented_control.item("Legacy", value="legacy"),
                value=PilotDetailState.data_source,
                on_change=PilotDetailState.set_data_source,
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
                rx.input(type="date", value=PilotDetailState.date_range_start, on_change=PilotDetailState.set_date_start, style=INPUT_STYLE, width="100%"),
                rx.text("to", size="1", color=TEXT_SECONDARY, text_align="center"),
                rx.input(type="date", value=PilotDetailState.date_range_end, on_change=PilotDetailState.set_date_end, style=INPUT_STYLE, width="100%"),
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
            hierarchical_format_filter(PilotDetailState),
            width="100%",
        ),
        
        # 3. Context Filters (Upgrades on this Pilot)
        rx.vstack(
            rx.text("UPGRADE FILTERS", size="2", weight="bold", letter_spacing="1px", color=TEXT_PRIMARY),
            
            # Sort By
            rx.vstack(
                rx.text("Sort By", size="1", weight="bold", letter_spacing="1px", color=TEXT_SECONDARY),
                rx.select(
                    ["Popularity", "Win Rate"],
                    value=PilotDetailState.sort_mode,
                    on_change=PilotDetailState.set_sort_mode,
                    style=INPUT_STYLE,
                    width="100%",
                    color_scheme="gray",
                ),
                spacing="1",
                width="100%"
            ),

            # Text Search
            rx.vstack(
                rx.text("Text Search", size="1", weight="bold", color=TEXT_SECONDARY),
                rx.input(
                    placeholder="Search Upgrade...",
                    value=PilotDetailState.text_filter,
                    on_change=PilotDetailState.set_text_filter,
                    style=INPUT_STYLE,
                    width="100%",
                    color_scheme="gray",
                ),
                spacing="1",
                width="100%"
            ),

            # Upgrade Types Only
            filter_accordion(
                "Upgrade Type",
                PilotDetailState.upgrade_type_options,
                PilotDetailState.selected_upgrade_types,
                PilotDetailState.toggle_upgrade_type
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

def upgrade_card_item(u: dict) -> rx.Component:
    is_selected = PilotDetailState.comparison_selection.contains(u["xws"])
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
                rx.button(
                    rx.cond(is_selected, "REMOVE COMPARISON", "COMPARE"),
                    variant=rx.cond(is_selected, "solid", "outline"),
                    color_scheme=rx.cond(is_selected, "red", "gray"),
                    size="1",
                    on_click=lambda: PilotDetailState.toggle_comparison(u["xws"]),
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
        border=rx.cond(is_selected, "1px solid #00E0FF", f"1px solid {BORDER_COLOR}"),
        transition="transform 0.2s",
        _hover={"transform": "translateY(-4px)"}
    )

def pilot_detail_content() -> rx.Component:
    return rx.cond(
        PilotDetailState.loading,
        rx.spinner(),
        rx.cond(
            PilotDetailState.error != "",
            rx.text(PilotDetailState.error, color="red"),
            rx.vstack(
                # Header
                rx.hstack(
                    rx.link(rx.button("< BACK", variant="ghost", size="1", style={"font_family": MONOSPACE_FONT}), href="/cards"),
                    rx.heading(PilotDetailState.pilot_info["name"], size="8", font_family=SANS_FONT, weight="bold"),
                    rx.badge("PILOT", color_scheme="blue", variant="solid", size="2"),
                     spacing="4", width="100%", align="center", margin_bottom="24px"
                ),
                
                # Main Info + Chart Area
                rx.grid(
                    # Left: Pilot Image & Basic Info
                    rx.box(
                         rx.cond(
                            PilotDetailState.pilot_info["image"].to(str) != "",
                            rx.image(src=PilotDetailState.pilot_info["image"].to(str), width="100%", border_radius="12px", max_width="300px"),
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
                            usage_chart(PilotDetailState.chart_data, PilotDetailState.chart_series_list),
                            width="100%",
                            height="300px",
                            padding="16px",
                            style=TERMINAL_PANEL_STYLE,
                            border_radius=RADIUS
                        ),
                        rx.text("Select upgrades below to compare usage in combination with this pilot.", size="1", color=TEXT_SECONDARY),
                        width="100%",
                        spacing="2"
                    ),
                    columns={"initial": "1", "md": "1", "lg": "1fr 2fr"}, # Stack on mobile, side-by-side on larger screens
                    spacing="6",
                    width="100%",
                    margin_bottom="32px",
                    align_items="start"
                ),

                rx.divider(border_color=BORDER_COLOR, margin_bottom="24px"),
                
                rx.heading("TOP COMPATIBLE UPGRADES", size="5", font_family=SANS_FONT, margin_bottom="16px", color=TEXT_PRIMARY),
                
                # Upgrade Grid
                rx.grid(
                    rx.foreach(PilotDetailState.results.to(list[dict]), upgrade_card_item),
                    columns={"initial": "1", "sm": "2", "xl": "3", "2xl": "4"},
                    spacing="4",
                    width="100%"
                ),
                
                 # Pagination
                pagination_controls(PilotDetailState),
                
                width="100%",
                padding="20px",
                align="start"
            )
        )
    )

def pilot_detail_page() -> rx.Component:
    return layout(
        dashboard_layout(
             render_filters(),
             pilot_detail_content()
        ),
        on_mount=PilotDetailState.load_pilot
    )
