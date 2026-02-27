
import reflex as rx
from ..theme import (
    TEXT_PRIMARY, TEXT_SECONDARY, MONOSPACE_FONT, SANS_FONT, 
    TERMINAL_PANEL_STYLE, RADIUS, BORDER_COLOR
)
from ..ui_utils.factions import faction_icon, get_faction_color
from ..components.icons import ship_icon, xwing_icon
from ..backend.state.global_filter_state import GlobalFilterState
from ..backend.utils.xwing_data.pilots import get_pilot_info
from ..backend.utils.xwing_data.ships import get_ship_icon_name
from ..backend.utils.xwing_data.upgrades import get_upgrade_info, get_upgrade_slot
from ..backend.data_structures.factions import Faction

# Data Models
class UpgradeData(rx.Base):
    name: str = ""
    xws: str = ""
    slot: str = ""
    slot_icon: str = ""
    image: str = ""
    points: int = 0

class PilotData(rx.Base):
    name: str = ""
    xws: str = ""
    ship_name: str = ""
    ship_icon: str = ""
    image: str = ""
    points: int = 0
    loadout: int = 0
    upgrades: list[UpgradeData] = []

class ListData(rx.Base):
    signature: str = ""
    faction: str = ""
    faction_key: str = ""
    points: int = 0
    count: int = 0
    games: int = 0
    win_rate: float = 0.0
    total_loadout: int = 0
    pilots: list[PilotData] = []

def enrich_list_data(stats: dict) -> ListData:
    """
    Converts a raw list stats dictionary (from aggregate_list_stats) into a ListData object.
    """
    pilots = stats.get("pilots", [])
    rich_pilots = []
    
    total_loadout = 0
    
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
        pilot_loadout = pilot_info.get("loadout", 0)
        total_loadout += pilot_loadout
        
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
            loadout=pilot_loadout,
            upgrades=rich_upgrades
        ))
    
    # Return ListData
    # Note: stats['faction'] might be xws key or label, aggregation returns xws key usually?
    # aggregate_list_stats returns xws key in 'faction' field.
    f_key = stats.get("faction", "unknown")
    try:
        f_label = Faction.from_xws(f_key).label
    except:
        f_label = f_key.title()

    return ListData(
        signature=stats.get("name", "Unknown List"), # We use name as signature/ID for display? Or stats don't have sig?
        # aggregate_list_stats returns "name" which is the list name or "Untitled..."
        faction=f_label,
        faction_key=f_key,
        points=stats.get("points", 0),
        count=stats.get("popularity", 0),
        games=stats.get("games", 0),
        win_rate=stats.get("win_rate", 0.0),
        total_loadout=total_loadout,
        pilots=rich_pilots
    )

def pilot_tooltip_content(pilot: PilotData) -> rx.Component:
    """Tooltip content for a pilot."""
    return pilot.name + " (" + pilot.ship_name + ")"

def render_upgrade_icon(upgrade: UpgradeData) -> rx.Component:
    return rx.hover_card.root(
        rx.hover_card.trigger(
            rx.box(
                rx.hstack(
                    xwing_icon(upgrade.slot, size="14px", margin_top="-1px"),
                    rx.text(f"{upgrade.name} ({upgrade.points})", size="1"),
                    padding_x="4px",
                    padding_y="2px",
                    border=f"1px solid {BORDER_COLOR}",
                    border_radius="4px",
                    bg="rgba(0,0,0,0.3)",
                    spacing="1",
                    align="center"
                ),
                cursor="pointer",
            )
        ),
        rx.hover_card.content(
            rx.cond(
                upgrade.image,
                rx.image(src=upgrade.image, width="300px", height="auto"),
                rx.text(upgrade.name)
            )
        )
    )

