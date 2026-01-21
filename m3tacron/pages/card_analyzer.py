"""
Card Analyzer Page.
"""
import reflex as rx
from ..backend.card_analytics import aggregate_card_stats
from ..backend.enums.formats import FORMAT_HIERARCHY
from ..components.format_filter import hierarchical_format_filter
from ..components.sidebar import layout
from ..theme import (
    TEXT_PRIMARY, TEXT_SECONDARY, BORDER_COLOR, TERMINAL_PANEL, TERMINAL_PANEL_STYLE,
    HEADER_FONT, MONOSPACE_FONT, SANS_FONT, INPUT_STYLE, RADIUS, FACTION_COLORS
)
from ..components.icons import ship_icon

class CardAnalyzerState(rx.State):
    """
    State for the Card Analyzer page.
    """
    # Active Tab
    active_tab: str = "pilots" # pilots, upgrades
    
    # Common Filters
    date_range_start: str = ""
    date_range_end: str = ""
    text_filter: str = ""
    
    # Format Filter State (Hierarchical)
    # Map of format_value -> boolean. 
    # Must initialize with Defaults? Or empty = all?
    # Let's initialize all to True for better UX (show everything by default)
    selected_formats: dict[str, bool] = {}
    
    # Pilot Specific
    faction_filter: str = "all"
    
    # Upgrade Specific
    upgrade_type_filter: str = "all"
    
    # Sorting
    sort_mode: str = "popularity"
    
    # Data
    results: list[dict] = []
    total_count: int = 0
    
    # Pagination
    page: int = 0
    page_size: int = 24
    
    def on_mount(self):
        # Initialize selected_formats to True for all if empty
        if not self.selected_formats:
            for macro in FORMAT_HIERARCHY:
                self.selected_formats[macro["value"]] = True
                for child in macro["children"]:
                    self.selected_formats[child["value"]] = True
        self.load_data()
        
    def set_active_tab(self, tab: str):
        self.active_tab = tab
        self.page = 0
        self.load_data()
        
    def set_sort_mode(self, mode: str):
        self.sort_mode = mode
        self.load_data()
        
    def set_faction_filter(self, faction: str):
        self.faction_filter = faction
        self.page = 0
        self.load_data()

    def set_upgrade_type_filter(self, u_type: str):
        self.upgrade_type_filter = u_type
        self.page = 0
        self.load_data()

    def set_text_filter(self, text: str):
        self.text_filter = text
        self.page = 0
        self.load_data() # Debounce? Reflex handles debounce on input usually if configured
        
    def set_date_start(self, date: str):
        self.date_range_start = date
        self.load_data()
        
    def set_date_end(self, date: str):
        self.date_range_end = date
        self.load_data()
        
    # Format Filter Logic
    def toggle_format_macro(self, macro_val: str, checked: bool):
        self.selected_formats[macro_val] = checked
        # Toggle all children
        # Find children for this macro
        # (Need to traverse FORMAT_HIERARCHY)
        for m in FORMAT_HIERARCHY:
            if m["value"] == macro_val:
                for child in m["children"]:
                    self.selected_formats[child["value"]] = checked
        self.load_data()

    def toggle_format_child(self, child_val: str, checked: bool, macro_val: str):
        self.selected_formats[child_val] = checked
        # If unchecked, uncheck macro? If checked, check macro if all checked?
        # Simple rule: if unchecked, uncheck macro.
        if not checked:
            self.selected_formats[macro_val] = False
        else:
            # Check if all siblings valid?
            pass 
        self.load_data()
    
    def next_page(self):
        self.page += 1
        
    def prev_page(self):
        if self.page > 0:
            self.page -= 1

    def load_data(self):
        # Construct Allowed Formats List
        # Iterate selected_formats, if true add to list.
        # Note: Backend expects specific formats, not macros.
        allowed = []
        for k, v in self.selected_formats.items():
            if v:
                allowed.append(k)
        
        # If all formats are selected, we can pass None to optimize?
        # Or just pass the list.
        
        filters = {
            "allowed_formats": allowed,
            "date_start": self.date_range_start,
            "date_end": self.date_range_end,
            "search_text": self.text_filter,
            "faction": self.faction_filter,
            "upgrade_type": self.upgrade_type_filter
        }
        
        data = aggregate_card_stats(filters, self.sort_mode, self.active_tab)
        
        self.total_count = len(data)
        
        # Pagination
        # Pagination
        start = self.page * self.page_size
        self.results = data[start:start + self.page_size]

