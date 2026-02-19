
import reflex as rx
from ..theme import (
    TEXT_PRIMARY, TEXT_SECONDARY, BORDER_COLOR, MONOSPACE_FONT, 
    FACTION_COLORS, TERMINAL_PANEL_STYLE, SANS_FONT
)
from ..ui_utils.factions import faction_icon, get_faction_color
from ..components.icons import ship_icon

def meta_stat_card(label: str, value: str, subtext: str = "", icon: str = "activity") -> rx.Component:
    """A sleek metric card for the meta dashboard."""
    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.icon(icon, size=16, color=TEXT_SECONDARY),
                rx.text(label, size="1", color=TEXT_SECONDARY, font_family=MONOSPACE_FONT, weight="bold"),
                align="center",
                spacing="2",
            ),
            rx.text(value, size="6", color=TEXT_PRIMARY, font_family=SANS_FONT, weight="bold"),
            rx.cond(
                subtext != "",
                rx.text(subtext, size="1", color=TEXT_SECONDARY, font_family=MONOSPACE_FONT, as_="span"),
                rx.fragment()
            ),
            spacing="1",
            align="start",
        ),
        padding="16px",
        style=TERMINAL_PANEL_STYLE,
        width="100%",
    )

def faction_performance_chart(data: list[dict], data_key: str = "win_rate", title: str = "Win Rate (%)") -> rx.Component:
    """Bar chart for faction analytics."""
    return rx.vstack(
        rx.text(title.upper(), size="2", weight="bold", color=TEXT_PRIMARY, font_family=MONOSPACE_FONT),
        rx.recharts.responsive_container(
            rx.recharts.bar_chart(
                rx.recharts.cartesian_grid(stroke_dasharray="3 3", stroke="#222"),
                rx.recharts.x_axis(data_key="icon_char", stroke=TEXT_SECONDARY, tick={"fontFamily": "XWing", "fontSize": 20, "fill": TEXT_SECONDARY}),
                rx.recharts.y_axis(stroke=TEXT_SECONDARY, style={"font_family": MONOSPACE_FONT, "font_size": "10px"}),
                rx.recharts.bar(
                    rx.foreach(
                        data,
                        lambda entry: rx.recharts.cell(
                            fill=get_faction_color(entry["xws"]),
                        )
                    ),
                    data_key=data_key,
                    radius=[4, 4, 0, 0],
                    is_animation_active=False,
                ),
                data=data,
            ),
            height=250,
            width="100%",
        ),
        width="100%",
        padding="20px",
        style=TERMINAL_PANEL_STYLE,
    )

def faction_game_pie_chart(data: list[dict]) -> rx.Component:
    """Pie chart for faction game distribution."""
    return rx.vstack(
        rx.text("GAME DISTRIBUTION", size="2", weight="bold", color=TEXT_PRIMARY, font_family=MONOSPACE_FONT),
        rx.recharts.responsive_container(
            rx.recharts.pie_chart(
                rx.recharts.pie(
                    rx.foreach(
                        data,
                        lambda entry: rx.recharts.cell(
                            fill=get_faction_color(entry["xws"]),
                        )
                    ),
                    data=data,
                    data_key="games",
                    name_key="name",
                    label={
                        "position": "outside",
                        "fill": "#888",
                        "fontSize": "22px",
                        "fontFamily": "XWing",
                    },
                    labelLine=False, 
                    cx="50%",
                    cy="50%",
                    outer_radius=70,  # Reduced from 80 to avoid label overlap
                    is_animation_active=False,
                ),
            ),
            height=250,
            width="100%",
        ),
        width="100%",
        padding="20px",
        style=TERMINAL_PANEL_STYLE,
    )

def sort_toggle(value: rx.Var, on_change: callable) -> rx.Component:
    """A small toggle for popularity vs winrate."""
    return rx.segmented_control.root(
        rx.segmented_control.item("POP", value="popularity"),
        rx.segmented_control.item("WR%", value="win_rate"),
        value=value,
        on_change=on_change,
        size="1",
        variant="surface",
        margin_left="auto",
    )