def render_pilot_block(pilot: PilotData) -> rx.Component:
    return rx.box(
        rx.vstack(
            # Top: Pilot (Clickable) + Name Tooltip
            rx.hstack(
                 rx.text(ship_icon(pilot.ship_icon), font_family="xwing-miniatures-ship", font_size="2em"),
                 rx.vstack(
                     # Tooltip ONLY on name
                     rx.hover_card.root(
                        rx.hover_card.trigger(
                            rx.text(pilot.name, size="3", weight="bold"),
                        ),
                        rx.hover_card.content(
                            rx.cond(
                                pilot.image,
                                rx.image(src=pilot.image, width="300px", height="auto"),
                                rx.text(pilot.name)
                            )
                        )
                     ),
                     rx.hstack(
                         rx.text(f"{pilot.points} pts", size="1", color=TEXT_SECONDARY),
                         rx.cond(
                             GlobalFilterState.data_source == "xwa",
                             rx.cond(
                                 pilot.loadout > 0,
                                 rx.text(f"LV: {pilot.loadout}", size="1", color=TEXT_SECONDARY),
                             )
                         ),
                         spacing="1",
                         align="center"
                     ),
                     spacing="0"
                 ),
                 spacing="2",
                 align="center",
                 width="100%",
                 cursor="pointer",
                 on_click=rx.redirect(f"/cards?pilot={pilot.xws}") # Redirect to card browser filter
            ),
            
            # Upgrades
            rx.flex(
                rx.foreach(
                    pilot.upgrades,
                    render_upgrade_icon
                ),
                wrap="wrap",
                spacing="1",
                width="100%"
            ),
            
            spacing="2",
            padding="8px",
            width="100%",
            bg="rgba(255,255,255,0.03)",
            border_radius="8px"
        ),
        width="100%", # Take full width of grid cell
        min_width={"initial": "100%", "md": "300px"}, # Responsive min-width
    )

def list_row_card(list_data: ListData) -> rx.Component:
    """
    Renders a single row for a list.
    """
    faction = list_data.faction_key
    faction_color = get_faction_color(faction)
    
    return rx.box(
        rx.hstack(
            # Faction Strip
            rx.box(
                width="6px", 
                min_height="100px", 
                bg=faction_color,
                align_self="stretch", # Force stretch to full height
                flex_shrink=0 # Prevent shrinking
            ),
            
            # Content
            rx.vstack(
                # Header: Faction Icon + Stats
                rx.flex(
                    faction_icon(faction, size="1.5em"),
                    rx.spacer(),
                    # Stats
                    rx.flex(
                        rx.badge(f"{list_data.points} pts", variant="solid", color_scheme="gray"),
                        rx.badge(f"{list_data.win_rate}% WR", variant="surface", 
                                 color_scheme=rx.cond(list_data.win_rate >= 50, "green", "orange")),
                        rx.cond(
                            GlobalFilterState.data_source == "xwa",
                            rx.badge(f"LV: {list_data.total_loadout}", variant="outline", color_scheme="violet")
                        ),
                        rx.text(f"{list_data.games} games", size="1", color=TEXT_SECONDARY, font_family=MONOSPACE_FONT),
                        spacing="2",
                        align="center",
                        wrap="wrap",
                        justify="end",
                    ),
                    width="100%",
                    align="center",
                    margin_bottom="4px",
                    wrap="wrap",
                    gap="2",
                ),
                
                # Ships Row - Use Grid or Flex
                rx.flex(
                    rx.foreach(
                        list_data.pilots,
                        render_pilot_block
                    ),
                    wrap="wrap",
                    spacing="2",
                    width="100%"
                ),
                
                width="100%",
                spacing="3",
                padding="12px"
            ),
            width="100%",
            align="stretch", # Ensure faction bar stretches
            spacing="0"
        ),
        bg=TERMINAL_PANEL_STYLE["background"],
        border=f"1px solid {BORDER_COLOR}",
        border_radius=RADIUS,
        overflow="hidden",
        width="100%", # Ensure card takes full width
        _hover={"border_color": TEXT_SECONDARY}
    )
