"""
Squadrons Page.
"""
import reflex as rx
from sqlmodel import Session, select
from collections import Counter

from ..components.card_tooltip import pilot_card_tooltip
from ..components.sidebar import layout, dashboard_layout
from ..backend.database import engine
from ..backend.models import PlayerResult, Tournament
from ..backend.data_structures.formats import Format, MacroFormat
from ..backend.utils.squadron import get_squadron_signature, parse_squadron_signature
from ..backend.data_structures.factions import Faction
from ..components.tournament_filters import tournament_filters
# from ..components.tournament_filters import TournamentFilterMixin - REMOVED
from ..backend.state.global_filter_state import GlobalFilterState
# from ..components.multi_filter import collapsible_checkbox_group # Replaced by filter_accordion
from ..components.filter_accordion import filter_accordion
from ..ui_utils.pagination import PaginationMixin
from ..components.pagination import pagination_controls
from ..theme import (
    FACTION_COLORS, TERMINAL_BG, BORDER_COLOR, TERMINAL_PANEL,
    TEXT_PRIMARY, TEXT_SECONDARY, MONOSPACE_FONT, SANS_FONT, INPUT_STYLE,
    TERMINAL_PANEL_STYLE, RADIUS, FACTION_ICONS
)
from ..components.ui import empty_state
from ..ui_utils.factions import faction_icon, get_faction_color
from ..components.icons import ship_icon
from ..backend.utils.xwing_data.pilots import load_all_pilots, get_pilot_info
from ..backend.utils.xwing_data.ships import get_filtered_ships
from ..components.searchable_filter_accordion import searchable_filter_accordion
from ..ui_utils.ships import get_ship_icon_name, render_ship_icon_group


