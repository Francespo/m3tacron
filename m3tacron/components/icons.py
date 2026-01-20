"""
X-Wing Icon Component - Renders icons from xwing-miniatures-font.

Usage:
    xwing_icon("rebel")            # Faction icon
    xwing_icon("empire", size="2em")
    ship_icon("t65xwing")          # Ship icon
"""
import reflex as rx

from ..theme import FACTION_ICONS


def xwing_icon(icon_type: str, size: str = "1.5em", color: str | None = None) -> rx.Component:
    """
    Render an X-Wing miniatures font icon.
    
    Args:
        icon_type: Icon type (faction XWS ID or icon class suffix)
        size: Font size (e.g., "1.5em", "24px")
        color: Optional color override
        
    Returns:
        Icon component using xwing-miniatures-font
    """
    # If icon_type is a Reflex Var, we must assume it's already the correct class
    # or handle it differently, as we can't look it up in a Python dict.
    if isinstance(icon_type, rx.Var):
        icon_class = icon_type
    else:
        # Map faction XWS to icon class if needed
        icon_class = FACTION_ICONS.get(icon_type.lower(), icon_type)
    
    style = {
        "font_size": size,
        "font_style": "normal",
    }
    if color is not None:
        style["color"] = color
    
    if isinstance(icon_class, rx.Var):
        # Reflex Logic
        return rx.el.i(
            class_name=rx.cond(
                icon_class.to(str).contains("xwing-miniatures-font-"),
                f"xwing-miniatures-font {icon_class}",
                f"xwing-miniatures-font xwing-miniatures-font-{icon_class}"
            ),
            style=style,
        )
    else:
        # Python Logic
        final_class = f"xwing-miniatures-font {icon_class}" if "xwing-miniatures-font-" in icon_class else f"xwing-miniatures-font xwing-miniatures-font-{icon_class}"
        return rx.el.i(
            class_name=final_class,
            style=style,
        )


def ship_icon(ship_xws: str, size: str = "1.5em", color: str | None = None) -> rx.Component:
    """
    Render a ship icon from xwing-miniatures-font.
    
    Args:
        ship_xws: Ship XWS ID (e.g., "t65xwing", "tielnfighter")
        size: Font size
        color: Optional color override
        
    Returns:
        Ship icon component
    """
    # Map common ship names to icon class - default to XWS
    if isinstance(ship_xws, rx.Var):
        icon_class = ship_xws.to(str).lower()
    else:
        icon_class = ship_xws.lower()
    
    
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


def faction_badge(faction_xws: str, show_name: bool = False) -> rx.Component:
    """
    Render a faction badge with icon and optional name.
    
    Follows the spec rule: "Never write name if icon can be used"
    By default shows icon only; set show_name=True for accessibility.
    """
    from ..theme import FACTION_COLORS
    
    color = FACTION_COLORS.get(faction_xws.lower(), "#8a8a9a")
    
    if show_name:
        from ..backend.enums.factions import Faction
        name = Faction.from_xws(faction_xws).label
        return rx.hstack(
            xwing_icon(faction_xws, size="1.2em", color=color),
            rx.text(name, size="2", color=color),
            spacing="1",
            align="center",
        )
    
    return xwing_icon(faction_xws, size="1.5em", color=color)
