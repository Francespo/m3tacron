"""
Usage Chart Component using Recharts.
"""
import reflex as rx
from ..theme import TEXT_PRIMARY, TEXT_SECONDARY, BORDER_COLOR, TERMINAL_PANEL_STYLE, MONOSPACE_FONT

def usage_chart(data: list[dict], series_list: list[dict]) -> rx.Component:
    """
    Render a Line Chart for card usage history.
    
    Args:
        data: List of dicts, e.g. [{"date": "2023-01", "xws_1": 10, "xws_2": 5}]
        series_list: List of dicts [{"data_key": "xws", "name": "Name", "color": "red"}]
    """
    return rx.recharts.responsive_container(
        rx.recharts.line_chart(
            rx.recharts.cartesian_grid(stroke_dasharray="3 3", stroke="#333"),
            rx.recharts.x_axis(data_key="date", stroke=TEXT_SECONDARY, style={"font_family": MONOSPACE_FONT, "font_size": "10px"}),
            rx.recharts.y_axis(stroke=TEXT_SECONDARY, style={"font_family": MONOSPACE_FONT, "font_size": "10px"}),
            rx.recharts.tooltip(
                content_style={"background_color": "#000", "border": f"1px solid {BORDER_COLOR}", "border_radius": "4px"},
                item_style={"color": TEXT_PRIMARY, "font_family": MONOSPACE_FONT},
                label_style={"color": TEXT_SECONDARY, "font_family": MONOSPACE_FONT}
            ),
            rx.recharts.legend(),
            rx.foreach(
                series_list,
                lambda item: rx.recharts.line(
                    data_key=item["data_key"],
                    name=item["name"],
                    stroke=item["color"],
                    type_="monotone",
                    stroke_width=2,
                    dot=False,
                    active_dot={"r": 4}
                )
            ),
            data=data,
        ),
        height=300,
        width="100%"
    )
