"""
Content Source Filter Component.
"""
import reflex as rx
from ..theme import TEXT_PRIMARY, BORDER_COLOR
from ..backend.data_structures.data_source import DataSource

class ContentSourceState:
    """
    Mixin for managing content source state.
    """
    data_source: str = "xwa" # xwa, legacy
    include_epic: bool = False

    def set_data_source(self, *args):
        source = args[0]
        if isinstance(source, list):
            source = source[0]
        self.data_source = source
        self.on_content_source_change()

    def set_include_epic(self, val: bool):
        self.include_epic = val
        self.on_content_source_change()

    def on_content_source_change(self):
        """Hook for sub-classes to handle changes."""
        pass

def content_source_filter(state: any) -> rx.Component:
    """
    Render Content Source and Epic Toggle.
    """
    return rx.vstack(
        rx.text("GAME CONTENT SOURCE", size="2", weight="bold", letter_spacing="1px", color=TEXT_PRIMARY),
        rx.segmented_control.root(
            rx.segmented_control.item("XWA", value="xwa"),
            rx.segmented_control.item("Legacy", value="legacy"),
            value=state.data_source,
            on_change=state.set_data_source,
            width="100%",
            color_scheme="gray",
        ),
        
        # Include Epic Content Checkbox
        rx.checkbox(
            "Include Epic Content",
            checked=state.include_epic,
            on_change=state.set_include_epic,
            color_scheme="gray"
        ),
        
        spacing="1",
        width="100%"
    )
