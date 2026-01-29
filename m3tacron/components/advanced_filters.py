
import reflex as rx
from ..theme import (
    TEXT_PRIMARY, TEXT_SECONDARY, BORDER_COLOR, INPUT_STYLE, RADIUS
)
from .filter_accordion import filter_accordion
from .initiative_grid import initiative_grid
from .maneuver_grid import maneuver_grid
# We don't have a maneuver accordion yet, let's just stick to generic inputs for now or reuse existing.

def advanced_filters(state) -> rx.Component:
    """
    Render the advanced filters for the Card Browser.
    Matches YASB layout:
    - General (Search, Faction, Points, Copies, Misc)
    - Ships and Pilots (Slots, Keywords, Actions, Stats, Dial) -> Only for Pilots
    - Other Stuff (Slots, Charges, Force) -> Only for Upgrades (mostly)
    """
    
    return rx.vstack(
        # --- GENERAL SECTION ---
        rx.text("General", size="2", weight="bold", color=TEXT_PRIMARY, width="100%", border_bottom=f"1px solid {BORDER_COLOR}"),
        
        # Text Search (Already in basic, but part of General here)
        rx.box(
            rx.text("Textsearch:", weight="bold", size="1", color=TEXT_PRIMARY),
            rx.input(
                placeholder="Search for name, text or ship",
                value=state.text_filter,
                on_change=state.set_text_filter,
                style=INPUT_STYLE,
                width="100%"
            ),
            width="100%"
        ),
        
        # Fractions (Already exists)
        filter_accordion(
            "Factions",
            state.faction_options,
            state.selected_factions,
            state.toggle_faction
        ),
        
        # Point Costs (Range)
        rx.vstack(
            rx.text("Point costs:", weight="bold", size="1", color=TEXT_PRIMARY),
            rx.hstack(
                rx.text("from", size="1", color=TEXT_SECONDARY),
                rx.input(
                     value=state.points_min, 
                     on_change=state.set_points_min, 
                     type="number", 
                     style=INPUT_STYLE, width="60px"
                ),
                rx.text("to", size="1", color=TEXT_SECONDARY),
                rx.input(
                     value=state.points_max, 
                     on_change=state.set_points_max, 
                     type="number", 
                     style=INPUT_STYLE, width="60px"
                ),
                align_items="center"
            ),
            spacing="1"
        ),
        
        # Loadout Value (XWA Pilots Only)
        rx.cond(
            (state.active_tab == "pilots") & (state.data_source == "xwa"),
            rx.vstack(
                rx.text("Loadout Value:", weight="bold", size="1", color=TEXT_PRIMARY),
                rx.hstack(
                    rx.text("from", size="1", color=TEXT_SECONDARY),
                    rx.input(
                        value=state.loadout_min, 
                        on_change=state.set_loadout_min, 
                        type="number", 
                        style=INPUT_STYLE, width="60px"
                    ),
                    rx.text("to", size="1", color=TEXT_SECONDARY),
                    rx.input(
                        value=state.loadout_max, 
                        on_change=state.set_loadout_max, 
                        type="number", 
                        style=INPUT_STYLE, width="60px"
                    ),
                    align_items="center"
                ),
                spacing="1"
            )
        ),
        
        # Misc (Unique)
        rx.hstack(
            rx.checkbox("Is unique", on_change=state.set_is_unique),
            rx.checkbox("Is not unique", on_change=state.set_is_not_unique),
            spacing="3"
        ),
        
        rx.divider(border_color=BORDER_COLOR),
        
        # --- SHIPS AND PILOTS SECTION (PILOTS ONLY) ---
        rx.cond(
            state.active_tab == "pilots",
            rx.vstack(
                rx.text("Ships and Pilots", size="2", weight="bold", color=TEXT_PRIMARY, width="100%", border_bottom=f"1px solid {BORDER_COLOR}"),
                
                # Slots
                # Keywords
                # Actions 
                # (Skipping complex multi-selects for now if not backing logic exists, focusing on requested stats)
                
                # Initiative
                initiative_grid(
                    "Initiative",
                    state.selected_initiatives,
                    state.toggle_initiative
                ),
                
                # Hull, Shields, Agility
                rx.grid(
                    rx.text("Hull:", size="1"), rx.input(value=state.hull_min, on_change=state.set_hull_min, type="number", style=INPUT_STYLE, width="50px"), rx.text("to"), rx.input(value=state.hull_max, on_change=state.set_hull_max, type="number", style=INPUT_STYLE, width="50px"),
                    rx.text("Shields:", size="1"), rx.input(value=state.shields_min, on_change=state.set_shields_min, type="number", style=INPUT_STYLE, width="50px"), rx.text("to"), rx.input(value=state.shields_max, on_change=state.set_shields_max, type="number", style=INPUT_STYLE, width="50px"),
                    rx.text("Agility:", size="1"), rx.input(value=state.agility_min, on_change=state.set_agility_min, type="number", style=INPUT_STYLE, width="50px"), rx.text("to"), rx.input(value=state.agility_max, on_change=state.set_agility_max, type="number", style=INPUT_STYLE, width="50px"),
                    columns="4",
                    spacing="2",
                    align_items="center"
                ),
                
                # Base Size
                rx.hstack(
                     rx.text("Base Size:", weight="bold", size="1"),
                     rx.checkbox("Small", on_change=lambda x: state.toggle_base_size("Small", x)),
                     rx.checkbox("Medium", on_change=lambda x: state.toggle_base_size("Medium", x)),
                     rx.checkbox("Large", on_change=lambda x: state.toggle_base_size("Large", x)),
                     spacing="3",
                     wrap="wrap"
                ),
                
                spacing="3",
                width="100%"
            )
        ),
        
        # --- OTHER STUFF (UPGRADES ONLY) ---
        rx.cond(
            state.active_tab == "upgrades",
            rx.vstack(
                rx.text("Other Stuff", size="2", weight="bold", color=TEXT_PRIMARY, width="100%", border_bottom=f"1px solid {BORDER_COLOR}"),
                
                # Upgrade Types (Renamed "Used slot" / "Second Upgrade Type")
                filter_accordion(
                    "Used slot",
                    state.upgrade_type_options,
                    state.selected_upgrade_types,
                    state.toggle_upgrade_type
                ),
                
                 # Charges
                 rx.vstack(
                     rx.text("Charges:", weight="bold", size="1"),
                     rx.hstack(
                         rx.text("from", size="1"), rx.input(type="number", style=INPUT_STYLE, width="50px"), # Logic pending
                         rx.text("to", size="1"), rx.input(type="number", style=INPUT_STYLE, width="50px"),
                         align_items="center"
                     ),
                     rx.hstack(
                         rx.checkbox("Recurring"),
                         rx.checkbox("Not recurring"),
                         spacing="2"
                     )
                 ),
                 
                 # Force
                 rx.hstack(
                      rx.text("Force:", weight="bold", size="1"),
                      rx.text("from", size="1"), rx.input(type="number", style=INPUT_STYLE, width="50px"),
                      rx.text("to", size="1"), rx.input(type="number", style=INPUT_STYLE, width="50px"),
                      align_items="center"
                 ),
                 
                 spacing="3",
                 width="100%"
            )
        ),

        spacing="4",
        width="100%"
    )
