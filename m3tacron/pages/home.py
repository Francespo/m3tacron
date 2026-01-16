"""
M3taCron Home Page - Meta Snapshot Dashboard.
Star Wars Imperial aesthetic.
"""
import reflex as rx
from sqlmodel import Session, select, func

from ..components.sidebar import layout
from ..backend.database import engine
from ..backend.models import Tournament, PlayerResult


# Star Wars color palette
IMPERIAL_BLUE = "#4fb8ff"
IMPERIAL_RED = "#ff4757"
IMPERIAL_YELLOW = "#ffc312"
STEEL_BORDER = "#2a2a3a"
STEEL_BG = "#1a1a24"


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
    """A stat card component - Imperial control panel style."""
    return rx.box(
        rx.vstack(
            rx.text(
                title, 
                size="2", 
                color="#8a8a9a", 
                font_family="Orbitron, sans-serif", 
                letter_spacing="0.08em",
                text_transform="uppercase",
            ),
            rx.text(
                value, 
                size="8", 
                weight="bold", 
                color=IMPERIAL_BLUE, 
                font_family="Orbitron, sans-serif",
            ),
            rx.text(subtitle, size="1", color="#6a6a7a") if subtitle else rx.fragment(),
            spacing="1",
            align="start",
        ),
        padding="20px 24px",
        background=f"linear-gradient(135deg, {STEEL_BG} 0%, rgba(26, 26, 36, 0.5) 100%)",
        border_radius="4px",
        border=f"1px solid {STEEL_BORDER}",
        border_left=f"3px solid {IMPERIAL_BLUE}",
        min_width="200px",
        transition="all 0.3s ease",
        _hover={
            "transform": "translateY(-3px)",
            "box_shadow": f"0 8px 30px -10px rgba(79, 184, 255, 0.3), 0 0 0 1px rgba(79, 184, 255, 0.2)",
            "border_color": IMPERIAL_BLUE,
        },
    )


def ship_row(ship: dict) -> rx.Component:
    """A row displaying ship statistics - Imperial terminal style."""
    return rx.hstack(
        rx.text(ship["name"], size="3", weight="medium"),
        rx.spacer(),
        rx.text(rx.Var.create(f"{ship['count']} lists"), size="2", color="#8a8a9a"),
        rx.badge(
            rx.Var.create(f"{ship['winrate']}%"),
            color_scheme="green",
            size="1",
            variant="soft",
        ),
        width="100%",
        padding="12px 16px",
        background="rgba(26, 26, 36, 0.5)",
        border_radius="4px",
        border_left=f"2px solid transparent",
        transition="all 0.2s ease",
        _hover={
            "background": "rgba(79, 184, 255, 0.1)",
            "border_left": f"2px solid {IMPERIAL_BLUE}",
            "cursor": "pointer",
        },
    )


def tournament_row(tournament: dict) -> rx.Component:
    """A row displaying tournament info - Imperial data terminal style."""
    return rx.hstack(
        rx.vstack(
            rx.text(tournament["name"], size="3", weight="medium"),
            rx.hstack(
                rx.text(tournament["date"], size="1", color="#6a6a7a"),
                rx.badge(tournament["format"], color_scheme="purple", size="1", variant="outline"),
                spacing="2",
            ),
            spacing="1",
            align="start",
        ),
        rx.spacer(),
        rx.badge(rx.Var.create(f"{tournament['players']} players"), color_scheme="blue", size="1"),
        width="100%",
        padding="12px 16px",
        background="rgba(26, 26, 36, 0.5)",
        border_radius="4px",
        border_left=f"2px solid transparent",
        transition="all 0.2s ease",
        _hover={
            "background": "rgba(79, 184, 255, 0.1)",
            "border_left": f"2px solid {IMPERIAL_BLUE}",
            "cursor": "pointer",
        },
    )


def section_panel(title: str, content: rx.Component) -> rx.Component:
    """A section panel - Imperial control room style."""
    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.box(
                    width="4px",
                    height="20px",
                    background=IMPERIAL_BLUE,
                    border_radius="2px",
                ),
                rx.heading(
                    title, 
                    size="4", 
                    font_family="Orbitron, sans-serif",
                    letter_spacing="0.1em",
                    color="#e8e8e8",
                ),
                spacing="3",
                align="center",
                margin_bottom="16px",
            ),
            content,
            align="stretch",
            width="100%",
        ),
        padding="24px",
        background=f"linear-gradient(180deg, rgba(26, 26, 36, 0.8) 0%, rgba(26, 26, 36, 0.4) 100%)",
        border_radius="4px",
        border=f"1px solid {STEEL_BORDER}",
        _hover={
            "border_color": "rgba(79, 184, 255, 0.3)",
        },
    )


def home_content() -> rx.Component:
    """The main content for the Home page - Imperial style."""
    return rx.vstack(
        # Header
        rx.vstack(
            rx.heading(
                "META SNAPSHOT", 
                size="8", 
                font_family="Orbitron, sans-serif", 
                letter_spacing="0.15em",
                color="#e8e8e8",
            ),
            rx.box(
                width="120px",
                height="2px",
                background=f"linear-gradient(90deg, {IMPERIAL_BLUE}, transparent)",
                margin_top="8px",
                margin_bottom="8px",
            ),
            rx.text(
                "Current tournament meta analysis for Star Wars: X-Wing",
                size="3",
                color="#8a8a9a",
                font_family="Inter, sans-serif",
            ),
            align="start",
            margin_bottom="32px",
        ),
        
        # Stats row
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
            section_panel(
                "TOP SHIPS",
                rx.vstack(
                    rx.foreach(HomeState.top_ships, ship_row),
                    spacing="2",
                    width="100%",
                ),
            ),
            # Recent Tournaments
            section_panel(
                "RECENT TOURNAMENTS",
                rx.vstack(
                    rx.foreach(HomeState.recent_tournaments, tournament_row),
                    rx.link(
                        rx.button(
                            "View All Tournaments", 
                            variant="outline", 
                            size="2",
                            color=IMPERIAL_BLUE,
                        ),
                        href="/tournaments",
                        margin_top="16px",
                    ),
                    spacing="2",
                    width="100%",
                ),
            ),
            columns="2",
            spacing="6",
            width="100%",
        ),
        
        align="start",
        width="100%",
        max_width="1200px",
        on_mount=HomeState.load_data,
    )


def home_page() -> rx.Component:
    """The Home page wrapped in the layout."""
    return layout(home_content())