class SquadronsState(PaginationMixin):
    """State for the Squadrons browser page."""
    # Multi-Select Filters
    selected_factions: dict[str, bool] = {}
    
    # --- Accordion States (Smart Persistence) ---
    faction_acc_val: list[str] = []
    ship_acc_val: list[str] = []
    
    def set_faction_acc_val(self, val):
        self.faction_acc_val = val
        
    def set_ship_acc_val(self, val):
        self.ship_acc_val = val
    
    # Static Options
    faction_options: list[list[str]] = [[f.label, f.value] for f in Faction if f != Faction.UNKNOWN]

    async def on_mount(self):
        gs = await self.get_state(GlobalFilterState)
        gs.load_locations()
        # Initialize default formats if needed (e.g. XWA defaults)
        if not gs.selected_formats:
             gs.set_default_formats_for_source(gs.data_source)
             
        # Initialize selected_factions keys to prevent binding errors
        if not self.selected_factions:
             for f_list in self.faction_options:
                 self.selected_factions[f_list[1]] = False

        # --- Smart Accordion Logic ---
        # Faction
        has_faction = any(self.selected_factions.values())
        if has_faction:
            self.faction_acc_val = ["Faction"]
            
        # Ship
        has_ship = any(self.selected_ships.values()) or self.ship_search_query
        if has_ship:
            self.ship_acc_val = ["Ship Chassis"]
             
        await self.load_squadrons()

    # Redundant total_pages_squadrons removed


    def on_page_change(self):
        """Handle page changes by reloading data."""
        self.update_view()

    # Override Pagination Methods to fix Reflex Mixin Dispatch
    def next_page(self):
        self.current_page += 1
        self.update_view()

    def prev_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.update_view()

    async def on_tournament_filter_change(self):
        self.current_page = 0
        await self.load_squadrons()

    async def reset_squadron_filters(self):
        """Reset only squadron-specific filters."""
        self.selected_factions = {}
        self.selected_ships = {}
        self.ship_search_query = ""
        self.current_page = 0
        await self.load_squadrons()

    async def reset_tournament_filters_wrapper(self):
        """Reset only global tournament filters."""
        gs = await self.get_state(GlobalFilterState)
        gs.reset_tournament_filters()
        self.current_page = 0
        await self.load_squadrons()

    async def reset_all_filters(self):
        """Reset both global tournament filters and local squadron filters."""
        gs = await self.get_state(GlobalFilterState)
        gs.reset_tournament_filters()
        self.selected_factions = {}
        self.selected_ships = {}
        self.ship_search_query = ""
        self.current_page = 0
        await self.load_squadrons()

    # --- Mixin Overrides REMOVED (Handled by GlobalState) ---
    
    async def toggle_faction(self, faction: str, checked: bool):
        self.selected_factions[faction] = checked
        self.current_page = 0
        await self.load_squadrons()
    
    # New Filters
    # date_range_start: str = "" # YYYY-MM-DD - Handled by Mixin
    # date_range_end: str = ""   # YYYY-MM-DD - Handled by Mixin
    ship_filter: str = ""      # Filter by specific ship name
    sort_mode: str = "popularity" # "popularity" or "win_rate"
    
    # Autocomplete options
    all_ships: list[str] = []
    
    
    # Data
    squadrons_data: list[dict] = []
    _all_squadrons_cached: list[dict] = []
    total_lists: int = 0
    
    selected_squadron: str = ""
    squadron_details: dict = {}
    current_ships: list[str] = []
    current_rich_ships: list[dict] = []
    

    # Ship Filter
    ship_search_query: str = ""
    selected_ships: dict[str, bool] = {}
     
    @rx.var
    def available_ships(self) -> list[list[str]]:
        """
        Get compatible ships based on selected factions and search query.
        Returns: [[Label, Value], ...]
        """
        # 1. Get filtered list from backend
        # selected_factions keys where value is True
        active_factions = [k for k,v in self.selected_factions.items() if v]
        # XWS data uses normalized keys? In toggle_faction we use values from opts.
        # Faction options are [Label, 'Rebel Alliance']. 
        # xwing_data.get_filtered_ships expects XWS faction strings usually?
        # Let's check xwing_data.
        # xwing_data.get_filtered_ships -> checks `ship["factions"]` which are usually mixed or labels?
        # In load_all_ships: ships_map[xws]["factions"].add(data.get("faction") or current_faction)
        # These are usually the strings from JSON, e.g. "Rebel Alliance".
        # So passing "Rebel Alliance" (Value from frontend) should work.
        
        # We need to map our frontend Faction Enum Values to what xwing_data expects?
        # Frontend: "Rebel Alliance". Backend: seems to store "Rebel Alliance".
        
        # Let's clean up:
        factions_input = active_factions if active_factions else None
        
        ships = get_filtered_ships(factions_input)
        
        # 2. Convert to options
        options = []
        q = self.ship_search_query.lower()
        
        for s in ships:
            label = s["name"]
            val = s["name"] # Use Name as value for simplicity in UI state key
            
            if not q or q in label.lower():
                options.append([label, val])
                
        return options

    def set_ship_search_query(self, value: str):
        self.ship_search_query = value

    async def toggle_ship(self, value: str, checked: bool):
        self.selected_ships[value] = checked
        self.current_page = 0
        await self.load_squadrons()

    # def set_date_range_start(self, value: str):
    #     self.date_range_start = value
    #     self.load_squadrons()
        
    # def set_date_range_end(self, value: str):
    #     self.date_range_end = value
    #     self.load_squadrons()
        
    async def set_sort_mode(self, value: str):
        self.sort_mode = value
        await self.load_squadrons()
    
    def update_view(self):
        """Slice cache and populate UI data."""
        start = self.current_page * self.page_size
        page_items = self._all_squadrons_cached[start:start + self.page_size]
        
        new_data = []
        
        # Helper for icons update (need to load pilots if not already loaded, but should be fast)
        # Ideally this map should be cached too or computed once in load_squadrons if static enough
        all_pilots = load_all_pilots()
        ship_map = {p["ship"]: p.get("ship_xws", "") for p in all_pilots.values() if "ship" in p and "ship_xws" in p}

        for item in page_items:
            faction = item["faction"]
            ships = item["ships_list"]
            
            # Format Ships for UI
            ship_counts = Counter(ships)
            ship_ui_list = []
            for name, count in sorted(ship_counts.items()):
                raw_xws = ship_map.get(name, "")
                if not raw_xws:
                    raw_xws = name.lower().replace(" ", "").replace("-", "")
                icon_xws = get_ship_icon_name(raw_xws)
                
                ship_ui_list.append({
                    "name": name,
                    "count": count,
                    "icon": icon_xws,
                    "color": FACTION_COLORS.get(faction, TEXT_SECONDARY),
                })
            
            raw_faction = faction.lower().replace(" ", "").replace("-", "")
            
            new_data.append({
                "signature": item["signature"],
                "faction": Faction.from_xws(faction).label,
                "faction_key": faction,
                "icon": FACTION_ICONS.get(raw_faction, ""),
                "ships": ship_ui_list,
                "count": item["count"],
                "format_play_rate": round(item["count"] / max(self.total_lists, 1) * 100, 1),
                "win_rate": round(item["win_rate"], 1),
                "games": item["games"],
                "color": FACTION_COLORS.get(raw_faction, TEXT_SECONDARY),
            })
        
        self.squadrons_data = new_data

    async def load_squadrons(self):
        print("DEBUG: load_squadrons called")
        gs = await self.get_state(GlobalFilterState)
        with Session(engine) as session:
            # Optimize: Join with Tournament to filter by date/format efficiently
            query = select(PlayerResult, Tournament).where(PlayerResult.tournament_id == Tournament.id)
            
            # 1. Apply Filters
            # SQL level format filter difficult with detailed hierarchy/enum mix, do mostly in python
            pass 
                
            # Execute query - fetching necessary fields
            rows = session.exec(query).all()
            
            # Post-SQL Filtering (Python side for flexibility with Props/Enums)
            # gs loaded above
            filtered_rows = []
            
            for result, tournament in rows:
                # Filter by Format
                t_fmt_raw = tournament.format
                t_fmt = str(t_fmt_raw) if t_fmt_raw else "other"
                
                if gs.selected_formats:
                     if not gs.selected_formats.get(t_fmt, False):
                         continue
                
                # Filter by Date
                if gs.date_range_start and str(tournament.date) < gs.date_range_start:
                    continue
                if gs.date_range_end and str(tournament.date) > gs.date_range_end:
                    continue

                # Filter by Location
                active_continents = [k for k, v in gs.selected_continents.items() if v]
                active_countries = [k for k, v in gs.selected_countries.items() if v]
                active_cities = [k for k, v in gs.selected_cities.items() if v]
                
                if active_continents or active_countries or active_cities:
                    loc = tournament.location
                    if not loc: continue
                    if active_continents and (not loc.continent or loc.continent not in active_continents): continue
                    if active_countries and (not loc.country or loc.country not in active_countries): continue
                    if active_cities and (not loc.city or loc.city not in active_cities): continue

                filtered_rows.append(result)

            # Aggregation
            squadron_stats = {} # signature -> {count, wins, games, ...}
            
            all_pilots = load_all_pilots()
            # ship_map = {p["ship"]: p.get("ship_xws", "") for p in all_pilots.values() if "ship" in p and "ship_xws" in p}
            
            for r in filtered_rows:
                xws = r.list_json
                if not xws or not isinstance(xws, dict): continue
                sig = get_squadron_signature(xws)
                if not sig: continue
                
                faction, ships = parse_squadron_signature(sig)
                
                # Filter by Faction
                # Multi-Select Faction Check
                # If selected_factions has true entries, current faction must be one of them.
                active_factions = [k for k,v in self.selected_factions.items() if v]
                if active_factions:
                    # Normalize sig faction? 
                    # Sig uses Faction Enum Value usually? or Label?
                    # parse_squadron_signature returns faction NAME usually if I recall utils.
                    # Let's check or normalize. Faction.from_xws(faction).value
                    # Wait, parse_squadron_signature returns "Rebel Alliance" (label) or value?
                    # Sig: "rebelalliance_..." -> faction segment is xws.
                    # But parse_squadron_signature might return xws or label. 
                    # Let's check Faction.from_xws usage below -> `Faction.from_xws(faction).label`.
                    # So 'faction' variable here is likely XWS or Label?
                    # `Faction.from_xws` handles both.
                    # Let's use the value for comparison.
                    current_fac_val = Faction.from_xws(faction).value
                    # Check against active_factions (which use values if we set them up that way)
                    # We will set up options using values.
                    if current_fac_val not in active_factions:
                        continue
                
                # Filter by Ship (Multi-Select OR)
                # If selected_ships has active entries, current list must contain at least one.
                active_ships = [k for k,v in self.selected_ships.items() if v]
                if active_ships:
                    # Check intersection
                    # Squad ships are in `ships` list (names)
                    if set(active_ships).isdisjoint(ships):
                        continue
                
                # Collect valid ships for autocomplete (only from visible results? or all? Let's do all visible)
                # valid_ships.update(ships) 
                
                if sig not in squadron_stats:
                    squadron_stats[sig] = {
                        "count": 0, 
                        "wins": 0, 
                        "games": 0, 
                        "faction": faction,
                        "ships": ships
                    }
                
                stats = squadron_stats[sig]
                stats["count"] += 1
                
                # Calculate games/wins
                # Swiss + Cut
                wins = (r.swiss_wins or 0) + (r.cut_wins or 0)
                losses = (r.swiss_losses or 0) + (r.cut_losses or 0)
                draws = (r.swiss_draws or 0) + (r.cut_draws or 0)
                games = wins + losses + draws

                
                # If no record of games (e.g. only rank), heuristic? 
                # For now rely on recorded wins/losses.
                stats["wins"] += wins
                stats["games"] += games

            self.total_lists = sum(s["count"] for s in squadron_stats.values())
            
            # Convert to list for sorting
            # Filter out squadrons with very few games for Win Rate sorting?
            # Let's keep all but maybe deprioritize in UI if 0 games?
            
            processed_list = []
            for sig, stats in squadron_stats.items():
                win_rate = 0.0
                if stats["games"] > 0:
                    win_rate = (stats["wins"] / stats["games"]) * 100
                    
                processed_list.append({
                    "signature": sig,
                    "faction": stats["faction"],
                    "ships_list": stats["ships"], # Raw list
                    "count": stats["count"],
                    "wins": stats["wins"],
                    "games": stats["games"],
                    "win_rate": win_rate
                })
            
            # Sorting
            if self.sort_mode == "win_rate":
                # Sort by Win Rate (DESC), then Count (DESC)
                # Penalty for low game count could be applied here (Bayesian average?), but let's stick to simple
                # Maybe filter out single occurrences?
                processed_list.sort(key=lambda x: (x["games"] > 5, x["win_rate"], x["count"]), reverse=True)
            else:
                # Default: Popularity
                processed_list.sort(key=lambda x: x["count"], reverse=True)

            self.total_items_count = len(processed_list)
            self._all_squadrons_cached = processed_list
            self.current_page = 0
            
            self.update_view()
                
            # Populate autocomplete if empty (first run)
            if not self.all_ships:
                # Get unique ships from all pilots db (so we have a complete list, not just what's in tournaments)
                # or just from the loaded data? Data is better for "available" ships.
                # Let's use all known pilots for a complete filter.
                self.all_ships = sorted(list(set(p["ship"] for p in all_pilots.values() if "ship" in p)))
    
    def open_detail(self, signature: str):
        self.selected_squadron = signature
        faction, ships = parse_squadron_signature(signature)
        self.current_ships = ships
        
        # Build rich ship data for the modal
        all_pilots = load_all_pilots()
        ship_map = {p["ship"]: p.get("ship_xws", "") for p in all_pilots.values() if "ship" in p and "ship_xws" in p}
        ship_counts = Counter(ships)
        
        ship_list = []
        # Normalize faction for color lookup
        raw_faction = faction.lower().replace(" ", "").replace("-", "")
        faction_color = FACTION_COLORS.get(raw_faction, TEXT_SECONDARY)
        faction_icon = FACTION_ICONS.get(raw_faction, "")

        for name, count in sorted(ship_counts.items()):
            raw_xws = ship_map.get(name, "")
            if not raw_xws:
                raw_xws = name.lower().replace(" ", "").replace("-", "")
            icon_xws = get_ship_icon_name(raw_xws)
            
            ship_list.append({
                "name": name,
                "count": count,
                "icon": icon_xws,
                "color": faction_color,
            })
            
        self.current_rich_ships = ship_list

        # --- Aggregation for Pilot Variations ---
        # Re-fetch matching lists to analyze pilots
        # We respect the current filters to show relevant data
        
        with Session(engine) as session:
            query = select(PlayerResult, Tournament).where(PlayerResult.tournament_id == Tournament.id)
            rows = session.exec(query).all()
            
            pilot_variations = Counter()
            
            for result, tournament in rows:
                # Apply Filters
                t_fmt_raw = tournament.format
                t_fmt = str(t_fmt_raw) if t_fmt_raw else "other"
                
                if gs.selected_formats and not gs.selected_formats.get(t_fmt, False):
                    continue
                    
                if gs.date_range_start and str(tournament.date) < gs.date_range_start: continue
                if gs.date_range_end and str(tournament.date) > gs.date_range_end: continue
                
                xws = result.list_json
                if not xws or not isinstance(xws, dict): continue
                
                # Check Signature
                sig = get_squadron_signature(xws)
                if sig != signature: continue
                
                # Extract Pilots
                pilots = []
                for p in xws.get("pilots", []):
                    pid = p.get("id") or p.get("name")
                    pinfo = get_pilot_info(pid)
                    pname = pinfo.get("name", pid) if pinfo else pid
                    pilots.append(pname)
                
                pilots.sort()
                pilot_sig = " + ".join(pilots)
                pilot_variations[pilot_sig] += 1
                
        # Format Top Variations
        common_pilots = []
        for p_sig, count in pilot_variations.most_common(5): # Top 5
            common_pilots.append({
                "pilots": p_sig,
                "count": count,
                "percent": round(count / max(sum(pilot_variations.values()), 1) * 100, 1)
            })

        self.squadron_details = {
            "subtitle": f"{squadron['faction']} • {squadron['count']} lists", # subtitle - Wait, 'squadron' var isn't available here effectively unless passed. 
            # We can reconstruct it or just use generic text.
            "faction": Faction.from_xws(faction).label,
            "faction_key": faction,
            "faction_color": faction_color,
            "faction_icon": faction_icon,
            "ships": ship_list,
            "common_pilots": common_pilots 
        }
    
    def close_detail(self):
        self.selected_squadron = ""
        self.squadron_details = {}
        self.current_ships = []
        self.current_rich_ships = []

    def handle_open_change(self, is_open: bool):
        if not is_open:
            self.close_detail()


