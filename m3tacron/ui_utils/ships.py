"""
Ship UI Utilities.
"""
import reflex as rx
from ..components.icons import ship_icon
from ..theme import MONOSPACE_FONT

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

def get_ship_icon_name(xws_id: str) -> str:
    """Get the correct icon name for a given ship XWS ID."""
    return SHIP_ICON_OVERRIDES.get(xws_id, xws_id)

def render_ship_icon_group(ship: dict) -> rx.Component:
    """
    Render a group of ship icons for a single chassis (e.g. 3x X-Wing).
    ship: {"name": str, "count": int, "icon": str, "color": str}
    """
    return rx.tooltip(
        rx.hstack(
            rx.cond(
                ship["count"].to(int) > 1,
                rx.text(f"{ship['count']}x", size="1", color=ship["color"], font_family=MONOSPACE_FONT, weight="bold"),
                rx.fragment()
            ),
            ship_icon(ship["icon"], size="1.6em", color=ship["color"]),
            spacing="1",
            align_items="center",
            style={"cursor": "help"}
        ),
        content=ship["name"]
    )
