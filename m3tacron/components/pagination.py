"""
Pagination UI Component.
"""
import reflex as rx
from ..theme import TEXT_PRIMARY, TEXT_SECONDARY, MONOSPACE_FONT, BORDER_COLOR

def pagination_controls(state: any) -> rx.Component:
    """
    Reusable pagination controls component.
    
    Args:
        state: The state class (should inherit from PaginationMixin).
    """
    return rx.hstack(
        rx.text(
            (state.current_page + 1).to_string() + " / " + state.total_pages.to_string(),
            size="2",
            color=TEXT_SECONDARY,
            font_family=MONOSPACE_FONT
        ),
        rx.spacer(),
        rx.button(
            "< PREV",
            variant="ghost",
            size="1",
            on_click=state.prev_page,
            disabled=~state.has_prev,
            style={"color": TEXT_PRIMARY, "font_family": MONOSPACE_FONT}
        ),
        rx.button(
            "NEXT >",
            variant="ghost",
            size="1",
            on_click=state.next_page,
            disabled=~state.has_next,
            style={"color": TEXT_PRIMARY, "font_family": MONOSPACE_FONT}
        ),
        width="100%",
        padding_top="16px",
        border_top=f"1px solid {BORDER_COLOR}"
    )
