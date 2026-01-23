import reflex as rx
from ..theme import TEXT_PRIMARY, TEXT_SECONDARY, BORDER_COLOR, MONOSPACE_FONT, INPUT_STYLE

def checkbox_row(label: str, value: str, state_map: rx.Var, on_toggle: callable) -> rx.Component:
    """A minimal transparent checkbox row."""
    # This duplicates functionality from filter_accordion but logic might differ if we need id mapping
    return rx.hstack(
        rx.checkbox(
            checked=state_map[value],
            on_change=lambda c: on_toggle(value, c),
            color_scheme="gray",
            size="1",
        ),
        rx.text(
            label, 
            size="1", 
            color=TEXT_PRIMARY, 
            font_family=MONOSPACE_FONT,
            on_click=lambda: on_toggle(value, ~state_map[value]),
            cursor="pointer",
            _hover={"opacity": 0.8}
        ),
        spacing="2",
        align="center",
        width="100%",
        padding_y="2px"
    )

def searchable_filter_accordion(
    label: str,
    options: rx.Var[list[list[str]]], # List of [label, value]
    state_map: rx.Var,  # Dict[str, bool]
    on_toggle: callable, # Function(value, checked)
    search_text: rx.Var, # State var for search
    set_search_text: callable, # Setter for search
) -> rx.Component:
    """
    A transparent accordion with an internal search bar.
    """
    return rx.accordion.root(
        rx.accordion.item(
            header=rx.text(
                label, 
                size="1", 
                weight="bold", 
                color=TEXT_SECONDARY, 
                font_family=MONOSPACE_FONT, 
                letter_spacing="1px"
            ),
            content=rx.vstack(
                # Search Bar
                rx.input(
                    placeholder="Search...",
                    value=search_text,
                    on_change=set_search_text,
                    size="1",
                    style={**INPUT_STYLE, "border": "none", "border_bottom": f"1px solid {BORDER_COLOR}", "border_radius": "0"},
                    width="100%",
                    margin_bottom="8px"
                ),
                # Options List
                rx.scroll_area(
                    rx.vstack(
                        rx.foreach(
                            options,
                            lambda opt: checkbox_row(opt[0], opt[1], state_map, on_toggle)
                        ),
                        spacing="1",
                        width="100%"
                    ),
                    max_height="200px",
                    type="always",
                    scrollbars="vertical",
                    style={"padding_right": "10px"} 
                ),
                width="100%",
                padding_left="8px",
                padding_top="8px"
            ),
            value=label,
            style={
                "background": "transparent", 
                "border": "none",
                "_hover": {"background": "transparent"}
            }
        ),
        type="multiple",
        collapsible=True,
        width="100%",
        color_scheme="gray",
        variant="ghost"
    )
