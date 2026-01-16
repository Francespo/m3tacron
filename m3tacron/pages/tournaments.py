"""
M3taCron Tournaments Page - Browse all tournaments.
Star Wars Imperial aesthetic.
"""
import reflex as rx
from sqlmodel import Session, select, func

from ..components.sidebar import layout
from ..backend.database import engine
from ..backend.models import (
    Tournament, PlayerResult, MacroFormat, SubFormat,
    get_macro_format, get_sub_format
)


# Star Wars color palette
IMPERIAL_BLUE = "#4fb8ff"
IMPERIAL_RED = "#ff4757"
STEEL_BORDER = "#2a2a3a"
STEEL_BG = "#1a1a24"


class TournamentsState(rx.State):
    """State for the Tournaments page."""
    tournaments: list[dict] = []
    search_query: str = ""
    macro_filter: str = "all"
    sub_filter: str = "all"
    
    @rx.var
    def available_sub_formats(self) -> list[str]:
        """Get available sub-formats based on current macro filter."""
        if self.macro_filter == "all":
            return ["all"] + [sf.value for sf in SubFormat if sf != SubFormat.UNKNOWN]
        elif self.macro_filter == MacroFormat.V2_5.value:
            return ["all", SubFormat.AMG.value, SubFormat.XWA.value, SubFormat.STANDARD.value]
        elif self.macro_filter == MacroFormat.V2_0.value:
            return ["all", SubFormat.X2PO.value, SubFormat.XLC.value, SubFormat.WILDSPACE.value, SubFormat.LEGACY.value]
        return ["all"]
    
    @rx.var
    def filtered_tournaments(self) -> list[dict]:
        """Filters tournaments based on search query and format filters."""
        result = self.tournaments
        
        # Apply macro format filter
        if self.macro_filter != "all":
            result = [t for t in result if t["macro_format"] == self.macro_filter]
        
        # Apply sub format filter
        if self.sub_filter != "all":
            result = [t for t in result if t["sub_format"] == self.sub_filter]
        
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
                # Use player_count from Tournament model if available
                # Otherwise fall back to counting PlayerResults
                player_count = t.player_count
                if player_count == 0:
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
                    "macro_format": get_macro_format(t.format),
                    "sub_format": get_sub_format(t.format),
                    "platform": t.platform,
                    "url": t.url,
                })
    
    def set_search(self, value: str):
        self.search_query = value
    
    def set_macro_filter(self, value: str):
        self.macro_filter = value
        # Reset sub filter when macro changes
        self.sub_filter = "all"
    
    def set_sub_filter(self, value: str):
        self.sub_filter = value


def tournament_card(tournament: dict) -> rx.Component:
    """A card displaying tournament info - Imperial data terminal style."""
    return rx.box(
        rx.vstack(
            # Header
            rx.hstack(
                rx.heading(tournament["name"], size="4"),
                rx.spacer(),
                rx.badge(tournament["macro_format"], color_scheme="purple", size="1"),
                rx.badge(tournament["sub_format"], color_scheme="blue", variant="outline", size="1"),
                width="100%",
            ),
            # Meta info
            rx.hstack(
                rx.icon("calendar", size=14, color="#6a6a7a"),
                rx.text(tournament["date"], size="2", color="#8a8a9a"),
                rx.icon("users", size=14, color="#6a6a7a"),
                rx.text(rx.Var.create(f"{tournament['players']} players"), size="2", color="#8a8a9a"),
                rx.icon("globe", size=14, color="#6a6a7a"),
                rx.text(tournament["platform"], size="2", color="#8a8a9a"),
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
        padding="20px 24px",
        background=f"linear-gradient(135deg, {STEEL_BG} 0%, rgba(26, 26, 36, 0.5) 100%)",
        border_radius="4px",
        border=f"1px solid {STEEL_BORDER}",
        border_left=f"3px solid transparent",
        transition="all 0.3s ease",
        _hover={
            "border_left": f"3px solid {IMPERIAL_BLUE}",
            "border_color": f"rgba(79, 184, 255, 0.3)",
            "box_shadow": f"0 4px 20px -5px rgba(79, 184, 255, 0.2)",
        },
        width="100%",
    )


def filter_select(
    label: str,
    options: list[str] | rx.Var,
    value: rx.Var,
    on_change: callable,
) -> rx.Component:
    """A styled filter select - Imperial style."""
    return rx.vstack(
        rx.text(label, size="1", color="#6a6a7a", text_transform="uppercase", letter_spacing="0.05em"),
        rx.select(
            options,
            value=value,
            on_change=on_change,
            size="2",
        ),
        align="start",
        spacing="1",
    )


def tournaments_content() -> rx.Component:
    """The main content for the Tournaments page - Imperial style."""
    return rx.vstack(
        # Header
        rx.hstack(
            rx.vstack(
                rx.heading(
                    "TOURNAMENTS", 
                    size="8",
                    font_family="Orbitron, sans-serif",
                    letter_spacing="0.15em",
                ),
                rx.box(
                    width="100px",
                    height="2px",
                    background=f"linear-gradient(90deg, {IMPERIAL_BLUE}, transparent)",
                    margin_top="4px",
                ),
                rx.text("Browse all tracked X-Wing tournaments", size="3", color="#8a8a9a"),
                align="start",
            ),
            rx.spacer(),
            rx.badge(
                TournamentsState.filtered_tournaments.length().to_string() + " shown",
                color_scheme="blue",
                size="2",
            ),
            width="100%",
            margin_bottom="24px",
        ),
        
        # Filters - styled Imperial control panel
        rx.box(
            rx.hstack(
                rx.input(
                    placeholder="Search tournaments...",
                    value=TournamentsState.search_query,
                    on_change=TournamentsState.set_search,
                    width="280px",
                ),
                rx.box(width="1px", height="32px", background=STEEL_BORDER),
                filter_select(
                    "Format",
                    ["all", MacroFormat.V2_5.value, MacroFormat.V2_0.value, MacroFormat.OTHER.value],
                    TournamentsState.macro_filter,
                    TournamentsState.set_macro_filter,
                ),
                filter_select(
                    "Sub-Format",
                    TournamentsState.available_sub_formats,
                    TournamentsState.sub_filter,
                    TournamentsState.set_sub_filter,
                ),
                spacing="4",
                align="end",
            ),
            padding="16px 20px",
            background=f"linear-gradient(135deg, {STEEL_BG} 0%, rgba(26, 26, 36, 0.5) 100%)",
            border_radius="4px",
            border=f"1px solid {STEEL_BORDER}",
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
                    rx.icon("inbox", size=48, color="#6a6a7a"),
                    rx.text("No tournaments found", size="4", color="#8a8a9a"),
                    rx.text("Try adjusting your filters", size="2", color="#6a6a7a"),
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


