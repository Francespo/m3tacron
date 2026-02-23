"""
M3taCron Home Page.
"""
import reflex as rx
from sqlmodel import Session, select, func

from ..components.sidebar import layout
from ..components.ui import content_panel, list_row
from ..backend.database import engine
from ..backend.models import Tournament, PlayerResult
from ..theme import (
    TEXT_PRIMARY, TEXT_SECONDARY, MONOSPACE_FONT, SANS_FONT
)


from ..backend.analytics import get_meta_snapshot
from ..components.dashboard_components import (
    meta_stat_card, 
    faction_performance_chart, 
    faction_game_pie_chart,
    sort_toggle,
    top_list_row,
    top_item_row
)
from ..components.list_renderer import list_row_card, enrich_list_data, ListData
from ..components.ui import content_panel
from ..backend.state.global_filter_state import GlobalFilterState

def data_source_toggle() -> rx.Component:
    """Toggle between XWA and Legacy content."""
    return rx.segmented_control.root(
        rx.segmented_control.item("XWA", value="xwa"),
        rx.segmented_control.item("Legacy", value="legacy"),
        value=GlobalFilterState.data_source,
        on_change=HomeState.on_source_change,
        size="2",
        variant="surface",
    )

class HomeState(rx.State):
    """Snapshot of the current meta (last 90 days)."""
    processed: bool = False
    
    # Snapshot data
    factions: list[dict] = []
    faction_distribution: list[dict] = []
    ships: list[dict] = []
    lists: list[ListData] = [] # Updated to Rich Data
    pilots: list[dict] = []
    upgrades: list[dict] = []
    
    last_sync: str = "Updating..."
    date_range: str = ""
    
    total_tournaments: int = 0
    total_players: int = 0
    
    # Sorting Preferences
    sort_lists: str = "popularity"
    sort_ships: str = "popularity"
    sort_pilots: str = "popularity"
    sort_upgrades: str = "popularity"
    
    async def load_data(self):
        """Fetch meta snapshot summary."""
        # Always reload if triggered by toggle, but check processed if mounting
        # We handle processed flag in on_source_change
        if self.processed: return
        
        from ..backend.data_structures.data_source import DataSource
        
        # Get Global State
        global_state = await self.get_state(GlobalFilterState)
        ds_value = global_state.data_source
        
        # Determine DataSource Enum
        ds_enum = DataSource.XWA if ds_value == "xwa" else DataSource.LEGACY
        
        # Get Allowed Formats from Global State
        # This ensures we respect the "Standard/Extended" or "Epic" filters if they were set globally
        allowed_formats = global_state.selected_formats
        
        snapshot = get_meta_snapshot(ds_enum, allowed_formats=allowed_formats)
        
        self.factions = snapshot["factions"]
        self.faction_distribution = snapshot["faction_distribution"]
        self.ships = snapshot["ships"]
        
        # Enrich Lists
        raw_lists = snapshot["lists"]
        self.lists = [enrich_list_data(l) for l in raw_lists]
        
        # Enrich Pilots
        self.pilots = snapshot["pilots"]
        
        self.upgrades = snapshot["upgrades"]
        self.last_sync = snapshot["last_sync"]
        self.date_range = snapshot["date_range"]
        
        with Session(engine) as session:
            # Stats also filtered by 3 months ideally, but for now global counts are ok
            # Actually user asked for "stats only for last 3 months"
            from datetime import datetime, timedelta
            start_date = datetime.now() - timedelta(days=90)
            
            self.total_tournaments = session.exec(select(func.count(Tournament.id)).where(Tournament.date >= start_date)).one()
            self.total_players = session.exec(
                select(func.count(PlayerResult.id))
                .join(Tournament)
                .where(Tournament.date >= start_date)
            ).one()
            
        self.processed = True
        self.apply_sorting()

    async def on_source_change(self, val):
        """Handle data source toggle."""
        # Reflex often sends value as a list for segmented control
        if isinstance(val, list) and len(val) > 0:
            val = val[0]
            
        # 1. Update Global State first
        yield GlobalFilterState.set_data_source(val)
        
        # 2. Reset local processed flag to allow reload
        self.processed = False
        
        # 3. Trigger reload
        yield HomeState.load_data

    def set_sort_lists(self, val):
        self.sort_lists = val
        self.apply_sorting()

    def set_sort_ships(self, val):
        self.sort_ships = val
        self.apply_sorting()

    def set_sort_pilots(self, val):
        self.sort_pilots = val
        self.apply_sorting()

    def set_sort_upgrades(self, val):
        self.sort_upgrades = val
        self.apply_sorting()

    def apply_sorting(self):
        """Sort local lists based on criteria."""
        def skey(item, criteria):
            if isinstance(item, ListData):
                # Map criteria to ListData properties
                if criteria == "popularity": return item.count
                if criteria == "win_rate": return item.win_rate
                return 0
                
            val = item.get(criteria, 0)
            if val == "NA": return -1
            return float(val)

        # Sort Lists (ListData objects)
        self.lists = sorted(self.lists, key=lambda x: skey(x, self.sort_lists), reverse=True)
        
        # Sort others (dicts)
        self.ships = sorted(self.ships, key=lambda x: skey(x, self.sort_ships), reverse=True)
        self.pilots = sorted(self.pilots, key=lambda x: skey(x, self.sort_pilots), reverse=True)
        self.upgrades = sorted(self.upgrades, key=lambda x: skey(x, self.sort_upgrades), reverse=True)

    # Navigation Handlers
    def nav_to_ship_filter(self, ship_xws: str):
        # We need to set GlobalFilter to pre-filter ship browser?
        # Or simple redirect query param?
        # Simple redirect: /ships?ship=xws
        return rx.redirect(f"/ships?ship={ship_xws}") # Assuming logic exists there or we implement query read.
        # Actually user asked: "Filtered Card Browser" for chassis.
        # So /cards?ship=xws would be better if Card Browser supports ship filter.
        # But top chassis ranking usually implies Ship Browser.
        # Let's redirect to /cards?ship=xws 
        # return rx.redirect(f"/cards?ship={ship_xws}")

