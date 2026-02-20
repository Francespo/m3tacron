
"""
List Browser Page.
"""
import reflex as rx
from sqlmodel import Session, select
from collections import Counter
import math
from typing import Any


from ..components.sidebar import layout, dashboard_layout
from ..backend.database import engine
from ..backend.models import PlayerResult, Tournament
from ..backend.utils.squadron import get_list_signature, parse_squadron_signature
from ..backend.data_structures.factions import Faction
from ..backend.data_structures.data_source import DataSource
from ..backend.data_structures.data_source import DataSource
from ..components.tournament_filters import tournament_filters
from ..backend.state.global_filter_state import GlobalFilterState
from ..components.content_source_filter import content_source_filter
from ..components.filter_accordion import filter_accordion
from ..components.pagination import pagination_controls
from ..ui_utils.pagination import PaginationMixin

from ..theme import (
    TEXT_PRIMARY, TEXT_SECONDARY, MONOSPACE_FONT, SANS_FONT, INPUT_STYLE,
    TERMINAL_PANEL_STYLE, RADIUS, FACTION_ICONS, BORDER_COLOR
)
from ..ui_utils.factions import faction_icon, get_faction_color
from ..components.icons import ship_icon
from ..backend.utils.xwing_data.pilots import load_all_pilots, get_pilot_info
from ..backend.utils.xwing_data.ships import get_ship_icon_name
from ..backend.utils.xwing_data.upgrades import get_upgrade_name, get_upgrade_slot, get_upgrade_info

from ..components.list_renderer import (
    UpgradeData, PilotData, ListData, 
    pilot_tooltip_content, render_upgrade_icon, 
    render_pilot_block, list_row_card
)

