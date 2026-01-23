"""
Hierarchical Format Filter Component.
"""
import reflex as rx
from ..ui_utils.formats import FORMAT_HIERARCHY, get_default_format_selection
from ..theme import TEXT_PRIMARY, TEXT_SECONDARY, BORDER_COLOR, INPUT_STYLE, MONOSPACE_FONT

class FormatFilterMixin:
    """
    Mixin for states that need hierarchical format filtering.
    """
    # Map of format/macro value -> boolean
    selected_formats: dict[str, bool] = get_default_format_selection()

    def toggle_format_macro(self, macro_val: str, checked: bool):
        """Toggle a macro format and all its children."""
        self.selected_formats[macro_val] = checked
        # Toggle all children
        for m in FORMAT_HIERARCHY:
            if m["value"] == macro_val:
                for child in m["children"]:
                    self.selected_formats[child["value"]] = checked
        self.on_filter_change()

    def toggle_format_child(self, child_val: str, checked: bool):
        """Toggle a specific format child."""
        self.selected_formats[child_val] = checked
        # Optional: update macro indeterminate state logic could go here
        self.on_filter_change()

    def on_filter_change(self):
        """Hook for sub-classes to handle filter changes."""
        pass

def render_format_item(item: dict, state_var: rx.Var, on_toggle: callable) -> rx.Component:
    """
    Render a single format toggle item.
    item: {"label": "...", "value": "..."}
    """
    return rx.hstack(
        rx.checkbox(
            checked=state_var[item["value"]],
            on_change=lambda val: on_toggle(item["value"], val),
            color_scheme="green",
        ),
        rx.text(item["label"], size="2", color=TEXT_PRIMARY),
        spacing="2",
        align="center"
    )

def render_macro_section(
    macro: dict, 
    path_to_selection: rx.Var, 
    on_toggle_macro: callable, 
    on_toggle_child: callable
) -> rx.Component:
    """
    Render a macro format section as an accordion item.
    """
    children_components = []
    
    # Static iteration over children
    for child in macro["children"]:
        children_components.append(
            rx.hstack(
                rx.checkbox(
                    checked=path_to_selection[child["value"]],
                    on_change=lambda val: on_toggle_child(child["value"], val),
                    color_scheme="gray",
                    size="1",
                ),
                rx.text(
                    child["label"], 
                    size="1", 
                    color=TEXT_PRIMARY,
                    font_family=MONOSPACE_FONT,
                    on_click=lambda: on_toggle_child(child["value"], ~path_to_selection[child["value"]]),
                    cursor="pointer"
                ),
                spacing="2",
                align="center",
                padding_left="8px"
            )
        )

    return rx.accordion.item(
        header=rx.hstack(
            rx.checkbox(
                checked=path_to_selection[macro["value"]],
                on_change=lambda val: on_toggle_macro(macro["value"], val),
                size="1", 
                color_scheme="gray",
            ),
            rx.text(
                macro["label"], 
                weight="bold", 
                size="1", 
                color=TEXT_SECONDARY,
                font_family=MONOSPACE_FONT,
                letter_spacing="1px"
            ),
            spacing="2",
            align="center",
            width="100%",
        ),
        content=rx.vstack(
            *children_components,
            spacing="1",
            width="100%",
            padding_top="8px"
        ),
        value=macro["label"], # Value for open state
        style={
            "background": "transparent", 
            "border": "none",
            "_hover": {"background": "transparent"}
        }
    )

def hierarchical_format_filter(
    selection_var: rx.Var, 
    on_toggle_macro: callable, 
    on_toggle_child: callable,
    label: str = "Formats"
) -> rx.Component:
    """
    Main component.
    """
    # Static iteration over Macros
    macro_items = []
    for m in FORMAT_HIERARCHY:
        macro_items.append(
            render_macro_section(m, selection_var, on_toggle_macro, on_toggle_child)
        )
    
    # Inner Accordion for Macros
    inner_accordion = rx.accordion.root(
        *macro_items,
        type="multiple",
        collapsible=True,
        width="100%",
        color_scheme="gray",
        variant="ghost"
    )

    # Outer Accordion Item (The "Wrapper")
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
            content=rx.box(
                inner_accordion,
                width="100%",
                padding_left="8px"
            ),
            value="main",
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
