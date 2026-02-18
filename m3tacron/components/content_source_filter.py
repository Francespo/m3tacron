"""
Content Source Filter Component.
"""
import reflex as rx
from ..theme import TEXT_PRIMARY, BORDER_COLOR
from ..backend.state.global_filter_state import GlobalFilterState

def content_source_filter(on_change: any) -> rx.Component:
    """
    Render Content Source and Epic Toggle.
    Args:
        on_change: Event handler to trigger when filters change (e.g. State.load_data)
    """
    return rx.vstack(
        rx.hstack(
            rx.text("GAME CONTENT SOURCE", size="2", weight="bold", letter_spacing="1px", color=TEXT_PRIMARY),
            width="100%",
            align_items="center"
        ),
        
        rx.segmented_control.root(
            rx.segmented_control.item("XWA", value="xwa"),
            rx.segmented_control.item("Legacy", value="legacy"),
            value=GlobalFilterState.data_source,
            on_change=[GlobalFilterState.set_data_source, on_change],
            width="100%",
            color_scheme="gray",
        ),
        
        # Include Epic Content Checkbox
        rx.checkbox(
            "Include Epic Content",
            checked=GlobalFilterState.include_epic,
            on_change=[GlobalFilterState.set_include_epic, on_change],
            color_scheme="gray"
        ),
        
        spacing="1",
        width="100%"
    )
