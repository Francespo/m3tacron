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
from ..components.tournament_filters import TournamentFilterMixin
from ..components.location_filter import location_filter
from ..components.format_filter import hierarchical_format_filter
from ..theme import (
    TERMINAL_BG, TEXT_PRIMARY, TEXT_SECONDARY, BORDER_COLOR,
    MONOSPACE_FONT, SANS_FONT, INPUT_STYLE, FACTION_COLORS, RADIUS
)


class TournamentsState(TournamentFilterMixin):
    """
    State for the Tournaments page.

    Inherits TournamentFilterMixin -> FormatFilterMixin -> PaginationMixin(rx.State):
        - date_range_start/end, location selections
        - selected_formats, format toggles
        - pagination states
    """
    tournaments: list[dict] = []
    _all_tournaments_cached: list[dict] = [] # Cache for client-side pagination
    search_query: str = ""
    # NOTE: Do NOT redefine page_size, selected_formats, or total_pages here.
    # Overriding parent state vars creates duplicate Reflex state slots,
    # breaking reactivity (toggle writes to parent slot, query reads child slot).

    def _get_query_filters(self):
        """Build filters for the SQL query based on state."""

        filters = []
        
        # 1. Format Filter
        valid_format_values = {f.value for f in Format}
        allowed = [k for k, v in self.selected_formats.items() if v and k in valid_format_values]
        if allowed:
            filters.append(Tournament.format.in_(allowed))
            
        # 2. Date Range
        if self.date_range_start:
            filters.append(Tournament.date >= self.date_range_start)
        if self.date_range_end:
            filters.append(Tournament.date <= self.date_range_end)
            
        # 3. Tournament Name Search
        if self.search_query:
            filters.append(Tournament.name.ilike(f"%{self.search_query}%"))
            
        # 4. Location Filters
        active_continents = [k for k, v in self.selected_continents.items() if v]
        active_countries = [k for k, v in self.selected_countries.items() if v]
        active_cities = [k for k, v in self.selected_cities.items() if v]
        
        # We use JSON extract for location matching
        if active_continents:
            filters.append(func.json_extract(Tournament.location, '$.continent').in_(active_continents))
        if active_countries:
            filters.append(func.json_extract(Tournament.location, '$.country').in_(active_countries))
        if active_cities:
            filters.append(func.json_extract(Tournament.location, '$.city').in_(active_cities))
            
        return filters

    def load_tournaments(self):
        """Load tournaments with all active filters from database."""
        print("DEBUG: load_tournaments START")
        with Session(engine) as session:
            # Base query
            query = select(Tournament).order_by(Tournament.date.desc())
            
            # Apply all filters
            for f in self._get_query_filters():
                query = query.where(f)
            
            # Fetch ALL matching results
            # page_query = query.offset(self.current_page * self.page_size).limit(self.page_size) # OLD backend pagination
            results = session.exec(query).all()
            
            self._all_tournaments_cached = []
            for t in results:
                player_count = t.player_count
                if player_count == 0:
                    player_count = session.exec(
                        select(func.count(PlayerResult.id)).where(
                            PlayerResult.tournament_id == t.id
                        )
                    ).one_or_none() or 0

                # Format Location
                loc_str = "Unknown Location"
                if t.location:
                   parts = []
                   if t.location.city: parts.append(t.location.city)
                   if t.location.country: parts.append(t.location.country)
                   if t.location.continent: parts.append(t.location.continent)
                   
                   # Dedup parts (e.g. "Virtual, Virtual, Virtual" -> "Virtual")
                   # maintain order
                   seen = set()
                   unique_parts = []
                   for p in parts:
                       if p not in seen:
                           unique_parts.append(p)
                           seen.add(p)
                           
                   if unique_parts:
                       loc_str = ", ".join(unique_parts)

                # Format Badge
                f_label = Format(t.format).label if t.format in {f.value for f in Format} else (t.format or "Other")
                b1, b2 = _split_format_badge(f_label)

                self._all_tournaments_cached.append({
                    "id": t.id,
                    "name": t.name,
                    "date": t.date.strftime("%Y-%m-%d") if t.date else "Unknown",
                    "players": player_count,
                    "format_label": f_label,
                    "badge_l1": b1,
                    "badge_l2": b2,
                    "platform_label": Platform(t.platform).label if t.platform in Platform._value2member_map_ else str(t.platform),
                    "location": loc_str,
                    "url": t.url,
                })
                
            self.total_items_count = len(self._all_tournaments_cached)
            self.update_view()

    def update_view(self):
        """Slice the cached tournaments for the current page."""
        print(f"DEBUG: update_view. Page: {self.current_page}, Size: {self.page_size}, Total Cached: {len(self._all_tournaments_cached)}")
        start = self.current_page * self.page_size
        end = start + self.page_size
        self.tournaments = self._all_tournaments_cached[start:end]


    def set_search(self, value: str):
        """Handle search input change."""
        self.search_query = value
        self.current_page = 0
        self.load_tournaments()

    # --- Hooks & Mixin Overrides ---
    # WHY: Reflex silently fails on mixin event propagation.
    # Inlining logic from FormatFilterMixin / TournamentFilterMixin.

    def on_tournament_filter_change(self):
        """Central reload hook."""
        self.current_page = 0
        self.load_tournaments()

    def on_filter_change(self):
        """Hook from FormatFilterMixin (Format)."""
        self.on_tournament_filter_change()

    def on_location_change(self):
        """Hook from TournamentFilterMixin (Location)."""
        self.on_tournament_filter_change()

    def toggle_format_macro(self, macro_val: str):
        """Toggle a macro format and reload tournaments."""
        from ..backend.data_structures.formats import MacroFormat

        current_state = self.macro_states.get(macro_val, "unchecked")
        target_checked = current_state == "unchecked"

        new_formats = self.selected_formats.copy()
        try:
            macro = MacroFormat(macro_val)
            for f in macro.formats():
                new_formats[f.value] = target_checked
        except ValueError:
            pass
        new_formats[macro_val] = target_checked

        self.selected_formats = new_formats
        self.on_tournament_filter_change()

    def toggle_format_child(self, child_val: str):
        """Toggle a specific format child and reload tournaments."""
        checked = not self.selected_formats.get(child_val, False)
        new_formats = self.selected_formats.copy()
        new_formats[child_val] = checked
        self.selected_formats = new_formats
        self.on_tournament_filter_change()

    def set_date_start(self, date: str):
        self.date_range_start = date
        self.on_tournament_filter_change()

    def set_date_end(self, date: str):
        self.date_range_end = date
        self.on_tournament_filter_change()

    def toggle_continent(self, val: str, checked: bool):
        new_sel = self.selected_continents.copy()
        new_sel[val] = checked
        self.selected_continents = new_sel
        self.on_tournament_filter_change()

    def toggle_country(self, val: str, checked: bool):
        new_sel = self.selected_countries.copy()
        new_sel[val] = checked
        self.selected_countries = new_sel
        self.on_tournament_filter_change()

    def toggle_city(self, val: str, checked: bool):
        new_sel = self.selected_cities.copy()
        new_sel[val] = checked
        self.selected_cities = new_sel
        self.on_tournament_filter_change()

    def on_page_change(self):
        """Hook from PaginationMixin."""
        self.update_view()

    def on_mount_tournaments(self):
        """Called on page mount."""
        self.page_size = 10  # Override default (20) at runtime, not class-level
        self.load_locations()
        self.load_tournaments()