def format_filter_select() -> rx.Component:
    """Format filter dropdown using label/value pairs."""
    options = get_format_options()
    return rx.select.root(
        rx.select.trigger(placeholder="Format", style=INPUT_STYLE),
        rx.select.content(
            rx.foreach(
                options,
                lambda opt: rx.select.item(opt[0], value=opt[1])
            )
        ),
        value=SquadronsState.format_filter,
        on_change=SquadronsState.set_format_filter,
        size="2",
    )


def faction_filter_select() -> rx.Component:
    """Faction filter dropdown using label/value pairs."""
    from ..backend.data_structures.factions import Faction
    options = [["All", "all"]] + [[f.label, f.value] for f in Faction if f != Faction.UNKNOWN]
    return rx.select.root(
        rx.select.trigger(placeholder="Faction", style=INPUT_STYLE),
        rx.select.content(
             rx.select.group(
                rx.foreach(
                    options,
                    lambda opt: rx.select.item(opt[0], value=opt[1])
                )
             )
        ),
        value=SquadronsState.faction_filter,
        on_change=SquadronsState.set_faction_filter,
        size="2",
    )



def sort_select() -> rx.Component:
    return rx.select.root(
        rx.select.trigger(placeholder="Sort By", style=INPUT_STYLE),
        rx.select.content(
             rx.select.group(
                rx.select.item("Popularity", value="popularity"),
                rx.select.item("Win Rate", value="win_rate"),
             )
        ),
        value=SquadronsState.sort_mode,
        on_change=SquadronsState.set_sort_mode,
        size="2",
    )

