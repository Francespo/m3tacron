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
        rx.hstack(
            rx.text("Page", color=TEXT_SECONDARY, size="2", font_family=MONOSPACE_FONT),
            rx.input(
                value=(state.current_page + 1).to_string(),
                on_change=state.jump_to_page,
                width="50px",
                size="1",
                style={"text_align": "center", "font_family": MONOSPACE_FONT},
                on_key_down=state.handle_page_submit,
                debounce_timeout=600  # Debounce to avoid jumping while typing
            ),
            rx.text("of", state.total_pages, color=TEXT_SECONDARY, size="2", font_family=MONOSPACE_FONT),
            spacing="2",
            align="center"
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