def home_content() -> rx.Component:
    """The main dashboard layout."""
    return rx.flex(
        rx.vstack(
            # Hero Section
            rx.box(
                rx.flex(
                    rx.vstack(
                        rx.heading("META SNAPSHOT", size={"initial": "5", "sm": "7", "md": "9"}, font_family=SANS_FONT, weight="bold", letter_spacing="-0.03em"),
                        rx.hstack(
                            rx.badge(HomeState.last_sync, variant="surface", color_scheme="gray"),
                            rx.text(f"RANGE: {HomeState.date_range}", size="1", color=TEXT_SECONDARY, font_family=MONOSPACE_FONT),
                            spacing="2",
                            align="center",
                        ),
                        align="start",
                        spacing="2"
                    ),
                    rx.spacer(),
                    rx.vstack(
                        rx.text("GAME SOURCE", size="1", weight="bold", color=TEXT_SECONDARY, font_family=MONOSPACE_FONT),
                        data_source_toggle(),
                        align="start",
                        spacing="1"
                    ),
                    width="100%",
                    align="end",
                    flex_direction={"initial": "column", "md": "row"},
                    gap="4",
                ),
                padding_bottom="40px",
                width="100%"
            ),
            
            # Stat Row (3-Month Filtered)
            rx.grid(
                meta_stat_card("RECENT TOURNAMENTS", HomeState.total_tournaments.to(str), icon="database", subtext="Last 90 Days"),
                meta_stat_card("RECENT LISTS", HomeState.total_players.to(str), icon="users", subtext="Last 90 Days"),
                meta_stat_card("ACTIVE FACTIONS", "7", icon="layers"),
                # Add Data Source Toggle here actually looks better on top right of header
                columns={"initial": "1", "md": "3"},
                spacing="4",
                width="100%",
                margin_bottom="32px",
            ),

            # Charts Section (3 Columns)
            rx.grid(
                content_panel(
                    "POPULARITY",
                    rx.box(faction_performance_chart(HomeState.factions, data_key="popularity", title="Total Lists"), width="100%"),
                    icon="pie-chart"
                ),
                content_panel(
                    "WIN RATES",
                    rx.box(faction_performance_chart(HomeState.factions, data_key="win_rate", title="Win Rate %"), width="100%"),
                    icon="trending-up"
                ),
                content_panel(
                    "DISTRIBUTION",
                    rx.box(faction_game_pie_chart(HomeState.faction_distribution), width="100%"),
                    icon="circle-dashed"
                ),
                columns={"initial": "1", "md": "3"},
                spacing="4",
                width="100%",
                margin_bottom="32px",
            ),

            # Rankings Section
            rx.grid(
                # Column 1: Lists & Ships
                rx.vstack(
                    content_panel(
                        rx.hstack(
                           rx.text("TOP SQUAD LISTS", weight="bold"),
                           sort_toggle(HomeState.sort_lists, HomeState.set_sort_lists),
                           width="100%", align="center"
                        ),
                        rx.vstack(
                            rx.foreach(
                                HomeState.lists[:5],
                                lambda l: top_list_row(
                                    l, 
                                    value=rx.cond(HomeState.sort_lists == "win_rate", l.win_rate.to(str) + "%", l.count.to(str)),
                                    on_click=rx.redirect("/squadrons")
                                )
                            ),
                            spacing="0", width="100%",
                        ),
                        icon="layers"
                    ),
                    content_panel(
                        rx.hstack(
                           rx.text("TOP CHASSIS", weight="bold"),
                           sort_toggle(HomeState.sort_ships, HomeState.set_sort_ships),
                           width="100%", align="center"
                        ),
                        rx.vstack(
                            rx.foreach(
                                HomeState.ships[:5],
                                lambda s, i: top_item_row(
                                    s["ship_name"], 
                                    s["ship_xws"], 
                                    f"{s['popularity']} Lists", 
                                    f"{s['win_rate']}% WR", 
                                    i + 1, 
                                    is_ship=True,
                                    on_click=rx.redirect(f"/cards?ship={s['ship_xws']}")
                                )
                            ),
                            spacing="0", width="100%",
                        ),
                        icon="rocket"
                    ),
                    spacing="6",
                ),
                # Column 2: Pilots & Upgrades
                rx.vstack(
                    content_panel(
                        rx.hstack(
                           rx.text("TOP PILOTS", weight="bold"),
                           sort_toggle(HomeState.sort_pilots, HomeState.set_sort_pilots),
                           width="100%", align="center"
                        ),
                        rx.vstack(
                            rx.foreach(
                                HomeState.pilots[:5],
                                lambda p, i: top_item_row(
                                    p["name"], 
                                    p["faction"], 
                                    f"{p['popularity']} Lists", 
                                    f"{p['win_rate']}% WR", 
                                    i + 1,
                                    ship_icon_xws=p["ship_xws"], # Pass ship icon if available
                                    on_click=rx.redirect(f"/pilot/{p['name']}") # Using name/xws if available. Backend MUST provide xws. Assuming p['xws'] exists or we use name? aggregate_card_stats uses xws? Let's check backend/analytics/core.py.
                                )
                            ),
                            spacing="0", width="100%",
                        ),
                        icon="user"
                    ),
                    content_panel(
                        rx.hstack(
                           rx.text("TOP UPGRADES", weight="bold"),
                           sort_toggle(HomeState.sort_upgrades, HomeState.set_sort_upgrades),
                           width="100%", align="center"
                        ),
                        rx.vstack(
                            rx.foreach(
                                HomeState.upgrades[:5],
                                lambda u, i: top_item_row(
                                    u["name"], 
                                    "unknown", 
                                    f"{u['popularity']} Lists", 
                                    f"{u['win_rate']}% WR", 
                                    i + 1,
                                    on_click=rx.redirect(f"/upgrade/{u['name']}") # Assuming name/xws
                                )
                            ),
                            spacing="0", width="100%",
                        ),
                        icon="cpu"
                    ),
                    spacing="6",
                ),
                columns={"initial": "1", "md": "2"},
                spacing="4",
                width="100%",
            ),
            
            width="100%",
            max_width="1400px",
            margin_x="auto",
            on_mount=HomeState.load_data,
        ),
        width="100%",
        padding_x={"initial": "16px", "sm": "24px", "md": "32px", "lg": "40px"},
        padding_y="32px",
        padding_bottom="120px",
        justify="center",
    )

def home_page() -> rx.Component:
    """The Home page wrapped in the layout."""
    return layout(home_content())