def render_sidebar_filters() -> rx.Component:
    """Render the sidebar filters for Squadrons."""
    return rx.vstack(
        rx.text("FILTERS", size="1", weight="bold", letter_spacing="1px", color=TEXT_SECONDARY),
        
        # Sort
        rx.vstack(
             rx.text("Sort By", size="1", color=TEXT_SECONDARY),
             sort_select(),
             width="100%",
             spacing="1"
        ),
        
        rx.divider(border_color=BORDER_COLOR, flex_shrink="0"),

        # Search Ship
        searchable_filter_accordion(
            "Ship Chassis",
            SquadronsState.available_ships,
            SquadronsState.selected_ships,
            SquadronsState.toggle_ship,
            SquadronsState.ship_search_query,
            SquadronsState.set_ship_search_query,
            accordion_value=SquadronsState.ship_acc_val,
            on_accordion_change=SquadronsState.set_ship_acc_val,
        ),
        
        rx.divider(border_color=BORDER_COLOR, flex_shrink="0"),

        # Tournament Filters
        rx.box(
            tournament_filters(
                on_change=SquadronsState.load_squadrons,
                reset_handler=SquadronsState.reset_tournament_filters_wrapper
            ),
            width="100%"
        ),
        
        rx.divider(border_color=BORDER_COLOR, flex_shrink="0"),
        
        # Squadron Filters Header with Reset
        rx.hstack(
            rx.text("SQUADRON FILTERS", size="2", weight="bold", letter_spacing="1px", color=TEXT_PRIMARY),
            rx.spacer(),
            rx.icon_button(
                rx.icon(tag="rotate-ccw"),
                on_click=SquadronsState.reset_squadron_filters,
                variable="ghost",
                color_scheme="gray",
                size="1",
                tooltip="Reset Squadron Filters"
            ),
            width="100%",
            align_items="center"
        ),
        filter_accordion(
            "Faction",
            SquadronsState.faction_options,
            SquadronsState.selected_factions,
            SquadronsState.toggle_faction,
            accordion_value=SquadronsState.faction_acc_val,
            on_accordion_change=SquadronsState.set_faction_acc_val,
        ),

        spacing="4",
        width="100%",
    )