class ListBrowserState(rx.State):
    """State for the List Browser page."""
    
    # --- Global State Access ---
    # We no longer store data_source locally.

    @rx.var
    def lists_found_label(self) -> str:
        return f"{self.total_items_count} LISTS FOUND"

    # --- Filters ---
    
    # Faction Filter
    selected_factions: dict[str, bool] = {}
    faction_options: list[list[str]] = [[f.label, f.value] for f in Faction if f != Faction.UNKNOWN]
    
    # --- Accordion States (Smart Persistence) ---
    faction_acc_val: list[str] = []
    
    def set_faction_acc_val(self, val):
        self.faction_acc_val = val

    async def toggle_faction(self, faction: str, checked: bool):
        new_factions = self.selected_factions.copy()
        new_factions[faction] = checked
        self.selected_factions = new_factions
        self.current_page = 0
        await self.load_lists()

    async def reset_list_filters(self):
        """Reset only list-specific filters."""
        self.selected_factions = {}
        self.points_min = 0
        self.points_max = 50 if (await self.get_state(GlobalFilterState)).data_source == "xwa" else 200
        self.loadout_min = 0
        self.min_games = 0
        self.sort_metric = "Games"
        self.sort_direction = "desc"
        self.current_page = 0
        await self.load_lists()

    async def actual_source_change_logic(self, forced_source: str):
        """Async Logic for content source change."""
        # Use passed source to avoid race conditions with Global State update
        
        # Update Points Max defaults
        if forced_source == "xwa":
             self.points_max = 50
        else: # legacy or other
             self.points_max = 200
             
        self.current_page = 0
        await self.load_lists(override_source=forced_source)

    async def handle_source_change(self, _e=None, **kwargs):
        """Handle content source change: update defaults and reload."""
        # _e is the value from SegmentedControl (str) or Event from Button (dict/obj)
        new_source = _e if isinstance(_e, str) else "xwa"
        
        # 1. Update Global State first
        yield GlobalFilterState.set_data_source(new_source)
        
        # 2. Trigger async actual logic
        yield ListBrowserState.actual_source_change_logic(new_source)

    async def reset_tournament_filters_wrapper(self):
        """Reset only global tournament filters."""
        gs = await self.get_state(GlobalFilterState)
        gs.reset_tournament_filters()
        self.current_page = 0
        await self.load_lists()

    # Sorting
    sort_metric: str = "Games" # Label
    sort_direction: str = "desc" # asc, desc
    
    @rx.var
    def sort_metric_options(self) -> list[str]:
        return ["Games", "Win Rate", "Points Cost", "Total Loadout"]

    min_games: int = 0 
    points_min: int = 0
    points_max: int = 200 # Updated dynamically based on source
    loadout_min: int = 0
    loadout_max: int = 50 # Default max reasonable loadout? 
    
    # Data
    lists_data: list[ListData] = []
    _all_lists_cached: list[ListData] = []
    total_lists: int = 0
    total_items_count: int = 0
    
    # Pagination State (Manual Implementation)
    page_size: int = 20
    current_page: int = 0
    
    @rx.var
    def total_pages(self) -> int:
        return (self.total_items_count + self.page_size - 1) // self.page_size if self.total_items_count > 0 else 1

    @rx.var
    def has_next(self) -> bool:
        return self.current_page < self.total_pages - 1

    @rx.var
    def has_prev(self) -> bool:
        return self.current_page > 0

    def next_page(self):
        if self.has_next:
            self.current_page += 1
            self.update_view()

    def prev_page(self):
        if self.has_prev:
            self.current_page -= 1
            self.update_view()
            
    def jump_to_page(self, val: str):
        try:
            p = int(val)
            idx = p - 1
            if 0 <= idx < self.total_pages:
                self.current_page = idx
                self.update_view()
        except ValueError:
            pass

    def handle_page_submit(self, key: str):
        if key == "Enter":
            self.update_view()

    # --- Actions ---
    async def set_sort_metric(self, metric: str):
        self.sort_metric = metric
        await self.load_lists()

    async def toggle_sort_direction(self):
        self.sort_direction = "asc" if self.sort_direction == "desc" else "desc"
        await self.load_lists()
        
    async def set_min_games(self, val: Any):
        try:
            self.min_games = int(val)
            self.current_page = 0
            await self.load_lists()
        except ValueError:
            pass
            
    async def set_points_min(self, val: Any):
        try:
            self.points_min = int(val)
            self.current_page = 0
            await self.load_lists()
        except ValueError:
            pass

    async def set_points_max(self, val: Any):
        try:
            self.points_max = int(val)
            self.current_page = 0
            await self.load_lists()
        except ValueError:
            pass

    async def set_loadout_min(self, val: Any):
        try:
            val_int = int(val)
            self.loadout_min = val_int
            self.current_page = 0
            await self.load_lists()
        except ValueError:
            pass

    async def set_loadout_max(self, val: Any):
        try:
            val_int = int(val)
            self.loadout_max = val_int
            self.current_page = 0
            await self.load_lists()
        except ValueError:
            pass
            
    async def on_mount(self):
        gs = await self.get_state(GlobalFilterState)
        gs.load_locations()
        
        if not gs.selected_formats:
             gs.set_default_formats_for_source(gs.data_source)
        
        # Force update points max default
        self.points_max = 50 if gs.data_source == "xwa" else 200

        # --- Smart Accordion Logic ---
        # Initialize selected_factions keys to False if empty to prevent UI binding errors
        if not self.selected_factions:
             for f_list in self.faction_options:
                 # f_list is [label, value]
                 self.selected_factions[f_list[1]] = False

        # Faction
        has_faction = any(self.selected_factions.values())
        if has_faction:
            self.faction_acc_val = ["Faction"]
            
        await self.load_lists()

    async def load_lists(self, override_source=None):
        print("DEBUG: Loading Lists...")
        gs = await self.get_state(GlobalFilterState)
        
        # Use override if provided and is string (ignore boolean event args), else global state
        current_source = override_source if isinstance(override_source, str) else gs.data_source
        
        with Session(engine) as session:
            # Prepare filters
            active_factions = [k for k, v in self.selected_factions.items() if v]
            
            allowed_formats = []
            for k, v in gs.selected_formats.items():
                if v: allowed_formats.append(k)

            query = select(PlayerResult, Tournament).where(PlayerResult.tournament_id == Tournament.id)
            
            # 1. Date Filter
            if gs.date_range_start:
                query = query.where(Tournament.date >= gs.date_range_start)
            if gs.date_range_end:
                query = query.where(Tournament.date <= gs.date_range_end)
                
            # 2. Format Filter
            if allowed_formats:
                # Tournament.format is a string column (e.g. "amg", "xwa")
                query = query.where(Tournament.format.in_(allowed_formats))
            
            # 3. Location Filter
            active_continents = [k for k, v in gs.selected_continents.items() if v]
            active_countries = [k for k, v in gs.selected_countries.items() if v]
            
            if active_continents:
                query = query.where(Tournament.continent.in_(active_continents))
            if active_countries:
                query = query.where(Tournament.country.in_(active_countries))
                
            # 4. Faction Filter (Done in Python)
            # if active_factions:
            #     query = query.where(PlayerResult.faction.in_(active_factions))
                
            # 5. Points Filter (Done in Python)
            # query = query.where(PlayerResult.points >= self.points_min)
            # if self.points_max < 200:
            #      query = query.where(PlayerResult.points <= self.points_max)

            # Loadout Filter is purely Python-side as it relies on parsing JSON


            # Execute Query
            # print(f"DEBUG: Executing Query with filters: formats={allowed_formats}, date={gs.date_range_start}-{gs.date_range_end}, pt={self.points_min}-{self.points_max}")
            rows = session.exec(query).all()
            print(f"DEBUG: Query returned {len(rows)} rows.")
            
            # Grouping Logic
            list_signatures = {} # signature -> {faction, points, count, games, wins}
            
            for result, tournament in rows:
                # 2. List Processing
                xws = result.list_json
                if not xws:
                     # print(f"DEBUG: result {result.id} has empty xws", flush=True)
                     continue
                if not isinstance(xws, dict):
                     # print(f"DEBUG: result {result.id} xws is not dict", flush=True)
                     continue
                
                # Check min games filter? No, we filter aggregated results later.
                
                signature = get_list_signature(xws)
                if not signature:
                    # print(f"DEBUG: Could not generate signature for result {result.id}", flush=True)
                    continue
                
                # Filter Faction (Python Side)
                faction_xws = xws.get("faction", "unknown")
                if active_factions and faction_xws not in active_factions:
                    continue

                # Filter Points (Python Side)
                points = xws.get("points", 0)
                if points < self.points_min:
                    continue
                if self.points_max < 200 and points > self.points_max:
                    continue

                if signature not in list_signatures:
                    list_signatures[signature] = {
                        "faction": faction_xws,
                        "points": points,
                        "count": 0,
                        "games": 0,
                        "wins": 0,
                        "win_rate": 0.0,
                        "raw_xws": xws,
                        "total_loadout": 0 # Track loadout for filtering
                    }
                
                stats = list_signatures[signature]
                stats["count"] += 1
                
                # Calculate Loadout (Once per signature is enough usually, but lets check)
                if stats["total_loadout"] == 0 and current_source == "xwa":
                     total_loadout = 0
                     pilots_data = xws.get("pilots", [])
                     for p in pilots_data:
                         pid = p.get("id") or p.get("name")
                         if not pid: continue
                         # We need to fetch pilot info to get base loadout? 
                         # Or is it in the list? Standard XWA lists don't always sum it.
                         # We need to fetch from metadata.
                         p_info = get_pilot_info(pid)
                         if p_info:
                             total_loadout += p_info.get("loadout", 0)
                     stats["total_loadout"] = total_loadout

                # Filter Loadout (Python Side)
                if current_source == "xwa":
                    if self.loadout_min > 0 and stats["total_loadout"] < self.loadout_min:
                        continue
                    if self.loadout_max > 0 and stats["total_loadout"] > self.loadout_max:
                        continue
                
                # Assume aggregated games/wins if available in PlayerResult?
                # For now assume result represents 1 entry.
                games_played = 0
                wins = 0
                if result.swiss_rank and result.swiss_rank > 0:
                    wins += result.swiss_wins if result.swiss_wins >= 0 else 0
                    # Accurate games played calculation
                    games_played += (result.swiss_wins or 0) + (result.swiss_losses or 0) + (result.swiss_draws or 0)
                    if games_played == 0: games_played = 3 # Fallback
                stats["games"] += games_played
                stats["wins"] += wins

            # Process Aggregates
            final_list: list[ListData] = []
            
            for sig, stats in list_signatures.items():
                if stats["games"] < self.min_games:
                    continue
                    
                win_rate = (stats["wins"] / stats["games"] * 100) if stats["games"] > 0 else 0.0
                
                # Build Rich Data
                raw_xws = stats["raw_xws"]
                pilots = raw_xws.get("pilots", [])
                
                rich_pilots = []
                for p in pilots:
                    pid = p.get("id") or p.get("name")
                    pilot_info = get_pilot_info(pid) or {}
                    
                    pilot_name = pilot_info.get("name", pid)
                    ship_xws = pilot_info.get("ship_xws", "")
                    ship_name = pilot_info.get("ship", "Unknown Ship")
                    ship_icon_name = get_ship_icon_name(ship_xws)
                    pilot_image = pilot_info.get("image", "")
                    # Points: Use list-specific points if available
                    pilot_points = p.get("points", pilot_info.get("cost", 0))
                    
                    rich_upgrades = []
                    upgrades_data = p.get("upgrades", {})
                    
                    # Handle upgrades as list or dict
                    if isinstance(upgrades_data, dict):
                        # Standard XWS format: {"slot": ["upgrade_xws", ...]}
                        for slot, items in upgrades_data.items():
                            if not isinstance(items, list): continue
                            for item_id in items:
                                upg_info = get_upgrade_info(item_id) or {}
                                norm_slot = slot.lower()
                                if norm_slot == "configuration": norm_slot = "config"
                                rich_upgrades.append(UpgradeData(
                                    name=upg_info.get("name", item_id),
                                    xws=item_id,
                                    slot=norm_slot,
                                    slot_icon="",
                                    image=upg_info.get("image", ""),
                                    points=upg_info.get("cost", {}).get("value", 0)
                                ))
                    elif isinstance(upgrades_data, list):
                         # Legacy/Simple format: ["upgrade_xws", ...]
                         for item_id in upgrades_data:
                                upg_info = get_upgrade_info(item_id) or {}
                                slot = get_upgrade_slot(item_id)
                                norm_slot = slot.lower()
                                if norm_slot == "configuration": norm_slot = "config"
                                rich_upgrades.append(UpgradeData(
                                    name=upg_info.get("name", item_id),
                                    xws=item_id,
                                    slot=norm_slot,
                                    slot_icon="",
                                    image=upg_info.get("image", ""),
                                    points=upg_info.get("cost", {}).get("value", 0)
                                ))
                    
                    rich_pilots.append(PilotData(
                        name=pilot_name,
                        xws=pid,
                        ship_name=ship_name,
                        ship_icon=ship_icon_name,
                        image=pilot_image,
                        points=pilot_points,
                        loadout=pilot_info.get("loadout", 0),
                        upgrades=rich_upgrades
                    ))
                
                final_list.append(ListData(
                    signature=sig,
                    faction=Faction.from_xws(stats["faction"]).label,
                    faction_key=stats["faction"],
                    points=stats["points"],
                    count=stats["count"],
                    games=stats["games"],
                    win_rate=round(win_rate, 1),
                    total_loadout=stats["total_loadout"],
                    pilots=rich_pilots
                ))
            
            # Sort
            reverse = self.sort_direction == "desc"
            
            if self.sort_metric == "Win Rate":
                final_list.sort(key=lambda x: x.win_rate, reverse=reverse)
            elif self.sort_metric == "Points Cost":
                final_list.sort(key=lambda x: x.points, reverse=reverse)
            elif self.sort_metric == "Total Loadout":
                 pass
            else: # Games (Default)
                final_list.sort(key=lambda x: x.games, reverse=reverse)
                
            # If Sort Metric is Loadout, handle manual sort 
            if self.sort_metric == "Total Loadout":
                 final_list.sort(key=lambda x: sum(p.loadout for p in x.pilots), reverse=reverse)
                
            self._all_lists_cached = final_list
            self.total_items_count = len(final_list)
            self.current_page = 0
            self.update_view()

    def update_view(self):
        start = self.current_page * self.page_size
        end = start + self.page_size
        self.lists_data = self._all_lists_cached[start:end]

