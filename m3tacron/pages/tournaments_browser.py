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
from ..components.pagination import pagination_controls
from ..components.content_source_filter import content_source_filter
from ..components.format_filter import hierarchical_format_filter, FormatFilterMixin
from ..theme import (
    TERMINAL_BG, TEXT_PRIMARY, TEXT_SECONDARY, BORDER_COLOR,
    MONOSPACE_FONT, SANS_FONT, INPUT_STYLE, FACTION_COLORS
)


class TournamentsState(FormatFilterMixin):
    """
    State for the Tournaments page.

    Inherits FormatFilterMixin -> PaginationMixin(rx.State):
        - selected_formats, toggle_format_macro/child, set_default_formats_for_source
        - page_size, current_page, total_items_count, next_page, prev_page
    """
    tournaments: list[dict] = []
    search_query: str = ""

    # Content source vars (inlined from ContentSourceState to avoid multiple inheritance)
    data_source: str = "xwa"
    include_epic: bool = False

    def set_data_source(self, *args):
        """Handle content source toggle (XWA / Legacy)."""
        source = args[0]
        if isinstance(source, list):
            source = source[0]
        self.data_source = source
        self.set_default_formats_for_source(self.data_source)
        self.current_page = 0
        self.load_tournaments()

    def set_include_epic(self, val: bool):
        """Handle epic content toggle."""
        self.include_epic = val

    def _get_filtered(self) -> list[dict]:
        """Filter loaded tournaments by active format checkboxes and search query."""
        result = self.tournaments

        # Collect checked format values (only actual Format enum keys, not macro keys)
        valid_format_values = {f.value for f in Format}
        active_formats = [k for k, v in self.selected_formats.items()
                          if v and k in valid_format_values]
        if active_formats:
            result = [t for t in result if t.get("format") in active_formats]

        # Text search
        if self.search_query:
            q = self.search_query.lower()
            result = [t for t in result if q in t["name"].lower()]

        return result

    @rx.var
    def filtered_tournaments(self) -> list[dict]:
        """Return filtered tournament list."""
        return self._get_filtered()

    @rx.var
    def paginated_tournaments(self) -> list[dict]:
        """Return current page slice of filtered tournaments."""
        start = self.current_page * self.page_size
        end = start + self.page_size
        return self.filtered_tournaments[start:end]

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
                    "macro_format": t.format.macro.value,
                    "platform": str(t.platform),
                    "platform_label": Platform(t.platform).label if t.platform in Platform._value2member_map_ else str(t.platform),
                    "url": t.url,
                })
            self.total_items_count = len(self._get_filtered())

    def set_search(self, value: str):
        """Handle search input change."""
        self.search_query = value
        self.current_page = 0
        self.total_items_count = len(self._get_filtered())

    def on_filter_change(self):
        """Hook from FormatFilterMixin when format checkboxes change."""
        self.current_page = 0
        self.total_items_count = len(self._get_filtered())

    def on_page_change(self):
        """Hook from PaginationMixin (no DB reload needed)."""
        return []

    def on_mount_tournaments(self):
        """Called on page mount."""
        self.set_default_formats_for_source(self.data_source)
        self.load_tournaments()


def tournament_card(tournament: dict, index: int) -> rx.Component:
    """A card displaying tournament info - Terminal ListRow."""
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
                    rx.badge(tournament["format_label"], variant="soft", color_scheme="gray"),
                    rx.text(tournament["date"], size="1", color=TEXT_SECONDARY, font_family=MONOSPACE_FONT),
                    rx.spacer(),
                    rx.text(tournament["platform_label"], size="1", color=TEXT_SECONDARY, font_family=MONOSPACE_FONT),
                    spacing="2",
                    width="100%",
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
            border_color=FACTION_COLORS.get("galacticempire", "#333333")
        ),
        href="/tournament/" + tournament["id"].to_string(),
        style={"text_decoration": "none", "width": "100%"}
    )


def render_filters() -> rx.Component:
    """Render the sidebar filters for Tournaments."""
    return rx.vstack(
        # 1. Content Source (XWA / Legacy + Epic toggle)
        rx.box(
            content_source_filter(TournamentsState),
            width="100%"
        ),

        rx.divider(border_color=BORDER_COLOR),

        # 2. Tournament Name Search
        rx.vstack(
            rx.text("Search", size="1", color=TEXT_SECONDARY, font_family=MONOSPACE_FONT),
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

        # 3. Format Filter (hierarchical checkboxes)
        rx.box(
            hierarchical_format_filter(TournamentsState),
            width="100%",
        ),

        spacing="4",
        width="100%",
    )


def tournaments_content() -> rx.Component:
    """The main content for the Tournaments page."""
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

        rx.flex(
             rx.text(
                 TournamentsState.filtered_tournaments.length().to_string() + " Tournaments",
                 size="2", color=TEXT_SECONDARY, font_family=MONOSPACE_FONT
             ),
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
                pagination_controls(TournamentsState),
                spacing="0",
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
        on_mount=TournamentsState.on_mount_tournaments,
        padding_bottom="60px"
    )


def tournaments_browser_page() -> rx.Component:
    """The Tournaments page wrapped in the layout."""
    return layout(
        dashboard_layout(
             render_filters(),
             tournaments_content()
        )
    )
