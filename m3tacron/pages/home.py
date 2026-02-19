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
    top_item_row
)
from ..components.ui import content_panel

class HomeState(rx.State):
    """Snapshot of the current meta (last 90 days)."""
    processed: bool = False
    
    # Snapshot data
    factions: list[dict] = []
    faction_distribution: list[dict] = []
    ships: list[dict] = []
    lists: list[dict] = []
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
    
    def load_data(self):
        """Fetch meta snapshot summary."""
        if self.processed: return
        
        from ..backend.data_structures.data_source import DataSource
        snapshot = get_meta_snapshot(DataSource.XWA)
        
        self.factions = snapshot["factions"]
        self.faction_distribution = snapshot["faction_distribution"]
        self.ships = snapshot["ships"]
        self.lists = snapshot["lists"]
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
            val = item.get(criteria, 0)
            if val == "NA": return -1
            return float(val)

        self.lists = sorted(self.lists, key=lambda x: skey(x, self.sort_lists), reverse=True)
        self.ships = sorted(self.ships, key=lambda x: skey(x, self.sort_ships), reverse=True)
        self.pilots = sorted(self.pilots, key=lambda x: skey(x, self.sort_pilots), reverse=True)
        self.upgrades = sorted(self.upgrades, key=lambda x: skey(x, self.sort_upgrades), reverse=True)

def home_content() -> rx.Component:
    """The main dashboard layout."""
    return rx.flex(
        rx.vstack(
            # Hero Section
            rx.box(
                rx.vstack(
                    rx.heading("META SNAPSHOT", size="9", font_family=SANS_FONT, weight="bold", letter_spacing="-0.03em"),
                    rx.hstack(
                        rx.badge(HomeState.last_sync, variant="surface", color_scheme="gray"),
                        rx.text(f"RANGE: {HomeState.date_range}", size="1", color=TEXT_SECONDARY, font_family=MONOSPACE_FONT),
                        spacing="2",
                        align="center",
                    ),
                    align="start",
                    spacing="2"
                ),
                padding_bottom="40px",
                width="100%"
            ),
            
            # Stat Row (3-Month Filtered)
            rx.grid(
                meta_stat_card("RECENT TOURNAMENTS", HomeState.total_tournaments.to(str), icon="database", subtext="Last 90 Days"),
                meta_stat_card("RECENT LISTS", HomeState.total_players.to(str), icon="users", subtext="Last 90 Days"),
                meta_stat_card("ACTIVE FACTIONS", "7", icon="layers"),
                columns="3",
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
                columns="3",
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
                                lambda l, i: top_item_row(l["name"], l["faction"], f"{l['popularity']} Games", f"{l['win_rate']}% WR", i + 1, is_list=True)
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
                                lambda s, i: top_item_row(s["ship_name"], s["ship_xws"], f"{s['popularity']} Lists", f"{s['win_rate']}% WR", i + 1, is_ship=True)
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
                                lambda p, i: top_item_row(p["name"], p["faction"], f"{p['popularity']} Lists", f"{p['win_rate']}% WR", i + 1)
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
                                lambda u, i: top_item_row(u["name"], "unknown", f"{u['popularity']} Lists", f"{u['win_rate']}% WR", i + 1)
                            ),
                            spacing="0", width="100%",
                        ),
                        icon="cpu"
                    ),
                    spacing="6",
                ),
                columns="2",
                spacing="6",
                width="100%",
            ),
            
            width="100%",
            max_width="1400px",
            margin_x="auto",
            on_mount=HomeState.load_data,
        ),
        width="100%",
        padding_x=["16px", "24px", "32px", "40px"],
        padding_y="40px",
        padding_bottom="120px",
        justify="center",
    )

def home_page() -> rx.Component:
    """The Home page wrapped in the layout."""
    return layout(home_content())
