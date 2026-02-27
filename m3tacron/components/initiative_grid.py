import reflex as rx
from ..theme import TEXT_PRIMARY, TEXT_SECONDARY, BORDER_COLOR, MONOSPACE_FONT, RADIUS

def initiative_cell(val: str, state_map: rx.Var, on_toggle: callable) -> rx.Component:
    """A single initiative toggle cell."""
    is_selected = state_map[val]
    
    return rx.box(
        rx.text(val, size="1", weight="bold", font_family=MONOSPACE_FONT),
        on_click=lambda: on_toggle(val, ~is_selected),
        width="100%",
        height="32px",
        display="flex",
        align_items="center",
        justify_content="center",
        border=f"1px solid {BORDER_COLOR}",
        border_radius=RADIUS,
        cursor="pointer",
        bg=rx.cond(is_selected, "rgba(255,255,255,0.1)", "transparent"),
        color=rx.cond(is_selected, TEXT_PRIMARY, TEXT_SECONDARY),
        _hover={"bg": "rgba(255,255,255,0.05)", "border_color": TEXT_PRIMARY},
        transition="all 0.2s"
    )

def initiative_grid(
    label: str,
    state_map: rx.Var,  # Dict[str, bool]
    on_toggle: callable, # Function(value, checked)
) -> rx.Component:
    """
    A compact grid layout for initiative selection, wrapped in a dropdown (accordion).
    """
    options = [str(i) for i in range(7)]
    
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
                    padding_y="8px",
                    padding_x="0px",
                    _hover={"background": "transparent", "opacity": 0.8},
                )
            ),
            rx.accordion.content(
                rx.box(
                    rx.grid(
                        rx.foreach(
                            options,
                            lambda opt: initiative_cell(opt, state_map, on_toggle)
                        ),
                        columns="4",
                        spacing="2",
                        width="100%",
                    ),
                    width="100%",
                    padding_top="0px",
                    padding_left="8px"
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
        variant="ghost"
    )
