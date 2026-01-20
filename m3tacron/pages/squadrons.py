"""
Squadrons Page - Imperial Data Terminal Spec.
"""
import reflex as rx
from sqlmodel import Session, select
from collections import Counter

from ..components.card_tooltip import pilot_card_tooltip
from ..components.sidebar import layout
from ..backend.database import engine
from ..backend.models import PlayerResult, Tournament
from ..backend.enums.formats import FORMAT_HIERARCHY, get_format
from ..backend.squadron_utils import get_squadron_signature, parse_squadron_signature
from ..backend.enums.factions import Faction
from ..theme import (
    FACTION_COLORS, TERMINAL_BG, BORDER_COLOR, TERMINAL_PANEL,
    TEXT_PRIMARY, TEXT_SECONDARY, MONOSPACE_FONT, SANS_FONT, INPUT_STYLE,
    TERMINAL_PANEL_STYLE, RADIUS, FACTION_ICONS
)
from ..components.icons import ship_icon
from ..backend.xwing_data import load_all_pilots, get_pilot_info


class SquadronsState(rx.State):
    """State for the Squadrons browser page."""
    format_filter: str = "all"
    faction_filter: str = "all"
    
    # New Filters
    date_range_start: str = "" # YYYY-MM-DD
    date_range_end: str = ""   # YYYY-MM-DD
    ship_filter: str = ""      # Filter by specific ship name
    sort_mode: str = "popularity" # "popularity" or "win_rate"
    
    # Autocomplete options
    all_ships: list[str] = []
    
    # Overrides for XWS IDs that don't match the font class names
    SHIP_ICON_OVERRIDES: dict[str, str] = {
        "tieininterceptor": "tieinterceptor",
        "tieadvx1": "tieadvancedx1",
        "tieadvv1": "tieadvancedv1",
        "scavengedyt1300lightfreighter": "scavengedyt1300", 
        "xixt3classlightshuttle": "xiclasslightshuttle",
        "bwing": "asf01bwing", # legacy check
        "ywing": "btla4ywing", # legacy check
    }
    
    squadrons_data: list[dict] = []
    total_squadrons: int = 0
    total_lists: int = 0
    
    page_size: int = 20
    current_page: int = 0
    
    selected_squadron: str = ""
    squadron_details: dict = {}
    current_ships: list[str] = []
    current_rich_ships: list[dict] = []
    
    def set_format_filter(self, value: str):
        self.format_filter = value
        self.current_page = 0
        self.load_squadrons()
    
    def set_faction_filter(self, value: str):
        self.faction_filter = value
        self.current_page = 0
        self.load_squadrons()
        
    def set_ship_filter(self, value: str):
        self.ship_filter = value
        self.current_page = 0
        self.load_squadrons()
        
    def set_date_range_start(self, value: str):
        self.date_range_start = value
        self.load_squadrons()
        
    def set_date_range_end(self, value: str):
        self.date_range_end = value
        self.load_squadrons()
        
    def set_sort_mode(self, value: str):
        self.sort_mode = value
        self.load_squadrons()
    
    def next_page(self):
        self.current_page += 1
    
    def prev_page(self):
        if self.current_page > 0:
            self.current_page -= 1
    
    def load_squadrons(self):
        with Session(engine) as session:
            # Optimize: Join with Tournament to filter by date/format efficiently
            query = select(PlayerResult, Tournament).where(PlayerResult.tournament_id == Tournament.id)
            
            # 1. Apply Filters
            if self.format_filter != "all":
                # We can't easily filter by property 'macro_format' in SQL translation usually, 
                # but we can filter by the raw column if needed, or filter in python if dataset is small.
                # For now, let's fetch all and filter in python to be safe with the Enum logic, 
                # or better, iterate.
                pass 
                
            # Execute query - fetching necessary fields
            rows = session.exec(query).all()
            
            # Post-SQL Filtering (Python side for flexibility with Props/Enums)
            filtered_rows = []
            valid_ships = set() # Collect all ships for autocomplete
            
            for result, tournament in rows:
                # Filter by Format
                if self.format_filter != "all" and tournament.macro_format != self.format_filter:
                    continue
                
                # Filter by Date
                if self.date_range_start and str(tournament.date) < self.date_range_start:
                    continue
                if self.date_range_end and str(tournament.date) > self.date_range_end:
                    continue

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
                if self.faction_filter != "all" and faction != self.faction_filter: continue
                
                # Filter by Ship (Search)
                if self.ship_filter:
                    search_term = self.ship_filter.lower()
                    if not any(search_term in s.lower() for s in ships):
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
                wins = r.swiss_wins + r.cut_wins
                losses = r.swiss_losses + r.cut_losses
                draws = r.swiss_draws
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

            self.total_squadrons = len(processed_list)
            
            # Pagination
            start = self.current_page * self.page_size
            page_items = processed_list[start:start + self.page_size]
            
            self.squadrons_data = []
            
            # Helper for icons update
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
                    icon_xws = self.SHIP_ICON_OVERRIDES.get(raw_xws, raw_xws)
                    
                    ship_ui_list.append({
                        "name": name,
                        "count": count,
                        "icon": icon_xws,
                        "color": FACTION_COLORS.get(faction, TEXT_SECONDARY),
                    })
                
                raw_faction = faction.lower().replace(" ", "").replace("-", "")
                
                self.squadrons_data.append({
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
            icon_xws = self.SHIP_ICON_OVERRIDES.get(raw_xws, raw_xws)
            
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
                # Apply Filters (Reuse logic - simpler if extracted but Inline is fine for now)
                if self.format_filter != "all" and tournament.macro_format != self.format_filter: continue
                if self.date_range_start and str(tournament.date) < self.date_range_start: continue
                if self.date_range_end and str(tournament.date) > self.date_range_end: continue
                
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
    options = [["All", "all"]] + [[item["label"], item["value"]] for item in FORMAT_HIERARCHY]
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
    from ..backend.enums.factions import Faction
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

def ship_filter_input() -> rx.Component:
    return rx.box(
        rx.input(
            placeholder="Search Ship... (e.g. X-wing)",
            value=SquadronsState.ship_filter,
            on_change=SquadronsState.set_ship_filter,
            style=INPUT_STYLE,
            list="ships-datalist"
        ),
        rx.el.datalist(
            rx.foreach(
                SquadronsState.all_ships,
                lambda s: rx.el.option(value=s)
            ),
            id="ships-datalist"
        )
    )

def date_filter_inputs() -> rx.Component:
    return rx.hstack(
        rx.input(
            type="date",
            placeholder="Start Date",
            value=SquadronsState.date_range_start,
            on_change=SquadronsState.set_date_range_start,
            style=INPUT_STYLE,
            width="130px"
        ),
        rx.text("-", color=TEXT_SECONDARY),
        rx.input(
            type="date",
            placeholder="End Date",
            value=SquadronsState.date_range_end,
            on_change=SquadronsState.set_date_range_end,
            style=INPUT_STYLE,
            width="130px"
        ),
        align="center",
        spacing="2"
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


def pagination_controls() -> rx.Component:
    return rx.hstack(
        rx.button("< PREV", variant="ghost", size="1", on_click=SquadronsState.prev_page, disabled=SquadronsState.current_page == 0, style={"color": TEXT_PRIMARY, "font_family": MONOSPACE_FONT}),
        rx.text(f"Page {SquadronsState.current_page + 1}", size="2", color=TEXT_SECONDARY, font_family=MONOSPACE_FONT),
        rx.button("NEXT >", variant="ghost", size="1", on_click=SquadronsState.next_page, style={"color": TEXT_PRIMARY, "font_family": MONOSPACE_FONT}),
        spacing="2",
        align="center",
    )


def render_ship_icon_group(ship: dict) -> rx.Component:
    """Render a group of ship icons for a single chassis (e.g. 3x X-Wing)."""
    return rx.tooltip(
        rx.hstack(
            rx.cond(
                ship["count"].to(int) > 1,
                rx.text(f"{ship['count']}x", size="1", color=ship["color"], font_family=MONOSPACE_FONT, weight="bold"),
                rx.fragment()
            ),
            ship_icon(ship["icon"], size="1.2em", color=ship["color"]),
            spacing="1",
            align="center",
            style={"cursor": "help"}
        ),
        content=ship["name"]
    )


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
                    rx.cond(
                        faction_icon_class.to(str) != "",
                        rx.el.i(class_name=f"xwing-miniatures-font {faction_icon_class.to(str)}", style={"color": faction_color, "font_size": "1.5em", "margin_right": "8px"}),
                        rx.fragment()
                    ),
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
                    rx.cond(
                        SquadronsState.squadron_details["faction_icon"].to(str) != "",
                        rx.el.i(class_name=SquadronsState.squadron_details["faction_icon"].to(str), style={"color": SquadronsState.squadron_details["faction_color"], "font_size": "2em", "margin_right": "12px"}),
                        rx.fragment()
                    ),
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
            rx.text(f"{SquadronsState.total_squadrons} UNIQUE SQUADRONS", size="2", color=TEXT_SECONDARY, font_family=MONOSPACE_FONT),
            rx.spacer(),
            rx.flex(
                date_filter_inputs(),
                faction_filter_select(),
                format_filter_select(),
                ship_filter_input(),
                sort_select(),
                spacing="2",
                wrap="wrap",
                justify="end"
            ),
            spacing="4",
            width="100%",
            margin_bottom="16px",
            justify="between",
            wrap="wrap"
        ),
        rx.grid(
            rx.foreach(SquadronsState.squadrons_data.to(list[dict]), squadron_card),
            columns="2",
            spacing="4",
            width="100%",
        ),
        rx.hstack(rx.spacer(), pagination_controls(), width="100%", margin_top="24px"),
        align="start",
        width="100%",
        max_width="1200px",
        on_mount=SquadronsState.load_squadrons,
        padding_bottom="60px"
    )

def squadrons_page() -> rx.Component:
    return layout(rx.fragment(squadrons_content(), render_squadron_detail()))
