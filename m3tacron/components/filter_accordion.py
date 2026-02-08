import reflex as rx
from ..theme import TEXT_PRIMARY, TEXT_SECONDARY, BORDER_COLOR, MONOSPACE_FONT

def checkbox_row(label: str, value: str, state_map: rx.Var, on_toggle: callable) -> rx.Component:
    """A minimal transparent checkbox row."""
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

def filter_accordion(
    label: str,
    options: list[list[str]], # [[label, value], ...]
    state_map: rx.Var,  # Dict[str, bool]
    on_toggle: callable, # Function(value, checked)
) -> rx.Component:
    """
    A transparent, black & white accordion for filters.
    """
    return rx.accordion.root(
        rx.accordion.item(
            rx.accordion.header(
                rx.accordion.trigger(
                    rx.text(
                        label, 
                        size="1", 
                        weight="bold", 
                        color=TEXT_SECONDARY, 
                        font_family=MONOSPACE_FONT,
                        letter_spacing="1px"
                    ),
                    rx.accordion.icon(),
                    align_items="center",
                    display="flex",
                    justify_content="space-between",
                    width="100%",
                    padding_y="8px", # Minimal vertical padding for interaction
                    padding_x="0px", # Remove horizontal padding to align with text above
                    _hover={"background": "transparent", "opacity": 0.8},
                )
            ),
            rx.accordion.content(
                rx.vstack(
                    rx.foreach(
                        options,
                        lambda opt: checkbox_row(opt[0], opt[1], state_map, on_toggle)
                    ),
                    spacing="1",
                    width="100%",
                    padding_left="8px", # Indentation
                    padding_top="0px"
                )
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
        variant="ghost" # Ghost variant usually has no borders/bg
    )