def top_list_row(list_data: any, value: rx.Var | str, on_click: callable = None) -> rx.Component:
    """A descriptive row for lists showing pilots and their key upgrades."""
    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.box(
                    faction_icon(list_data.faction_key, size="1.2em"),
                    width="24px",
                    height="24px",
                    display="flex",
                    align_items="center",
                    justify_content="center",
                ),
                rx.spacer(),
                rx.text(value, size="2", weight="bold", font_family=MONOSPACE_FONT, color=TEXT_PRIMARY),
                width="100%",
                align="center",
                margin_bottom="4px",
            ),
            rx.vstack(
                rx.foreach(
                    list_data.pilots,
                    lambda p: rx.vstack(
                        rx.hstack(
                            ship_icon(p.ship_icon, size="1em"),
                            rx.text(p.name, size="2", weight="bold", color=TEXT_PRIMARY),
                            spacing="2",
                            align="center",
                        ),
                        rx.flex(
                            rx.foreach(
                                p.upgrades,
                                lambda u: rx.text(u.name, size="1", color=TEXT_SECONDARY, margin_right="6px")
                            ),
                            wrap="wrap",
                            width="100%",
                        ),
                        spacing="1",
                        align="start",
                        width="100%",
                        padding_y="2px",
                    )
                ),
                spacing="2",
                width="100%",
            ),
            spacing="1",
            width="100%",
        ),
        padding="10px 14px",
        width="100%",
        border_bottom=f"1px solid {BORDER_COLOR}",
        bg="rgba(255, 255, 255, 0.01)",
        _hover={"background": "rgba(255, 255, 255, 0.03)", "cursor": "pointer" if on_click else "default"},
        on_click=on_click
    )

def top_item_row(name: str, xws: str, value: str, subvalue: str = "", rank: int = 1, is_ship: bool = False, is_list: bool = False, on_click: callable = None, ship_icon_xws: str = None) -> rx.Component:
    """A row in the 'Top Players/Ships/Cards' list."""
    # Icon Logic: Rank or Icon
    # is_ship and is_list are Python bools (literals) passed from loop
    if is_ship:
        icon_component = rx.box(
            ship_icon(xws, size="1.3em"),
            width="32px",
            height="32px",
            display="flex",
            align_items="center",
            justify_content="center",
            border_radius="4px",
            bg="rgba(255,255,255,0.05)",
            margin_right="12px"
        )
    elif is_list:
        # Use faction icon for list
        icon_component = rx.box(
            faction_icon(xws, size="1.5em"), # xws is faction key for lists
            width="32px",
            height="32px",
            display="flex",
            align_items="center",
            justify_content="center",
            margin_right="12px"
        )
    else:
        # Default Rank Icon
        rank_icon = rx.box(
            rx.text(f"#{rank}", color=TEXT_SECONDARY, font_family=MONOSPACE_FONT, weight="bold"),
            width="32px",
            height="32px",
            display="flex",
            align_items="center",
            justify_content="center",
            border_radius="50%",
            border=f"1px solid {BORDER_COLOR}",
            margin_right="12px"
        )
        
        # If ship_icon_xws var provided, conditionally render it
        if ship_icon_xws is not None:
            icon_component = rx.cond(
                ship_icon_xws, # Uses truthiness (handles undefined/null/empty string)
                rx.box(
                    ship_icon(ship_icon_xws, size="1.2em"),
                    width="32px",
                    height="32px",
                    display="flex",
                    align_items="center",
                    justify_content="center",
                    margin_right="12px"
                ),
                rank_icon
            )
        else:
            icon_component = rank_icon

    return rx.hstack(
        icon_component,
        rx.vstack(
            rx.text(name, size="2", weight="bold", color=TEXT_PRIMARY, _hover={"text_decoration": "underline" if on_click else "none"}),
            rx.text(subvalue, size="1", color=TEXT_SECONDARY),
            spacing="1",
            align="start",
            width="100%"
        ),
        rx.spacer(),
        rx.text(value, size="2", weight="bold", font_family=MONOSPACE_FONT),
        
        width="100%",
        padding="8px 12px",
        align="center",
        border_bottom=f"1px solid {BORDER_COLOR}",
        bg="rgba(255, 255, 255, 0.02)",
        _hover={"background": "rgba(255, 255, 255, 0.05)", "cursor": "pointer" if on_click else "default"},
        on_click=on_click
    )