def render_filters() -> rx.Component:
    """Render the sidebar filters."""
    return rx.vstack(
        # Search
        rx.input(
            placeholder="Search Name or Effect...",
            value=CardAnalyzerState.text_filter,
            on_change=CardAnalyzerState.set_text_filter,
            style=INPUT_STYLE,
            width="100%"
        ),
        
        # Date Range
        rx.vstack(
            rx.text("Date Range", size="1", color=TEXT_SECONDARY),
            rx.hstack(
                rx.input(type="date", value=CardAnalyzerState.date_range_start, on_change=CardAnalyzerState.set_date_start, style=INPUT_STYLE, width="100%"),
                rx.text("-", color=TEXT_SECONDARY),
                rx.input(type="date", value=CardAnalyzerState.date_range_end, on_change=CardAnalyzerState.set_date_end, style=INPUT_STYLE, width="100%"),
            ),
            spacing="1",
            width="100%"
        ),
        
        # Tab Specific Filters
        rx.cond(
            CardAnalyzerState.active_tab == "pilots",
            # Faction Selector
            rx.select(
                ["all", "Rebel Alliance", "Galactic Empire", "Scum and Villainy", "Resistance", "First Order", "Galactic Republic", "Separatist Alliance"],
                value=CardAnalyzerState.faction_filter,
                on_change=CardAnalyzerState.set_faction_filter,
                style=INPUT_STYLE,
                width="100%"
            ),
            # Upgrade Type Selector
            rx.select(
                ["all", "Talent", "Force", "System", "Cannon", "Turret", "Torpedo", "Missile", "Crew", "Gunner", "Astromech", "Device", "Illicit", "Modification", "Title", "Configuration", "Sensor", "Tech"],
                value=CardAnalyzerState.upgrade_type_filter,
                on_change=CardAnalyzerState.set_upgrade_type_filter,
                style=INPUT_STYLE,
                width="100%"
            )
        ),
        
        # Sort
        rx.vstack(
            rx.text("Sort By", size="1", color=TEXT_SECONDARY),
            rx.select(
                ["Popularity", "Win Rate"],
                value=CardAnalyzerState.sort_mode,
                on_change=CardAnalyzerState.set_sort_mode,
                style=INPUT_STYLE,
                width="100%"
            ),
            spacing="1",
            width="100%"
        ),

        # Format Filter
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
        
        spacing="4",
        width="280px", # Increased width slightly for better fit
        min_width="280px",
        padding="24px", # Increased padding
        border_right=f"1px solid {BORDER_COLOR}",
        height="100vh", # Full viewport height
        position="sticky", # Sticky sidebar
        top="0",
        overflow_y="auto"
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
                width="100%" 
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
        rx.hstack(
            rx.button("Previous", on_click=CardAnalyzerState.prev_page, disabled=CardAnalyzerState.page == 0),
            rx.text(f"Page {CardAnalyzerState.page + 1}", color=TEXT_SECONDARY),
            rx.button("Next", on_click=CardAnalyzerState.next_page),
            justify="center",
            width="100%",
            padding_top="20px"
        ),
        
        width="100%",
        padding="20px",
        align="start"
    )

def card_analyzer_page() -> rx.Component:
    return layout(
        rx.flex(
            render_filters(),
            render_content(),
            width="100%",
            height="100%",
            align="start"
        )
    )
