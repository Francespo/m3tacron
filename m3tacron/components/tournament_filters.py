"""
Tournament Filters Component.
Combines Date Range, Location, and Format filters.
"""
import reflex as rx
from ..theme import TEXT_PRIMARY, TEXT_SECONDARY, BORDER_COLOR, INPUT_STYLE, RADIUS
from ..components.format_filter import hierarchical_format_filter
from ..components.location_filter import location_filter
from ..backend.state.global_filter_state import GlobalFilterState

def tournament_filters(on_change: any, reset_handler: list | None = None) -> rx.Component:
    """
    Render the reusable tournament filters section.
    Includes Header, Date Range, Location, and Format.
    
    Args:
        on_change: Event handler to trigger when filters change.
        reset_handler: Optional custom handler for the reset button. 
                       Defaults to [GlobalFilterState.reset_filters, on_change].
    """
    if reset_handler is None:
        reset_handler = [GlobalFilterState.reset_filters, on_change]

    return rx.vstack(
        rx.hstack(
            rx.text("TOURNAMENT FILTERS", size="2", weight="bold", letter_spacing="1px", color=TEXT_PRIMARY),
            rx.spacer(),
            rx.icon_button(
                rx.icon(tag="rotate-ccw"),
                on_click=reset_handler,
                variable="ghost",
                color_scheme="gray",
                size="1",
                tooltip="Reset Filters"
            ),
            width="100%",
            align_items="center"
        ),
        
        # Filters inside an Accordion
        rx.accordion.root(
            # Date Range
            rx.accordion.item(
                rx.accordion.header(
                    rx.accordion.trigger(
                        rx.text("Date Range", size="1", weight="bold", color=TEXT_SECONDARY),
                        rx.accordion.icon(),
                        align_items="center", display="flex", justify_content="space-between", width="100%", padding_y="8px", padding_x="0px", _hover={"background": "transparent", "opacity": 0.8},
                    )
                ),
                rx.accordion.content(
                    rx.vstack(
                        rx.input(
                            type="date",
                            value=GlobalFilterState.date_range_start,
                            on_change=[GlobalFilterState.set_date_start, on_change],
                            style=INPUT_STYLE,
                            width="100%"
                        ),
                        rx.text("to", size="1", color=TEXT_SECONDARY, text_align="center"),
                        rx.input(
                            type="date",
                            value=GlobalFilterState.date_range_end,
                            on_change=[GlobalFilterState.set_date_end, on_change],
                            style=INPUT_STYLE,
                            width="100%"
                        ),
                        spacing="1",
                        width="100%",
                        padding="8px",
                        border=f"1px solid {BORDER_COLOR}",
                        border_radius=RADIUS
                    ),
                    padding_left="8px", padding_top="0px"
                ),
                value="date_range",
                style={"background": "transparent", "border": "none", "_hover": {"background": "transparent"}}
            ),
            # Location Filter
            rx.accordion.item(
                rx.accordion.header(
                    rx.accordion.trigger(
                        rx.text("Location", size="1", weight="bold", color=TEXT_SECONDARY),
                        rx.accordion.icon(),
                        align_items="center", display="flex", justify_content="space-between", width="100%", padding_y="8px", padding_x="0px", _hover={"background": "transparent", "opacity": 0.8},
                    )
                ),
                rx.accordion.content(
                    rx.box(location_filter(GlobalFilterState, on_change=on_change), width="100%"),
                    padding_left="8px", padding_top="0px"
                ),
                value="location",
                style={"background": "transparent", "border": "none", "_hover": {"background": "transparent"}}
            ),
            # Format Filter
            rx.accordion.item(
                rx.accordion.header(
                    rx.accordion.trigger(
                        rx.text("Format", size="1", weight="bold", color=TEXT_SECONDARY),
                        rx.accordion.icon(),
                        align_items="center", display="flex", justify_content="space-between", width="100%", padding_y="8px", padding_x="0px", _hover={"background": "transparent", "opacity": 0.8},
                    )
                ),
                rx.accordion.content(
                    rx.box(hierarchical_format_filter(GlobalFilterState, on_change=on_change), width="100%"),
                    padding_left="8px", padding_top="0px"
                ),
                value="format",
                style={"background": "transparent", "border": "none", "_hover": {"background": "transparent"}}
            ),
            type="multiple",
            collapsible=True,
            width="100%",
            color_scheme="gray",
            variant="ghost",
        ),
        
        spacing="4",
        width="100%"
    )
