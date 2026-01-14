"""
M3taCron Home Page - Meta Snapshot Dashboard.
"""
import reflex as rx
from sqlmodel import Session, select, func

from ..components.sidebar import layout
from ..backend.database import engine
from ..backend.models import Tournament, PlayerResult


class HomeState(rx.State):
    """State for the Home page."""
    # Stats
    total_tournaments: int = 0
    total_players: int = 0
    total_lists: int = 0
    
    # Data lists
    top_ships: list[dict] = []
    recent_tournaments: list[dict] = []
    
    def load_data(self):
        """Load data from database."""
        with Session(engine) as session:
            # Count tournaments
            self.total_tournaments = session.exec(
                select(func.count(Tournament.id))
            ).one()
            
            # Count player results
            self.total_players = session.exec(
                select(func.count(PlayerResult.id))
            ).one()
            
            # Lists = player results with non-empty list_json
            self.total_lists = self.total_players
            
            # Get recent tournaments
            tournaments = session.exec(
                select(Tournament).order_by(Tournament.date.desc()).limit(5)
            ).all()
            
            self.recent_tournaments = []
            for t in tournaments:
                # Count players per tournament
                player_count = session.exec(
                    select(func.count(PlayerResult.id)).where(
                        PlayerResult.tournament_id == t.id
                    )
                ).one()
                
                self.recent_tournaments.append({
                    "id": t.id,
                    "name": t.name,
                    "date": t.date.strftime("%Y-%m-%d"),
                    "players": player_count,
                    "format": t.format,
                })
            
            # Top ships placeholder (would need XWS parsing)
            self.top_ships = [
                {"name": "TIE/ln Fighter", "count": 12, "winrate": 52.3},
                {"name": "X-wing", "count": 10, "winrate": 48.7},
                {"name": "TIE Defender", "count": 8, "winrate": 55.1},
            ]


def stat_card(title: str, value: rx.Var, subtitle: str = "") -> rx.Component:
    """A stat card component for the dashboard."""
    return rx.box(
        rx.vstack(
            rx.text(title, size="2", color="gray"),
            rx.text(value, size="7", weight="bold", color="cyan"),
            rx.text(subtitle, size="1", color="gray") if subtitle else rx.fragment(),
            spacing="1",
            align="start",
        ),
        padding="20px",
        background="rgba(255, 255, 255, 0.05)",
        border_radius="12px",
        border="1px solid rgba(255, 255, 255, 0.1)",
        backdrop_filter="blur(10px)",
        min_width="180px",
    )


def ship_row(ship: dict) -> rx.Component:
    """A row displaying ship statistics."""
    return rx.hstack(
        rx.text(ship["name"], size="3", weight="medium"),
        rx.spacer(),
        rx.text(rx.Var.create(f"{ship['count']} lists"), size="2", color="gray"),
        rx.badge(
            rx.Var.create(f"{ship['winrate']}%"),
            color_scheme="green",
            size="1",
        ),
        width="100%",
        padding="12px 16px",
        background="rgba(255, 255, 255, 0.02)",
        border_radius="8px",
        _hover={"background": "rgba(255, 255, 255, 0.05)"},
    )


def tournament_row(tournament: dict) -> rx.Component:
    """A row displaying tournament info."""
    return rx.hstack(
        rx.vstack(
            rx.text(tournament["name"], size="3", weight="medium"),
            rx.hstack(
                rx.text(tournament["date"], size="1", color="gray"),
                rx.badge(tournament["format"], color_scheme="purple", size="1"),
                spacing="2",
            ),
            spacing="1",
            align="start",
        ),
        rx.spacer(),
        rx.badge(rx.Var.create(f"{tournament['players']} players"), color_scheme="blue", size="1"),
        width="100%",
        padding="12px 16px",
        background="rgba(255, 255, 255, 0.02)",
        border_radius="8px",
        _hover={"background": "rgba(255, 255, 255, 0.05)"},
    )


def home_content() -> rx.Component:
    """The main content for the Home page."""
    return rx.vstack(
        # Header
        rx.heading("Meta Snapshot", size="8", margin_bottom="8px"),
        rx.text(
            "Current tournament meta analysis for Star Wars: X-Wing",
            size="3",
            color="gray",
            margin_bottom="32px",
        ),
        
        # Stats row - now with real data
        rx.hstack(
            stat_card("Tournaments", HomeState.total_tournaments, "tracked"),
            stat_card("Lists", HomeState.total_lists, "analyzed"),
            stat_card("Players", HomeState.total_players, "entries"),
            wrap="wrap",
            spacing="4",
            margin_bottom="32px",
        ),
        
        # Two column layout
        rx.grid(
            # Top Ships
            rx.box(
                rx.vstack(
                    rx.heading("Top Ships", size="5", margin_bottom="16px"),
                    rx.foreach(HomeState.top_ships, ship_row),
                    align="stretch",
                    width="100%",
                ),
                padding="24px",
                background="rgba(255, 255, 255, 0.03)",
                border_radius="16px",
                border="1px solid rgba(255, 255, 255, 0.08)",
            ),
            # Recent Tournaments
            rx.box(
                rx.vstack(
                    rx.heading("Recent Tournaments", size="5", margin_bottom="16px"),
                    rx.foreach(HomeState.recent_tournaments, tournament_row),
                    rx.link(
                        rx.button("View All Tournaments", variant="outline", size="2"),
                        href="/tournaments",
                        margin_top="16px",
                    ),
                    align="stretch",
                    width="100%",
                ),
                padding="24px",
                background="rgba(255, 255, 255, 0.03)",
                border_radius="16px",
                border="1px solid rgba(255, 255, 255, 0.08)",
            ),
            columns="2",
            spacing="6",
            width="100%",
        ),
        
        align="start",
        width="100%",
        max_width="1200px",
        on_mount=HomeState.load_data,  # Load data when page mounts
    )


def home_page() -> rx.Component:
    """The Home page wrapped in the layout."""
    return layout(home_content())
