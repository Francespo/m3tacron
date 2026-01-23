"""
Faction UI Utilities.
Contains visual helpers for faction colors and icons.
"""
import reflex as rx
from ..theme import FACTION_COLORS, FACTION_ICONS, TEXT_SECONDARY

def get_faction_color(faction_xws: rx.Var | str) -> rx.Var:
    """Get color for a faction ID, supporting both Var and string."""
    return rx.match(
        faction_xws,
        *[ (k, v) for k, v in FACTION_COLORS.items() ],
        TEXT_SECONDARY
    )

def get_faction_icon(faction_xws: rx.Var | str) -> rx.Var:
    """Get icon class for a faction ID, supporting both Var and string."""
    return rx.match(
        faction_xws,
        *[ (k, v) for k, v in FACTION_ICONS.items() ],
        ""
    )