def pagination_controls_squadrons() -> rx.Component:
    return pagination_controls(SquadronsState)




def squadron_card(squadron: dict) -> rx.Component:
    # Use pre-computed color and icon from backend state
    faction_color = squadron["color"]
    faction_icon_class = squadron["icon"]

    return rx.box(
        rx.hstack(
            rx.box(width="4px", height="100%", background=faction_color, min_height="60px"),
            rx.vstack(
                # Faction Header with Icon
                rx.hstack(
                    faction_icon(squadron["faction_key"], size="1.5em"),
                    rx.text(squadron["faction"], size="1", color=faction_color, weight="bold", font_family=MONOSPACE_FONT),
                    spacing="2",
                    align="center"
                ),
                
                # Replace text string with icon row
                rx.flex(
                    rx.foreach(squadron["ships"].to(list[dict]), render_ship_icon_group),
                    wrap="wrap",
                    spacing="2", # Reduced spacing
                    align="center"
                ),
                
                rx.hstack(
                    rx.text(f"[{squadron['count']} LISTS]", size="1", color=TEXT_PRIMARY, font_family=MONOSPACE_FONT),
                    rx.text(f"[{squadron['win_rate']}% WR]", size="1", color=rx.cond(
                         squadron["win_rate"].to(float) >= 50,
                         "green",
                         rx.cond(squadron["win_rate"].to(float) > 0, "orange", "gray")
                    ), font_family=MONOSPACE_FONT),
                    rx.text(f"({squadron['games']} G)", size="1", color=TEXT_SECONDARY, font_family=MONOSPACE_FONT),
                    spacing="2",
                ),
                align="start",
                spacing="2",
                flex="1",
                width="100%"
            ),
            width="100%",
            spacing="3",
            padding="12px",
            align_items="stretch", # Force side bar to stretch to content
            height="100%", # Force hstack to fill the card height (if grid stretches it)
        ),
        style=TERMINAL_PANEL_STYLE,
        border_radius=RADIUS, # Use Standard RADIUS
        _hover={"border_color": faction_color, "cursor": "pointer", "background": "rgba(255, 255, 255, 0.05)"},
        transition="all 0.2s ease",
        on_click=lambda: SquadronsState.open_detail(squadron["signature"]),
    )