def _split_format_badge(format_label: str) -> tuple[str, str]:
    """
    Split format label into 2 short rows for the square badge.
    max 4 chars per row.
    Helper for backend logic using real python strings.
    """
    label = format_label.upper() if format_label else "UNK"
    
    # Manual mappings for common ones
    if "STANDARD" in label:
        return "XWA", "STD"
    if "EXTENDED" in label:
        return "XWA", "EXT"
    if "LEGACY (X2PO)" in label:
        return "LGCY", "X2PO"
    if "LEGACY (XLC)" in label:
        return "LGCY", "XLC"
    if "LEGACY" in label: # Generic fallback
        return "LGCY", "2.0"
    if "FFG" in label:
        return "FFG", "2.0"
    if "WILD" in label:
        return "WILD", "CARD"
    if "EPIC" in label:
        return "EPIC", "PLAY"
        
    # Fallback splitting
    words = label.split()
    if len(words) >= 2:
        return words[0][:4], words[1][:4]
    
    if len(label) > 4:
        return label[:4], label[4:8]
        
    return label, ""




def tournament_card(tournament: dict, index: int) -> rx.Component:
    """A card displaying tournament info in a structured list row."""
    # Use pre-calculated badge text from backend
    
    return rx.link(
        rx.hstack(
            # 1. Format Box (Left Anchor)
            rx.center(
                rx.vstack(
                    rx.text(tournament["badge_l1"], size="3", weight="bold", color=TEXT_PRIMARY, line_height="1"),
                    rx.text(tournament["badge_l2"], size="1", weight="bold", color=TEXT_SECONDARY, line_height="1"),
                    spacing="0",
                    align="center",
                ),
                width="60px",
                height="60px",
                bg="rgba(255, 255, 255, 0.05)",
                border_radius="6px",
                border=f"1px solid {BORDER_COLOR}",
            ),
            
            # 2. Tournament Info (Center-Left)
            rx.vstack(
                # Name (Level 1)
                rx.text(
                    tournament["name"],
                    size="4",
                    weight="bold",
                    color="white",
                    font_family=SANS_FONT,
                    _hover={"color": "var(--accent-9)"}, # Cyan glow on hover
                    transition="color 0.2s"
                ),
                # Metadata (Level 3)
                rx.hstack(
                     rx.text(tournament["platform_label"].to(str).upper(), size="1", color="cyan", font_family=MONOSPACE_FONT),
                     rx.text("•", size="1", color=TEXT_SECONDARY),
                     rx.text(tournament["date"], size="1", color=TEXT_SECONDARY, font_family=MONOSPACE_FONT),
                     rx.text("•", size="1", color=TEXT_SECONDARY),
                     rx.text(tournament["location"], size="1", color=TEXT_SECONDARY),
                     spacing="2",
                     align="center"
                ),
                spacing="1",
                align="start",
                justify="center",
                height="100%",
                flex_grow="1",
                padding_x="12px"
            ),
            
            # 3. Counts (Right Anchor)
            rx.hstack(
                rx.vstack(
                    rx.text(f"{tournament['players']}", size="5", weight="bold", color=TEXT_PRIMARY, line_height="1", font_family=MONOSPACE_FONT),
                    rx.text("PLY", size="1", color=TEXT_SECONDARY, font_family=MONOSPACE_FONT),
                    spacing="0",
                    align="end"
                ),
                # Placeholder for Teams if we had it, for now just Players
                padding_right="12px",
                align="center",
                height="100%"
            ),

            width="100%",
            height="80px", # Fixed height for uniformity
            align="center",
            padding="10px",
            border_bottom=f"1px solid {BORDER_COLOR}",
            _hover={
                "bg": "rgba(255, 255, 255, 0.02)",
            },
            transition="background 0.2s"
        ),
        href="/tournament/" + tournament["id"].to_string(),
        style={"text_decoration": "none", "width": "100%"}
    )


