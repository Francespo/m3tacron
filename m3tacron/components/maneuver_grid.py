
import reflex as rx
from ..theme import TEXT_PRIMARY, TEXT_SECONDARY, BORDER_COLOR, RADIUS, INPUT_STYLE

def maneuver_grid(
    state_var_dials: dict[str, bool],
    on_change_handler: callable
) -> rx.Component:
    """
    Renders a grid of maneuvers for filtering.
    Structure based on the provided screenshot (Speed 0-5 on rows, bearing columns).
    """
    
    speeds = [0, 1, 2, 3, 4, 5]
    # Bearings: 
    # T (Turn Left), B (Bank Left), F (Straight), B (Bank Right), T (Turn Right), K (Koiogran), S (Segnor's Loop Left), S (Segnor's Loop Right), T (Tallon Roll Left), T (Tallon Roll Right), R (Reverse/Stop)
    # The screenshot shows icons. We'll use text or icons.
    # Rows: Speed
    # Cols: Bearings.
    # Simplified mapping for user selection:
    # We need to decide what the filter actually *does*. 
    # Usually it filters for ships that have *at least one* of the selected maneuvers.
    
    # We'll use a simplified representation:
    # Speed 0-5
    # For each speed, checkboxes for: Turn, Bank, Straight, K-Turn, S-Loop, T-Roll, Reverse?
    # This might be too complex for a single component without proper icons.
    # The screenshot shows a grid of specific maneuvers.
    
    # Placeholder for now: simple text description or simplified grid.
    # Given the complexity of "Maneuver Dial" filtering, we might need a dedicated data structure.
    # For now, let's render a placeholder "Maneuvers" section that can be expanded later 
    # unless we have the assets for maneuver icons.
    
    return rx.vstack(
        rx.text("Maneuvers (Coming Soon)", color=TEXT_SECONDARY, size="1"),
        # TODO: Implement full dial grid once icons are available
    )