def render_filters_sidebar() -> rx.Component:
    return rx.vstack(
        # 1. Game Content Source
        rx.box(
            content_source_filter(ListBrowserState.handle_source_change),
            width="100%"
        ),
        
        rx.divider(border_color=BORDER_COLOR),
        
        # 2. Tournament Filters (Date, Location, Format)
        tournament_filters(
            on_change=ListBrowserState.load_lists,
            reset_handler=ListBrowserState.reset_tournament_filters_wrapper
        ),
        
        rx.divider(border_color=BORDER_COLOR),
        
        # 3. List Filters Header
        rx.hstack(
            rx.text("LIST FILTERS", size="2", weight="bold", letter_spacing="1px", color=TEXT_PRIMARY),
            rx.spacer(),
            rx.icon_button(
                rx.icon(tag="rotate-ccw"),
                on_click=ListBrowserState.reset_list_filters,
                variable="ghost",
                color_scheme="gray",
                size="1",
                tooltip="Reset List Filters"
            ),
            width="100%",
            align_items="center"
        ),
        
        # Sort By (Dropdown + Toggle)
        rx.vstack(
            rx.text("Sort By", size="1", weight="bold", color=TEXT_SECONDARY),
            rx.hstack(
                rx.select(
                    ListBrowserState.sort_metric_options,
                    value=ListBrowserState.sort_metric,
                    on_change=ListBrowserState.set_sort_metric,
                    flex="1",
                    style=INPUT_STYLE
                ),
                rx.button(
                    rx.icon(tag=rx.cond(ListBrowserState.sort_direction == "desc", "arrow-down-wide-narrow", "arrow-up-narrow-wide")),
                    on_click=ListBrowserState.toggle_sort_direction,
                    variant="surface",
                    color_scheme="gray",
                    width="40px",
                    flex_shrink="0"
                ),
                width="100%",
                spacing="2",
                align_items="center"
            ),
            spacing="1",
            width="100%"
        ),
        
        # Faction Filter (Shared Component)
        filter_accordion(
            "Faction",
            ListBrowserState.faction_options,
            ListBrowserState.selected_factions,
            ListBrowserState.toggle_faction,
            accordion_value=ListBrowserState.faction_acc_val,
            on_accordion_change=ListBrowserState.set_faction_acc_val,
        ),
        
        # Min Games
        rx.vstack(
            rx.text("Min Games", size="1", weight="bold", color=TEXT_SECONDARY),
            rx.input(
                type="number",
                value=ListBrowserState.min_games,
                on_change=ListBrowserState.set_min_games,
                min="0",
                style=INPUT_STYLE,
                width="100%"
            ),
            spacing="1",
            width="100%"
        ),
        
        # Points Filter (Range)
        rx.vstack(
            rx.text("Points Cost", size="1", weight="bold", color=TEXT_SECONDARY),
            rx.hstack(
                rx.input(
                    type="number",
                    value=ListBrowserState.points_min,
                    on_change=ListBrowserState.set_points_min,
                    # Dynamic Max based on source
                    min="0", 
                    max=rx.cond(GlobalFilterState.data_source == "xwa", "50", "200"),
                    style=INPUT_STYLE,
                    width="100%"
                ),
                rx.text("-", color=TEXT_SECONDARY),
                rx.input(
                    type="number",
                    value=ListBrowserState.points_max,
                    on_change=ListBrowserState.set_points_max,
                    min="0",
                    max=rx.cond(GlobalFilterState.data_source == "xwa", "50", "200"),
                    style=INPUT_STYLE,
                    width="100%"
                ),
                spacing="2",
                align="center",
                width="100%"
            ),
            spacing="1",
            width="100%"
        ),
        
        # Loadout Value Filter (XWA Only)
        rx.cond(
            GlobalFilterState.data_source == "xwa",
            rx.vstack(
                rx.text("Total Loadout", size="1", weight="bold", color=TEXT_SECONDARY),
                rx.hstack(
                    rx.input(
                        type="number",
                        value=ListBrowserState.loadout_min,
                        on_change=ListBrowserState.set_loadout_min,
                        min="0",
                        style=INPUT_STYLE,
                        width="100%"
                    ),
                    rx.text("-", color=TEXT_SECONDARY),
                    rx.input(
                        type="number",
                        value=ListBrowserState.loadout_max,
                        on_change=ListBrowserState.set_loadout_max,
                        min="0",
                        style=INPUT_STYLE,
                        width="100%"
                    ),
                    spacing="2",
                    align="center",
                    width="100%"
                ),
                spacing="1",
                width="100%"
            )
        ),
        
        spacing="4",
        width="100%",
        align_items="start"
    )

def pagination_controls_lists() -> rx.Component:
    return pagination_controls(ListBrowserState)

def list_browser() -> rx.Component:
    return layout(
        dashboard_layout(
            render_filters_sidebar(),
            rx.vstack(
                rx.heading("List Browser", size="6", font_family=SANS_FONT, weight="bold", color=TEXT_PRIMARY),
                rx.divider(border_color=BORDER_COLOR),
                
                rx.flex(
                    rx.text(ListBrowserState.lists_found_label, size="2", color=TEXT_SECONDARY, font_family=MONOSPACE_FONT),
                    rx.spacer(),
                    width="100%", 
                    justify="between", 
                    align="center",
                    margin_y="16px"
                ),
                
                rx.mobile_only(
                     rx.box(render_filters_sidebar(), width="100%", margin_bottom="16px")
                ),
                
                rx.vstack(
                    rx.foreach(ListBrowserState.lists_data, list_row_card),
                    width="100%",
                    spacing="2"
                ),
                
                rx.hstack(rx.spacer(), pagination_controls_lists(), width="100%", margin_top="24px"),
                
                width="100%",
                min_height="100vh",
            )
        )
    )
