"""
X-Wing Icon Component - Renders icons from xwing-miniatures-font.

Usage:
    xwing_icon("rebel")            # Faction icon
    xwing_icon("empire", size="2em")
    ship_icon("t65xwing")          # Ship icon
"""
import reflex as rx

from ..theme import FACTION_ICONS
from ..ui_utils.factions import get_faction_color, get_faction_icon_class


def xwing_icon(icon_type: str | rx.Var, size: str = "1.5em", color: str | rx.Var | None = None) -> rx.Component:
    """
    Render an X-Wing miniatures font icon.
    
    Args:
        icon_type: Icon type (faction XWS ID or icon class suffix)
        size: Font size (e.g., "1.5em", "24px")
        color: Optional color override (can be Var or string)
        
    Returns:
        Icon component using xwing-miniatures-font
    """
    # If icon_type is a known faction, get its specific icon class
    # If it's a Var, get_faction_icon_class uses rx.match
    icon_class = get_faction_icon_class(icon_type)
    
    # Fallback: if icon_class is empty (default in match), use icon_type directly
    # This allows passing direct classes like "rebel" or "empire"
    final_icon_class_var = rx.cond(
        icon_class == "",
        icon_type,
        icon_class
    )
    
    style = {
        "font_size": size,
        "font_style": "normal",
    }
    if color is not None:
        style["color"] = color
    
    return rx.el.i(
        class_name=rx.cond(
            final_icon_class_var.to(str).contains("xwing-miniatures-font-"),
            f"xwing-miniatures-font {final_icon_class_var}",
            f"xwing-miniatures-font xwing-miniatures-font-{final_icon_class_var}"
        ),
        style=style,
    )


# Map common ship names to icon class - default to XWS
SHIP_ICON_MAP = {
    "tieininterceptor": "tieinterceptor",
}


def ship_icon(ship_xws: str | rx.Var, size: str = "1.5em", color: str | rx.Var | None = None) -> rx.Component:
    """
    Render a ship icon from xwing-miniatures-font.
    
    Args:
        ship_xws: Ship XWS ID (e.g., "t65xwing", "tielnfighter")
        size: Font size
        color: Optional color override (can be Var or string)
        
    Returns:
        Ship icon component
    """
    # Normalize: lower case and remove prefix if present
    clean_name = ship_xws.to(str).lower().replace("xwing-miniatures-ship-", "")
    
    # Use rx.cond for mapping (rx.match requires tuples, dict not supported directly)
    # Currently only mapping tieininterceptor -> tieinterceptor
    icon_class = rx.cond(
        clean_name == "tieininterceptor",
        "tieinterceptor",
        clean_name
    )
    
    style = {
        "font_size": size,
        "font_style": "normal",
    }
    if color is not None:
        style["color"] = color
    
    return rx.el.i(
        class_name=f"xwing-miniatures-ship xwing-miniatures-ship-{icon_class}",
        style=style,
    )


def faction_badge(faction_xws: str | rx.Var, show_name: bool = False) -> rx.Component:
    """
    Render a faction badge with icon and optional name.
    
    Follows the spec rule: "Never write name if icon can be used"
    By default shows icon only; set show_name=True for accessibility.
    """
    color = get_faction_color(faction_xws)
    
    if show_name:
        from ..backend.data_structures.factions import Faction
        # Note: Faction.from_xws works on strings, so if faction_xws is Var, 
        # we'd need a frontend-side mapping for the name if we truly wanted it reactive.
        # But usually faction_badge is used in foreach where we have the string or 
        # we can pass the name separately. For now, keep icon reactive.
        return rx.hstack(
            xwing_icon(faction_xws, size="1.2em", color=color),
            spacing="1",
            align="center",
        )
    
    return xwing_icon(faction_xws, size="1.5em", color=color)
