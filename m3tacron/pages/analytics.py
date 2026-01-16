"""
Analytics Page - Meta statistics visualization.
Star Wars Imperial aesthetic.

Aggregates faction and pilot usage data with optional format filtering.
"""
import reflex as rx
from sqlmodel import Session, select
from collections import Counter

from ..components.sidebar import layout
from ..backend.database import engine
from ..backend.models import PlayerResult, Tournament, Faction, MacroFormat
from ..backend.xwing_data import get_pilot_name, get_faction_icon


# Star Wars color palette
IMPERIAL_BLUE = "#4fb8ff"
IMPERIAL_RED = "#ff4757"
STEEL_BORDER = "#2a2a3a"
STEEL_BG = "#1a1a24"


class AnalyticsState(rx.State):
    """Manages statistics aggregation for the Analytics page."""
    
    faction_data: list[dict] = []
    pilot_data: list[dict] = []
    total_lists: int = 0
    format_filter: str = "all"
    
    # Faction display config: xws_id -> (display_name, color, icon_url)
    # Colors aligned with Star Wars faction aesthetics
    FACTION_CONFIG = {
        Faction.REBEL.value: ("Rebel Alliance", "#e74c3c"),
        Faction.EMPIRE.value: ("Galactic Empire", "#4fb8ff"),
        Faction.SCUM.value: ("Scum and Villainy", "#27ae60"),
        Faction.RESISTANCE.value: ("Resistance", "#e67e22"),
        Faction.FIRST_ORDER.value: ("First Order", "#ff4757"),
        Faction.REPUBLIC.value: ("Galactic Republic", "#ffc312"),
        Faction.SEPARATIST.value: ("Separatist Alliance", "#8e44ad"),
    }
    
    def load_analytics(self):
        """Aggregates faction and pilot stats, respecting format filter."""
        with Session(engine) as session:
            # Build query with optional format filter
            if self.format_filter == "all":
                results = session.exec(select(PlayerResult)).all()
            else:
                # Join with Tournament to filter by macro_format
                query = (
                    select(PlayerResult)
                    .join(Tournament, PlayerResult.tournament_id == Tournament.id)
                    .where(Tournament.macro_format == self.format_filter)
                )
                results = session.exec(query).all()
            
            faction_counter: Counter = Counter()
            pilot_counter: Counter = Counter()
            valid_lists = 0
            
            for r in results:
                xws = r.list_json
                if not xws or not isinstance(xws, dict):
                    continue
                
                valid_lists += 1
                
                # Normalize and validate faction
                faction_raw = xws.get("faction", "").lower().replace(" ", "").replace("-", "")
                
                # Only count if it's a known faction
                if faction_raw in self.FACTION_CONFIG:
                    faction_counter[faction_raw] += 1
                
                for pilot in xws.get("pilots", []):
                    pilot_id = pilot.get("id") or pilot.get("name", "unknown")
                    pilot_counter[pilot_id] += 1
            
            self.total_lists = valid_lists
            
            # Build faction chart data with icons
            self.faction_data = []
            for faction_key, count in faction_counter.most_common():
                name, color = self.FACTION_CONFIG[faction_key]
                icon_url = get_faction_icon(faction_key)
                self.faction_data.append({
                    "name": name,
                    "value": count,
                    "fill": color,
                    "icon": icon_url,
                })
            
            # Build pilot data with readable names from xwing-data2
            self.pilot_data = [
                {"name": get_pilot_name(p), "count": c}
                for p, c in pilot_counter.most_common(10)
            ]
    
    def set_format_filter(self, value: str):
        self.format_filter = value
        self.load_analytics()


def format_filter_select() -> rx.Component:
    """Dropdown to filter statistics by game format."""
    return rx.select(
        ["all", MacroFormat.V2_5.value, MacroFormat.V2_0.value, MacroFormat.OTHER.value],
        value=AnalyticsState.format_filter,
        on_change=AnalyticsState.set_format_filter,
        placeholder="Filter by Format",
    )



