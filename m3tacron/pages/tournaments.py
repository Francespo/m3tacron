"""
M3taCron Tournaments Page.
"""
import reflex as rx
from sqlmodel import Session, select, func

from ..components.sidebar import layout, dashboard_layout
from ..backend.database import engine
from ..components.ui import content_panel, list_row
from ..components.icons import xwing_icon
from ..backend.models import Tournament, PlayerResult
from ..backend.data_structures.formats import Format, MacroFormat
from ..backend.data_structures.platforms import Platform
from ..ui_utils.pagination import PaginationMixin
from ..components.pagination import pagination_controls
from ..theme import (
    TERMINAL_BG, TEXT_PRIMARY, TEXT_SECONDARY, BORDER_COLOR, 
    MONOSPACE_FONT, SANS_FONT, INPUT_STYLE, FACTION_COLORS
)


class TournamentsState(rx.State, PaginationMixin):
    """State for the Tournaments page."""
    tournaments: list[dict] = []
    search_query: str = ""
    macro_filter: str = "all"
    sub_filter: str = "all"
    
    @rx.var
    def available_sub_formats(self) -> list[list[str]]:
        """Get available sub-formats based on current macro filter."""
        options = [["All", "all"]]
        
        if self.macro_filter == "all":
            # Show all specific formats
            for f in Format:
                if f != Format.OTHER:
                    options.append([f.label, f.value])
        else:
            # Show formats belonging to the selected macro
            try:
                macro = MacroFormat(self.macro_filter)
                for f in macro.formats():
                    options.append([f.label, f.value])
            except ValueError:
                pass
                
        return options
    
    @rx.var
    def filtered_tournaments(self) -> list[dict]:
        """Filters tournaments based on search query and format filters."""
        result = self.tournaments
        
        # Apply macro format filter
        if self.macro_filter != "all":
            result = [t for t in result if t["macro_format"] == self.macro_filter]
        
        # Apply sub format filter
        if self.sub_filter != "all":
            result = [t for t in result if t["format"] == self.sub_filter]
        
        # Apply search filter
        if self.search_query:
            query = self.search_query.lower()
            result = [t for t in result if query in t["name"].lower()]
        
        return result
    
    @rx.var
    def paginated_tournaments(self) -> list[dict]:
        """Get current page of filtered tournaments."""
        start = self.current_page * self.page_size
        end = start + self.page_size
        return self.filtered_tournaments[start:end]
    
    @rx.var
    def total_items_count(self) -> int:
        return len(self.filtered_tournaments)

    def set_page_size(self, size: str):
        self.page_size = int(size)
        self.current_page = 0
    
    def load_tournaments(self):
        """Load all tournaments from database."""
        with Session(engine) as session:
            query = select(Tournament).order_by(Tournament.date.desc())
            tournaments = session.exec(query).all()
            
            self.tournaments = []
            for t in tournaments:
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
                    "date": t.date.strftime("%Y-%m-%d") if t.date else "Unknown",
                    "players": player_count,
                    "format": str(t.format) if t.format else "other",
                    "format_label": Format(t.format).label if t.format else "Other",
                    "macro_format": t.macro_format,
                    "platform": str(t.platform),
                    "platform_label": Platform(t.platform).label if t.platform in Platform._value2member_map_ else str(t.platform),
                    "url": t.url,
                })
    
    def set_search(self, value: str):
        self.search_query = value
    
    def set_macro_filter(self, value: str):
        self.macro_filter = value
        self.sub_filter = "all"
    
    def set_sub_filter(self, value: str):
        self.sub_filter = value


def tournament_card(tournament: dict, index: int) -> rx.Component:
    """A card displaying tournament info - Terminal ListRow"""
    return rx.link(
        list_row(
            left_content=rx.vstack(
                 rx.text(
                     tournament["name"], 
                     size="2", 
                     weight="bold", 
                     color="white",
                     font_family=MONOSPACE_FONT
                 ),
                 rx.hstack(
                    rx.text(f"[{tournament['format_label']}]", size="1", color=TEXT_SECONDARY, font_family=MONOSPACE_FONT),
                    rx.text(tournament["date"], size="1", color=TEXT_SECONDARY, font_family=MONOSPACE_FONT),
                    spacing="2",
                    align="center"
                 ),
                 spacing="0",
                 align="start"
            ),
            right_content=rx.hstack(
                rx.vstack(
                    rx.text(f"{tournament['players']} PLY", size="1", color=TEXT_SECONDARY, font_family=MONOSPACE_FONT, text_align="right"),
                    rx.text(tournament["platform_label"].to(str).upper(), size="1", color="#444444", font_family=MONOSPACE_FONT),
                    spacing="0",
                    align="end"
                ),
                spacing="4",
                align="center"
            ),
            index=index,
            border_color=FACTION_COLORS.get("galacticempire", "#333333") # Default schematic color
        ),
        href="/tournament/" + tournament["id"].to_string(),
        style={"text_decoration": "none", "width": "100%"}
    )