def render_squadron_detail() -> rx.Component:
    """Render the squadron detail modal."""
    # details = SquadronsState.squadron_details
    return rx.dialog.root(
        rx.dialog.content(
            rx.vstack(
                # Header with Faction Icon
                rx.hstack(
                    faction_icon(SquadronsState.squadron_details["faction_key"], size="2em"),
                    rx.heading(
                        SquadronsState.squadron_details["faction"], 
                        size="5", 
                        font_family=SANS_FONT,
                        color=SquadronsState.squadron_details["faction_color"]
                    ),
                    width="100%",
                    align="center",
                    padding_bottom="16px",
                    border_bottom=f"1px solid {BORDER_COLOR}",
                ),
                
                # Ship List in Modal
                rx.text("SHIPS", color=TEXT_SECONDARY, size="1"),
                rx.flex(
                    rx.foreach(
                        SquadronsState.current_rich_ships,
                        render_ship_icon_group
                    ),
                    wrap="wrap",
                    spacing="4",
                    padding_y="16px"
                ),
                
                # Pilot Variations
                rx.cond(
                    SquadronsState.squadron_details["common_pilots"].to(list).length() > 0,
                    rx.vstack(
                        rx.text("TOP PILOT CONFIGURATIONS", color=TEXT_SECONDARY, size="1", font_family=MONOSPACE_FONT),
                        rx.foreach(
                            SquadronsState.squadron_details["common_pilots"].to(list[dict]),
                            lambda p: rx.hstack(
                                rx.text(f"{p['count']}x", width="40px", color=TEXT_SECONDARY, size="1", font_family=MONOSPACE_FONT),
                                rx.text(p['pilots'], color=TEXT_PRIMARY, size="1", font_family=SANS_FONT, flex="1"),
                                rx.text(f"{p['percent']}%", width="50px", text_align="right", color=TEXT_SECONDARY, size="1", font_family=MONOSPACE_FONT),
                                width="100%",
                                padding_y="4px",
                                border_bottom=f"1px solid {BORDER_COLOR}"
                            )
                        ),
                        width="100%",
                        spacing="2"
                    ),
                    rx.fragment()
                ),
                
                # Close Button
                rx.flex(
                    rx.dialog.close(
                        rx.button("CLOSE", variant="soft", color_scheme="gray", on_click=SquadronsState.close_detail)
                    ),
                    justify="end",
                    width="100%",
                    margin_top="16px"
                ),
                spacing="4",
                width="100%",
            ),
            style={"background": TERMINAL_PANEL, "border": f"1px solid {BORDER_COLOR}"},
            max_width="600px",
        ),
        open=SquadronsState.selected_squadron != "",
        on_open_change=SquadronsState.handle_open_change,
    )


