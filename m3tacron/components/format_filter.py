"""
Hierarchical Format Filter Component.
"""
import reflex as rx
from ..backend.enums.formats import FORMAT_HIERARCHY
from ..theme import TEXT_PRIMARY, TEXT_SECONDARY, BORDER_COLOR, INPUT_STYLE, MONOSPACE_FONT

class FormatFilterState(rx.State):
    """
    Sub-state for format filter logic needs to be integrated into the parent state usually,
    but here we can define components that take event handlers.
    
    Data structure expected:
    - selected_formats: dict[str, bool] - mapping of format values to boolean.
    
    If a macro key is True, it implies all children are effectively selected unless unchecked?
    Usually simpler: Toggle independently.
    Logic:
    - Toggle Macro: Select/Deselect ALL children.
    - Toggle Child: Toggle specific child. If all selected -> Macro selected. If mixed -> Macro indeterminate (or just simple check).
    """
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
    Render a macro format section with children using Python iteration.
    """
    children_components = []
    
    # Static iteration over children
    for child in macro["children"]:
        children_components.append(
            rx.hstack(
                rx.checkbox(
                    checked=path_to_selection[child["value"]],
                    on_change=lambda val: on_toggle_child(child["value"], val, macro["value"]),
                    color_scheme="gray", 
                ),
                rx.text(child["label"], size="2", color=TEXT_SECONDARY),
                spacing="2",
                align="center",
                padding_left="12px"
            )
        )

    return rx.vstack(
        # Macro Header
        rx.hstack(
            rx.checkbox(
                checked=path_to_selection[macro["value"]],
                on_change=lambda val: on_toggle_macro(macro["value"], val),
                size="3", 
                color_scheme="green",
            ),
            rx.text(macro["label"], weight="bold", size="3", color=TEXT_PRIMARY),
            spacing="3",
            align="center",
            width="100%",
            padding_y="4px",
            border_bottom=f"1px solid {BORDER_COLOR}"
        ),
        # Children
        rx.vstack(
            *children_components,
            spacing="2",
            width="100%",
            padding_y="8px"
        ),
        spacing="1",
        width="100%",
        align="start"
    )

def hierarchical_format_filter(
    selection_var: rx.Var, 
    on_toggle_macro: callable, 
    on_toggle_child: callable
) -> rx.Component:
    """
    Main component.
    """
    # Static iteration over Macros
    macro_components = []
    for m in FORMAT_HIERARCHY:
        macro_components.append(
            render_macro_section(m, selection_var, on_toggle_macro, on_toggle_child)
        )
    
    return rx.scroll_area(
        rx.vstack(
            *macro_components,
            spacing="4",
            width="100%",
        ),
        max_height="300px", 
        type="always",
        scrollbars="vertical",
        style={"padding_right": "10px"} 
    )