def render_filters() -> rx.Component:
    """Render the sidebar filters for Tournaments."""
    return rx.vstack(
        rx.text("TOURNAMENT FILTERS", size="2", weight="bold", letter_spacing="1px", color=TEXT_PRIMARY),
        
        # 1. Date Range
        rx.vstack(
            rx.text("Date Range", size="1", weight="bold", color=TEXT_SECONDARY),
            rx.vstack(
                rx.input(
                    type="date",
                    value=TournamentsState.date_range_start,
                    on_change=TournamentsState.set_date_start,
                    style=INPUT_STYLE,
                    width="100%"
                ),
                rx.text("to", size="1", color=TEXT_SECONDARY, text_align="center"),
                rx.input(
                    type="date",
                    value=TournamentsState.date_range_end,
                    on_change=TournamentsState.set_date_end,
                    style=INPUT_STYLE,
                    width="100%"
                ),
                spacing="1",
                width="100%",
                padding="8px",
                border=f"1px solid {BORDER_COLOR}",
                border_radius=RADIUS
            ),
            spacing="1",
            width="100%"
        ),
        
        # 2. Location Filter
        rx.box(
            location_filter(TournamentsState),
            width="100%",
        ),

        # 3. Format Filter
        rx.box(
            hierarchical_format_filter(TournamentsState),
            width="100%",
        ),

        # 4. Search Bar (at the bottom of filters)
        rx.vstack(
            rx.text("Search Name", size="1", weight="bold", color=TEXT_SECONDARY, font_family=MONOSPACE_FONT),
            rx.input(
                placeholder="Search name...",
                value=TournamentsState.search_query,
                on_change=TournamentsState.set_search,
                style=INPUT_STYLE,
                width="100%",
                color_scheme="gray",
            ),
            spacing="1",
            width="100%"
        ),

        spacing="6",
        width="100%",
        min_width="250px",
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
                 TournamentsState.total_items_count.to_string() + " Tournaments Found",
                 size="2", color=TEXT_SECONDARY, font_family=MONOSPACE_FONT
             ),
             width="100%",
             margin_bottom="16px"
        ),

        # Tournament grid
        rx.cond(
            TournamentsState.tournaments.length() > 0,
            rx.vstack(
                rx.foreach(
                    TournamentsState.tournaments,
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
