"""
Faction UI Utilities.
Contains visual helpers for faction colors and icons.
"""
import reflex as rx
from ..theme import FACTION_COLORS, FACTION_ICONS, TEXT_SECONDARY

# Mapping from XWS (lowercase) to X-Wing Font Character
# Based on xwing-miniatures.css
FACTION_CHARS = {
    "rebelalliance": "!",
    "galacticempire": "@",
    "scumandvillainy": "#",
    "resistance": "!", # Reuse Rebel for now as per theme.py
    "firstorder": "+",
    "galacticrepublic": "/",
    "separatistalliance": ".",
    "unknown": "?"
}

def get_faction_color(faction_xws: rx.Var | str) -> rx.Var:
    """Get color for a faction ID, supporting both Var and string."""
    return rx.match(
        faction_xws,
        *[ (k, v) for k, v in FACTION_COLORS.items() ],
        TEXT_SECONDARY
    )

def get_faction_icon_class(faction_xws: rx.Var | str) -> rx.Var:
    """Get icon class suffix for a faction ID."""
    return rx.match(
        faction_xws,
        *[ (k, v) for k, v in FACTION_ICONS.items() ],
        ""
    )

def get_faction_char(faction_xws: str) -> str:
    """Get the single-character icon code for a faction."""
    return FACTION_CHARS.get(faction_xws, "?")

def faction_icon(faction_xws: rx.Var | str, size: str = "24px") -> rx.Component:
    """Render a unified faction icon from the X-Wing font."""
    icon_cls = get_faction_icon_class(faction_xws)
    color = get_faction_color(faction_xws)
    
    return rx.cond(
        icon_cls != "",
        rx.html(
            rx.match(
                icon_cls,
                # Special cases if any, otherwise standard mapping
                *[ (v, f"<i class='xwing-miniatures-font {v}'></i>") for v in FACTION_ICONS.values() ],
                ""
            ),
            font_size=size,
            color=color
        ),
        rx.fragment()
    )
