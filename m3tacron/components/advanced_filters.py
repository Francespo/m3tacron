
import reflex as rx
from ..theme import (
    TEXT_PRIMARY, TEXT_SECONDARY, BORDER_COLOR, INPUT_STYLE, RADIUS
)
from .filter_accordion import filter_accordion
from .searchable_filter_accordion import searchable_filter_accordion

def advanced_filters(state) -> rx.Component:
    """
    Render the advanced filters for the Card Browser.
    All filters under single "Card Filters" section (no sub-headers).
    """
    
    return rx.vstack(
        # Text Search
        rx.box(
            rx.text("Text Search", weight="bold", size="1", color=TEXT_SECONDARY),
            rx.input(
                placeholder="Search card text",
                value=state.text_filter,
                on_change=state.set_text_filter,
                style=INPUT_STYLE,
                width="100%"
            ),
            width="100%"
        ),
        
        # Factions
        filter_accordion(
            "Factions",
            state.faction_options,
            state.selected_factions,
            state.toggle_faction
        ),
        
        # Ships (Pilots only)
        rx.cond(
            state.active_tab == "pilots",
            searchable_filter_accordion(
                "Chassis",
                state.available_ships,
                state.selected_ships,
                state.toggle_ship,
                state.ship_search_text,
                state.set_ship_search
            )
        ),
        
        # Point Costs (Range)
        rx.vstack(
            rx.text("Point Costs", weight="bold", size="1", color=TEXT_SECONDARY),
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
            spacing="1",
            width="100%"
        ),
        
        # Loadout Value (XWA Pilots Only)
        rx.cond(
            (state.active_tab == "pilots") & (state.data_source == "xwa"),
            rx.vstack(
                rx.text("Loadout Value", weight="bold", size="1", color=TEXT_SECONDARY),
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
                spacing="1",
                width="100%"
            )
        ),
        
        # Limited/Unique toggles (3 options on same line)
        rx.vstack(
            rx.text("Uniqueness", weight="bold", size="1", color=TEXT_SECONDARY),
            rx.hstack(
                rx.checkbox("Unique", checked=state.is_unique, on_change=state.set_is_unique),
                rx.checkbox("Limited", checked=state.is_limited, on_change=state.set_is_limited),
                rx.checkbox("Generic", checked=state.is_not_limited, on_change=state.set_is_not_limited),
                spacing="5",
                wrap="nowrap"
            ),
            spacing="1",
            width="100%"
        ),
        
        # Base Size (S/M/L/H on same line) - Pilots Only
        rx.cond(
            state.active_tab == "pilots",
            rx.vstack(
                rx.text("Base Size", weight="bold", size="1", color=TEXT_SECONDARY),
                rx.hstack(
                    rx.checkbox("S", on_change=lambda x: state.toggle_base_size("S", x)),
                    rx.checkbox("M", on_change=lambda x: state.toggle_base_size("M", x)),
                    rx.checkbox("L", on_change=lambda x: state.toggle_base_size("L", x)),
                    rx.checkbox("H", on_change=lambda x: state.toggle_base_size("H", x)),
                    spacing="3"
                ),
                spacing="1",
                width="100%"
            )
        ),
        
        # --- PILOT-SPECIFIC STATS ---
        rx.cond(
            state.active_tab == "pilots",
            rx.vstack(
                # Initiative (Range)
                rx.hstack(
                    rx.text("Initiative:", size="1", color=TEXT_SECONDARY, min_width="70px"),
                    rx.input(value=state.init_min, on_change=state.set_init_min, type="number", style=INPUT_STYLE, width="50px"),
                    rx.text("to", size="1", color=TEXT_SECONDARY),
                    rx.input(value=state.init_max, on_change=state.set_init_max, type="number", style=INPUT_STYLE, width="50px"),
                    align_items="center",
                    width="100%"
                ),
                # Hull
                rx.hstack(
                    rx.text("Hull:", size="1", color=TEXT_SECONDARY, min_width="70px"),
                    rx.input(value=state.hull_min, on_change=state.set_hull_min, type="number", style=INPUT_STYLE, width="50px"),
                    rx.text("to", size="1", color=TEXT_SECONDARY),
                    rx.input(value=state.hull_max, on_change=state.set_hull_max, type="number", style=INPUT_STYLE, width="50px"),
                    align_items="center",
                    width="100%"
                ),
                # Shields
                rx.hstack(
                    rx.text("Shields:", size="1", color=TEXT_SECONDARY, min_width="70px"),
                    rx.input(value=state.shields_min, on_change=state.set_shields_min, type="number", style=INPUT_STYLE, width="50px"),
                    rx.text("to", size="1", color=TEXT_SECONDARY),
                    rx.input(value=state.shields_max, on_change=state.set_shields_max, type="number", style=INPUT_STYLE, width="50px"),
                    align_items="center",
                    width="100%"
                ),
                # Agility
                rx.hstack(
                    rx.text("Agility:", size="1", color=TEXT_SECONDARY, min_width="70px"),
                    rx.input(value=state.agility_min, on_change=state.set_agility_min, type="number", style=INPUT_STYLE, width="50px"),
                    rx.text("to", size="1", color=TEXT_SECONDARY),
                    rx.input(value=state.agility_max, on_change=state.set_agility_max, type="number", style=INPUT_STYLE, width="50px"),
                    align_items="center",
                    width="100%"
                ),
                # Attack
                rx.hstack(
                    rx.text("Attack:", size="1", color=TEXT_SECONDARY, min_width="70px"),
                    rx.input(value=state.attack_min, on_change=state.set_attack_min, type="number", style=INPUT_STYLE, width="50px"),
                    rx.text("to", size="1", color=TEXT_SECONDARY),
                    rx.input(value=state.attack_max, on_change=state.set_attack_max, type="number", style=INPUT_STYLE, width="50px"),
                    align_items="center",
                    width="100%"
                ),
                spacing="2",
                width="100%"
            )
        ),
        
        # --- UPGRADE-SPECIFIC FILTERS ---
        rx.cond(
            state.active_tab == "upgrades",
            rx.vstack(
                # Upgrade Types
                filter_accordion(
                    "Upgrade Type",
                    state.upgrade_type_options,
                    state.selected_upgrade_types,
                    state.toggle_upgrade_type
                ),
                spacing="3",
                width="100%"
            )
        ),

        spacing="3",
        width="100%"
    )
