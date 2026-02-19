
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
                rx.text(subtext, size="1", color=TEXT_SECONDARY, font_family=MONOSPACE_FONT),
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
                rx.recharts.x_axis(data_key="name", stroke=TEXT_SECONDARY, style={"font_family": MONOSPACE_FONT, "font_size": "10px"}),
                rx.recharts.y_axis(stroke=TEXT_SECONDARY, style={"font_family": MONOSPACE_FONT, "font_size": "10px"}),
                rx.recharts.tooltip(
                    content_style={"background_color": "#000", "border": f"1px solid {BORDER_COLOR}", "border_radius": "4px"},
                    item_style={"color": TEXT_PRIMARY, "font_family": MONOSPACE_FONT},
                    label_style={"color": TEXT_SECONDARY, "font_family": MONOSPACE_FONT}
                ),
                rx.recharts.bar(
                    rx.foreach(
                        data,
                        lambda entry: rx.recharts.cell(
                            fill=get_faction_color(entry["xws"]),
                        )
                    ),
                    data_key=data_key,
                    radius=[4, 4, 0, 0],
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
                    cx="50%",
                    cy="50%",
                    outer_radius=80,
                    label=True,
                ),
                rx.recharts.tooltip(
                    content_style={"background_color": "#000", "border": f"1px solid {BORDER_COLOR}", "border_radius": "4px"},
                    item_style={"color": TEXT_PRIMARY, "font_family": MONOSPACE_FONT},
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

def top_item_row(name: str, xws: str, value: str, subvalue: str = "", rank: int = 1, is_ship: bool = False, is_list: bool = False) -> rx.Component:
    """A row in the 'Top Players/Ships/Cards' list."""
    return rx.hstack(
        rx.text(f"{rank}.", size="2", color=TEXT_SECONDARY, font_family=MONOSPACE_FONT, width="24px"),
        rx.vstack(
            rx.text(name, size="2", weight="bold", color=TEXT_PRIMARY, font_family=SANS_FONT, white_space="nowrap", overflow="hidden", text_overflow="ellipsis", max_width="200px"),
            rx.hstack(
                rx.text(value, size="1", color=TEXT_SECONDARY, font_family=MONOSPACE_FONT),
                rx.cond(subvalue != "", rx.text(f"({subvalue})", size="1", color="#444444", font_family=MONOSPACE_FONT), rx.fragment()),
                spacing="2",
            ),
            align="start",
            spacing="0",
        ),
        rx.spacer(),
        rx.cond(
            is_list,
            rx.icon("layers", size=18, color=TEXT_SECONDARY),
            rx.cond(
                is_ship,
                ship_icon(xws, size="20px", color=TEXT_PRIMARY),
                faction_icon(xws, size="20px")
            )
        ),
        width="100%",
        padding="10px 16px",
        border_bottom=f"1px solid {BORDER_COLOR}",
        transition="all 0.2s",
        _hover={"background": "rgba(255, 255, 255, 0.03)"}
    )
