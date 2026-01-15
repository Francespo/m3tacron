"""
M3taCron Tournaments Page - Browse all tournaments.
"""
import reflex as rx
from sqlmodel import Session, select, func

from ..components.sidebar import layout
from ..backend.database import engine
from ..backend.models import Tournament, PlayerResult


class TournamentsState(rx.State):
    """State for the Tournaments page."""
    tournaments: list[dict] = []
    search_query: str = ""
    format_filter: str = "all"
    
    @rx.var
    def filtered_tournaments(self) -> list[dict]:
        """Filters tournaments based on search query and format filter."""
        result = self.tournaments
        
        # Apply format filter
        if self.format_filter != "all":
            result = [t for t in result if t["macro_format"] == self.format_filter]
        
        # Apply search filter
        if self.search_query:
            query = self.search_query.lower()
            result = [t for t in result if query in t["name"].lower()]
        
        return result
    
    def load_tournaments(self):
        """Load all tournaments from database."""
        with Session(engine) as session:
            query = select(Tournament).order_by(Tournament.date.desc())
            tournaments = session.exec(query).all()
            
            self.tournaments = []
            for t in tournaments:
                player_count = session.exec(
                    select(func.count(PlayerResult.id)).where(
                        PlayerResult.tournament_id == t.id
                    )
                ).one()
                
                self.tournaments.append({
                    "id": t.id,
                    "name": t.name,
                    "date": t.date.strftime("%Y-%m-%d"),
                    "players": player_count,
                    "format": t.format,
                    "macro_format": t.macro_format,
                    "sub_format": t.sub_format,
                    "platform": t.platform,
                    "url": t.url,
                })
    
    def set_search(self, value: str):
        self.search_query = value
    
    def set_format_filter(self, value: str):
        self.format_filter = value


def tournament_card(tournament: dict) -> rx.Component:
    """A card displaying tournament info."""
    return rx.box(
        rx.vstack(
            # Header
            rx.hstack(
                rx.heading(tournament["name"], size="4"),
                rx.spacer(),
                rx.badge(tournament["macro_format"], color_scheme="purple", size="1"),
                rx.badge(tournament["sub_format"], color_scheme="cyan", variant="outline", size="1"),
                width="100%",
            ),
            # Meta info
            rx.hstack(
                rx.icon("calendar", size=14, color="gray"),
                rx.text(tournament["date"], size="2", color="gray"),
                rx.icon("users", size=14, color="gray"),
                rx.text(rx.Var.create(f"{tournament['players']} players"), size="2", color="gray"),
                rx.icon("globe", size=14, color="gray"),
                rx.text(tournament["platform"], size="2", color="gray"),
                spacing="2",
            ),
            # Actions
            rx.hstack(
                rx.link(
                    rx.button("View Details", variant="outline", size="1"),
                    href="/tournament/" + tournament["id"].to_string(),
                ),
                rx.link(
                    rx.button(
                        rx.icon("external-link", size=14),
                        "Source",
                        variant="ghost",
                        size="1",
                    ),
                    href=tournament["url"],
                    is_external=True,
                ),
                spacing="2",
            ),
            align="start",
            spacing="3",
            width="100%",
        ),
        padding="20px",
        background="rgba(255, 255, 255, 0.03)",
        border_radius="12px",
        border="1px solid rgba(255, 255, 255, 0.08)",
        _hover={
            "border_color": "rgba(0, 255, 255, 0.3)",
            "background": "rgba(255, 255, 255, 0.05)",
        },
        width="100%",
    )


def tournaments_content() -> rx.Component:
    """The main content for the Tournaments page."""
    return rx.vstack(
        # Header
        rx.hstack(
            rx.vstack(
                rx.heading("Tournaments", size="8"),
                rx.text("Browse all tracked X-Wing tournaments", size="3", color="gray"),
                align="start",
            ),
            rx.spacer(),
            rx.badge(
                TournamentsState.filtered_tournaments.length().to_string() + " shown",
                color_scheme="cyan",
                size="2",
            ),
            width="100%",
            margin_bottom="24px",
        ),
        
        # Filters
        rx.hstack(
            rx.input(
                placeholder="Search tournaments...",
                value=TournamentsState.search_query,
                on_change=TournamentsState.set_search,
                width="300px",
            ),
            rx.select(
                ["all", "2.5", "2.0", "Other"],
                value=TournamentsState.format_filter,
                on_change=TournamentsState.set_format_filter,
                placeholder="Format Category",
            ),
            spacing="3",
            margin_bottom="24px",
        ),
        
        # Tournament grid
        rx.cond(
            TournamentsState.filtered_tournaments.length() > 0,
            rx.vstack(
                rx.foreach(TournamentsState.filtered_tournaments, tournament_card),
                spacing="4",
                width="100%",
            ),
            rx.box(
                rx.vstack(
                    rx.icon("inbox", size=48, color="gray"),
                    rx.text("No tournaments found", size="4", color="gray"),
                    rx.text("Import some tournaments to get started", size="2", color="gray"),
                    spacing="2",
                    align="center",
                ),
                padding="48px",
                width="100%",
                text_align="center",
            ),
        ),
        
        align="start",
        width="100%",
        max_width="900px",
        on_mount=TournamentsState.load_tournaments,
    )


def tournaments_page() -> rx.Component:
    """The Tournaments page wrapped in the layout."""
    return layout(tournaments_content())
