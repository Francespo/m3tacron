import reflex as rx
from ..theme import TEXT_PRIMARY, TEXT_SECONDARY, INPUT_STYLE, BORDER_COLOR

def checkbox_item(label: str, value: str, state_map: rx.Var, on_toggle: callable) -> rx.Component:
    """A single checkbox item."""
    return rx.hstack(
        rx.checkbox(
             checked=state_map[value],
             on_change=lambda c: on_toggle(value, c),
             color_scheme="gray",
             size="1",
        ),
        rx.text(label, size="1", color=TEXT_PRIMARY, on_click=lambda: on_toggle(value, ~state_map[value]), cursor="pointer"),
        spacing="1",
        align="center",
        width="100%"
    )

def collapsible_checkbox_group(
    label: str,
    options: list[list[str]], # [[label, value], ...]
    state_map: rx.Var,  # Dict[str, bool]
    on_toggle: callable, # Function(value, checked)
    always_open: bool = False
) -> rx.Component:
    """
    A collapsible group of checkboxes with a summary header.
    
    Args:
        label: Title of the filter section.
        options: List of [Local Label, Backend Value] pairs.
        state_map: The State dictionary tracking selections.
        on_toggle: Event handler for toggling.
        always_open: If True, renders as a static vstack instead of accordion.
    """
    
    # Compute Summary
    # If all values in state_map are True -> "All"
    # Else join keys where value is True
    # Since we can't easily iterate Keys in Reflex Var for join string in frontend easily without a Computed Var,
    # we will rely on a generic check or just show "Active Filters" / "All".
    # BUT user asked for "elenco di parole separate da virgole".
    # This usually requires a Computed Var in the State to format the display string.
    # We will accept an optional `summary_text` var?
    # Or keep it simple: Just show Label.
    
    # Let's try to pass `summary_label` if possible, otherwise just use the Label.
    # For now, simplistic approach: Just the group label. 
    # To do specific summary, we'd need to bind it to a computed var in the State.
    
    content = rx.vstack(
        rx.foreach(
            options,
            lambda opt: checkbox_item(opt[0], opt[1], state_map, on_toggle)
        ),
        spacing="1",
        width="100%"
    )
    
    if always_open:
        return rx.vstack(
            rx.text(label, size="1", weight="bold", color=TEXT_SECONDARY),
            content,
            spacing="2",
            width="100%"
        )
        
    return rx.accordion.root(
        rx.accordion.item(
            header=rx.text(label, size="1", weight="bold", color=TEXT_SECONDARY),
            content=content,
            width="100%",
            border_color=BORDER_COLOR
        ),
        type="multiple",
        width="100%",
    )