def render_faction_legend_item(item: dict):
    return rx.hstack(
        rx.cond(
            item["icon"],
            rx.image(src=item["icon"], width="24px", height="24px", object_fit="contain"),
            rx.box(width="24px", height="24px", bg=item["fill"], border_radius="50%"),
        ),
        rx.text(item["name"], weight="medium"),
        rx.badge(item["value"], variant="outline", color_scheme="gray"),
        spacing="2",
        align="center",
        padding="6px 12px",
        border_radius="4px",
        bg="rgba(26, 26, 36, 0.5)",
        border_left=f"3px solid {item['fill']}",
    )


def faction_chart() -> rx.Component:
    """Pie chart for faction distribution - Imperial style."""
    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.box(
                    width="4px",
                    height="20px",
                    background=IMPERIAL_BLUE,
                    border_radius="2px",
                ),
                rx.heading(
                    "FACTION DISTRIBUTION", 
                    size="5",
                    font_family="Orbitron, sans-serif",
                    letter_spacing="0.1em",
                ),
                spacing="3",
                align="center",
            ),
            rx.recharts.pie_chart(
                rx.recharts.pie(
                    data=AnalyticsState.faction_data,
                    data_key="value",
                    name_key="name",
                    cx="50%",
                    cy="50%",
                    label=True,
                    label_line=True,
                ),
                width="100%",
                height=300,
            ),
            rx.flex(
                rx.foreach(AnalyticsState.faction_data, render_faction_legend_item),
                wrap="wrap",
                spacing="3",
                justify="center",
                width="100%",
                margin_top="16px",
            ),
            align="center",
            width="100%",
        ),
        padding="24px",
        background=f"linear-gradient(180deg, rgba(26, 26, 36, 0.8) 0%, rgba(26, 26, 36, 0.4) 100%)",
        border_radius="4px",
        border=f"1px solid {STEEL_BORDER}",
    )


def pilot_chart() -> rx.Component:
    """Bar chart for top pilot usage - Imperial style."""
    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.box(
                    width="4px",
                    height="20px",
                    background=IMPERIAL_BLUE,
                    border_radius="2px",
                ),
                rx.heading(
                    "TOP 10 PILOTS", 
                    size="5",
                    font_family="Orbitron, sans-serif",
                    letter_spacing="0.1em",
                ),
                spacing="3",
                align="center",
            ),
            rx.recharts.bar_chart(
                rx.recharts.bar(
                    data_key="count",
                    fill=IMPERIAL_BLUE,
                ),
                rx.recharts.x_axis(data_key="name", angle=-45, text_anchor="end"),
                rx.recharts.y_axis(),
                data=AnalyticsState.pilot_data,
                width="100%",
                height=400,
                margin={"bottom": 100, "left": 20},
            ),
            align="center",
            width="100%",
        ),
        padding="24px",
        background=f"linear-gradient(180deg, rgba(26, 26, 36, 0.8) 0%, rgba(26, 26, 36, 0.4) 100%)",
        border_radius="4px",
        border=f"1px solid {STEEL_BORDER}",
    )


def analytics_content() -> rx.Component:
    """Main content layout - Imperial style."""
    return rx.vstack(
        # Header with filter
        rx.hstack(
            rx.vstack(
                rx.heading(
                    "META ANALYTICS", 
                    size="8",
                    font_family="Orbitron, sans-serif",
                    letter_spacing="0.15em",
                ),
                rx.box(
                    width="100px",
                    height="2px",
                    background=f"linear-gradient(90deg, {IMPERIAL_BLUE}, transparent)",
                    margin_top="4px",
                ),
                rx.text("Explore faction and pilot trends", size="3", color="#8a8a9a"),
                align="start",
            ),
            rx.spacer(),
            rx.hstack(
                format_filter_select(),
                rx.badge(
                    AnalyticsState.total_lists.to_string() + " lists",
                    color_scheme="blue",
                    size="2",
                ),
                spacing="3",
            ),
            width="100%",
            margin_bottom="24px",
        ),
        
        # Charts
        rx.grid(
            faction_chart(),
            pilot_chart(),
            columns="2",
            spacing="6",
            width="100%",
        ),
        
        align="start",
        width="100%",
        max_width="1200px",
        on_mount=AnalyticsState.load_analytics,
    )


def analytics_page() -> rx.Component:
    """Analytics page wrapped in layout."""
    return layout(analytics_content())

