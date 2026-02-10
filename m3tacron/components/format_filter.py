"""
Hierarchical Format Filter Component.
"""
import reflex as rx
from ..backend.data_structures.formats import Format, MacroFormat
from ..theme import TEXT_PRIMARY, TEXT_SECONDARY, BORDER_COLOR, INPUT_STYLE, MONOSPACE_FONT

from ..ui_utils.pagination import PaginationMixin

class FormatFilterMixin(PaginationMixin):
    """
    Mixin for states that need hierarchical format filtering.
    """
    # Map of format/macro value -> boolean
    selected_formats: dict[str, bool] = {m.value: True for m in MacroFormat} | {f.value: True for f in Format}

    @rx.var
    def macro_states(self) -> dict[str, str]:
        """
        Compute the state of each macro: 'checked', 'unchecked', or 'indeterminate'.
        """
        states = {}
        for m in MacroFormat:
            children = [f.value for f in m.formats()]
            if not children:
                states[m.value] = "unchecked"
                continue
            
            # Count how many children are checked
            checked_count = sum(1 for c in children if self.selected_formats.get(c, False))
            
            if checked_count == len(children):
                states[m.value] = "checked"
            elif checked_count == 0:
                states[m.value] = "unchecked"
            else:
                states[m.value] = "indeterminate"
        return states

    def toggle_format_macro(self, macro_val: str):
        """Toggle a macro format based on its current state."""
        # Logic: If checked or indeterminate -> Uncheck all. If unchecked -> Check all.
        current_state = self.macro_states.get(macro_val, "unchecked")
        
        target_checked = True
        if current_state == "checked" or current_state == "indeterminate":
            target_checked = False
            
        new_formats = self.selected_formats.copy()
        # Update children
        try:
            macro = MacroFormat(macro_val)
            for f in macro.formats():
                new_formats[f.value] = target_checked
        except ValueError:
            pass
            
        # Update macro itself (for consistency, though computed var drives UI)
        new_formats[macro_val] = target_checked
        
        self.selected_formats = new_formats
        self.on_filter_change()

    def toggle_format_child(self, child_val: str):
        """Toggle a specific format child."""
        checked = not self.selected_formats.get(child_val, False)

        new_formats = self.selected_formats.copy()
        new_formats[child_val] = checked
        self.selected_formats = new_formats
        self.on_filter_change()

    def set_default_formats_for_source(self, source: str):
        """Set default format selection based on content source."""
        # Reset all to False
        new_sel = {k: False for k in self.selected_formats}
        
        keys_to_enable = []
        if source == "xwa":
            # AMG, XWA, Wildspace are typical 2.5 formats
            keys_to_enable = ["amg", "xwa", "wildspace"]
        elif source == "legacy":
            # 2.0 Legacy formats
            keys_to_enable = ["legacy_x2po", "legacy_xlc", "ffg"]
            
        for k in keys_to_enable:
            if k in new_sel:
                new_sel[k] = True
                
        self.selected_formats = new_sel

    def on_filter_change(self):
        """Hook for sub-classes to handle filter changes."""
        return []

def render_checkbox_icon(status: str) -> rx.Component:
    """Render a custom checkbox icon based on status string."""
    return rx.cond(
        status == "checked",
        rx.icon("check", size=14, color="white"), # Standard check
        rx.cond(
            status == "indeterminate",
            rx.icon("minus", size=14, color="white"), # Indeterminate dash
            rx.fragment() # Unchecked
        )
    )

def render_custom_checkbox(status: str, on_click: callable) -> rx.Component:
    """
    Render a composed checkbox that supports 'indeterminate'.
    """
    return rx.box(
        render_checkbox_icon(status),
        width="16px",
        height="16px",
        border=f"1px solid {BORDER_COLOR}",
        border_radius="4px",
        display="flex",
        align_items="center",
        justify_content="center",
        cursor="pointer",
        bg=rx.cond(status == "unchecked", "transparent", rx.cond(status == "indeterminate", "gray", "var(--accent-9)")),
        on_click=on_click,
        _hover={"border_color": TEXT_SECONDARY}
    )

def render_macro_section(
    macro: MacroFormat, 
    state: any,
) -> rx.Component:
    """
    Render a macro format section as a flattened list with indentation.
    """
    path_to_selection = state.selected_formats
    macro_status = state.macro_states[macro.value]
    
    children_components = []
    
    # Static iteration over children using enum
    for child in macro.formats():
        children_components.append(
            rx.hstack(
                rx.checkbox(
                    checked=path_to_selection[child.value],
                    on_change=lambda val, c=child: state.toggle_format_child(c.value),
                    color_scheme="gray",
                    size="1",
                ),
                rx.text(
                    child.label, 
                    size="1", 
                    color=TEXT_PRIMARY,
                    font_family=MONOSPACE_FONT,
                    on_click=lambda c=child: state.toggle_format_child(c.value),
                    cursor="pointer"
                ),
                spacing="2",
                align="center",
                padding_left="24px", # Indentation for children
                width="100%"
            )
        )

    return rx.vstack(
        # Macro Header
        rx.hstack(
            render_custom_checkbox(
                macro_status,
                lambda: state.toggle_format_macro(macro.value)
            ),
            rx.text(
                macro.label, 
                weight="bold", 
                size="1", 
                color=TEXT_SECONDARY,
                font_family=MONOSPACE_FONT,
                letter_spacing="1px",
                on_click=lambda: state.toggle_format_macro(macro.value),
                cursor="pointer"
            ),
            align="center",
            width="100%",
            spacing="2",
            padding_y="4px"
        ),
        # Children Container
        rx.vstack(
             *children_components,
             spacing="1",
             width="100%",
             padding_top="0px",
        ),
        spacing="0",
        width="100%",
        align_items="start"
    )

def hierarchical_format_filter(
    state: any,
    label: str = "Format"
) -> rx.Component:
    """
    Main component.
    """
    # Static iteration over Macros using enum
    macro_items = []
    for m in MacroFormat:
        macro_items.append(
            render_macro_section(m, state)
        )
    
    # Stack of Macro Sections (Flattened visually)
    macro_stack = rx.vstack(
        *macro_items,
        spacing="1",
        width="100%"
    )

    # Outer Accordion Item (The "Wrapper")
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
                    _hover={"background": "transparent"},
                )
            ),
            rx.accordion.content(
                rx.box(
                    macro_stack,
                    width="100%",
                    padding_left="8px",
                    padding_top="0px"
                )
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
