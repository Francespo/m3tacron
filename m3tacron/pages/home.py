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


class HomeState(rx.State):
    """State for the Home page."""
    recent_tournaments: list[Tournament] = []
    
    def load_data(self):
        """Load dashboard data from database."""
        with Session(engine) as session:
            # Get recent tournaments
            tournaments = session.exec(
                select(Tournament).order_by(Tournament.date.desc()).limit(10)
            ).all()
            
            self.recent_tournaments = tournaments
            
            # Note: player_count is a field in Tournament model. 
            # If it's 0, we could fetch it, but usually the model should have it.
            # Keeping the logic for dynamic count if needed, but storing the object.
            # To avoid extra DB queries during list render, we assume player_count is set.


def tournament_row(tournament: Tournament, index: int) -> rx.Component:
    """Row for recent tournaments."""
    from ..backend.data_structures.formats import Format
    return rx.link(
        list_row(
            left_content=rx.vstack(
                rx.text(tournament.name, size="2", weight="bold", color=TEXT_PRIMARY, font_family=MONOSPACE_FONT),
                rx.text(tournament.date.to(str), size="1", color=TEXT_SECONDARY, font_family=MONOSPACE_FONT),
                spacing="0",
                align="start",
            ),
            right_content=rx.hstack(
                rx.text(tournament.format_label, size="1", color=TEXT_SECONDARY, font_family=MONOSPACE_FONT),
                rx.text(f"[{tournament.player_count}]", size="1", color=TEXT_SECONDARY, font_family=MONOSPACE_FONT),
                spacing="2"
            ),
            index=index,
        ),
        href="/tournament/" + tournament.id.to_string(),
        style={"text_decoration": "none", "width": "100%"}
    )


def home_content() -> rx.Component:
    """The main content for the Home page."""
    return rx.vstack(
        # Header "Modern" style
        rx.box(
            rx.vstack(
                rx.heading(
                    "Dashboard", 
                    size="8", 
                    font_family=SANS_FONT, 
                    color=TEXT_PRIMARY,
                    weight="bold",
                    class_name="animate-fade-in-up"
                ),
                rx.text(
                    "Recent Tournaments",
                    size="3",
                    color=TEXT_SECONDARY,
                    font_family=SANS_FONT,
                    class_name="animate-fade-in-up delay-100"
                ),
                align="start",
                spacing="1"
            ),
            padding_bottom="32px",
            width="100%"
        ),
        
        # Tournaments Table
        rx.vstack(
            content_panel(
                "Recent Activity",
                rx.vstack(
                    rx.foreach(
                        HomeState.recent_tournaments.to(list[dict]), 
                        lambda t, i: tournament_row(t, i)
                    ),
                    spacing="0",
                    width="100%",
                ),
                icon="database"
            ),
            class_name="animate-fade-in-up delay-200",
            width="100%"
        ),
        
        width="100%",
        max_width="1000px",
        on_mount=HomeState.load_data,
        padding_bottom="60px"
    )


def home_page() -> rx.Component:
    """The Home page wrapped in the layout."""
    return layout(home_content())