def filter_select(
    label: str,
    options: list[list[str]] | rx.Var,
    value: rx.Var,
    on_change: callable,
) -> rx.Component:
    """A styled filter select - Terminal style.
    
    Args:
        label: Label text above the select.
        options: List of [label, value] pairs for options.
        value: Current selected value (state var).
        on_change: Handler when selection changes.
    """
    return rx.vstack(
        rx.text(label, size="1", color=TEXT_SECONDARY, font_family=MONOSPACE_FONT),
        rx.select.root(
            rx.select.trigger(style=INPUT_STYLE),
            rx.select.content(
                rx.foreach(
                    options,
                    lambda opt: rx.select.item(opt[0], value=opt[1])
                )
            ),
            value=value,
            on_change=on_change,
            size="2",
            color_scheme="gray",
        ),
        align="start",
        spacing="1",
    )

def render_filters() -> rx.Component:
    """Render the sidebar filters for Tournaments."""
    return rx.vstack(
        rx.text("FILTERS", size="1", weight="bold", letter_spacing="1px", color=TEXT_SECONDARY),
        
        # Search
        rx.vstack(
             rx.text("Search", size="1", color=TEXT_SECONDARY),
             rx.input(
                placeholder="Search Tournament...",
                value=TournamentsState.search_query,
                on_change=TournamentsState.set_search,
                width="100%",
                style=INPUT_STYLE,
                color_scheme="gray",
            ),
             width="100%",
             spacing="1"
        ),

        rx.divider(border_color=BORDER_COLOR),

        # Format
        filter_select(
            "FORMAT",
            [["All", "all"]] + [[m.label, m.value] for m in MacroFormat if m != MacroFormat.OTHER],
            TournamentsState.macro_filter,
            TournamentsState.set_macro_filter,
        ),
        filter_select(
            "SUB-FORMAT",
            TournamentsState.available_sub_formats,
            TournamentsState.sub_filter,
            TournamentsState.set_sub_filter,
        ),
        
        spacing="4",
        width="100%",
    )


def tournaments_content() -> rx.Component:
    """The main content for the Tournaments page - Imperial Data Terminal."""
    return rx.vstack(
        # Header
        rx.box(
             rx.heading(
                "Tournaments", 
                size="6",
                font_family=SANS_FONT,
                weight="bold",
                color=TEXT_PRIMARY
            ),
            padding_bottom="24px",
            border_bottom=f"1px solid {BORDER_COLOR}",
            margin_bottom="24px",
            width="100%"
        ),
        
        
        # Filters removed from here
        rx.flex(
             rx.text(TournamentsState.filtered_tournaments.length().to_string() + " Tournaments", size="2", color=TEXT_SECONDARY, font_family=MONOSPACE_FONT),
             width="100%",
             margin_bottom="16px"
        ),
        
        # Tournament grid
        rx.cond(
            TournamentsState.filtered_tournaments.length() > 0,
            rx.vstack(
                rx.foreach(
                    TournamentsState.paginated_tournaments.to(list[dict]), 
                    lambda t, i: tournament_card(t, i)
                ),
                # Pagination
                pagination_controls(TournamentsState),
                spacing="0", # Tight list
                width="100%",
                class_name="animate-fade-in-up delay-300"
            ),
            rx.box(
                rx.text("NO RECORDS FOUND", size="2", color=TEXT_SECONDARY, font_family=MONOSPACE_FONT),
                padding="48px",
                width="100%",
                text_align="center",
            ),
        ),
        
        width="100%",
        max_width="1000px",
        on_mount=TournamentsState.load_tournaments,
        padding_bottom="60px"
    )


def tournaments_page() -> rx.Component:
    """The Tournaments page wrapped in the layout."""
    return layout(
        dashboard_layout(
             render_filters(),
             tournaments_content()
        )
    )