def squadrons_content() -> rx.Component:
    return rx.vstack(
        rx.box(
            rx.heading("Squadrons", size="6", font_family=SANS_FONT, weight="bold", color=TEXT_PRIMARY),
            padding_bottom="24px",
            border_bottom=f"1px solid {BORDER_COLOR}",
            margin_bottom="24px",
            width="100%"
        ),
        rx.flex(
            rx.text(f"{SquadronsState.total_items_count} UNIQUE SQUADRONS", size="2", color=TEXT_SECONDARY, font_family=MONOSPACE_FONT),
            rx.spacer(),
            width="100%", 
            justify="between", 
            align="center",
            margin_bottom="16px"
        ),
        rx.cond(
            SquadronsState.squadrons_data.length() > 0,
            rx.vstack(
                rx.grid(
                    rx.foreach(SquadronsState.squadrons_data, squadron_card),
                    columns={"initial": "1", "md": "2"},
                    spacing="4",
                    width="100%",
                ),
                rx.hstack(rx.spacer(), pagination_controls_squadrons(), width="100%", margin_top="24px"),
                width="100%",
                spacing="0",
            ),
            rx.box(
                empty_state(
                    title="0 SQUADRONS FOUND",
                    description="No squadrons match your current filters or search query.",
                    icon_tag="swords",
                    reset_handler=SquadronsState.reset_all_filters
                ),
                width="100%",
                padding_y="48px"
            ),

        ),
        align="start",
        width="100%",
        max_width="1200px",
        on_mount=SquadronsState.load_squadrons,
        padding_bottom="60px"
    )

def squadrons_browser_page() -> rx.Component:
    return layout(
        rx.fragment(
            dashboard_layout(
                render_sidebar_filters(),
                squadrons_content()
            ),
            render_squadron_detail()
        )
    )
