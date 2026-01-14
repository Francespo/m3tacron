"""
Analytics Page - Visualizes X-Wing meta statistics.

Provides aggregated views of faction popularity and pilot usage across
all imported tournaments, with optional filtering by format.
"""
import reflex as rx
from sqlmodel import Session, select
from collections import Counter
from typing import Dict, List, Any

from ..components.sidebar import layout
from ..backend.database import engine
from ..backend.models import PlayerResult


class AnalyticsState(rx.State):
    """Manages statistics aggregation and chart data for the Analytics page."""
    
    faction_data: List[Dict[str, Any]] = []
    pilot_data: List[Dict[str, Any]] = []
    total_lists: int = 0
    format_filter: str = "all"
    
    # Faction display names and colors
    FACTION_MAP = {
        "rebelalliance": ("Rebel Alliance", "#e74c3c"),
        "galacticempire": ("Galactic Empire", "#3498db"),
        "scumandvillainy": ("Scum and Villainy", "#f39c12"),
        "resistance": ("Resistance", "#e91e63"),
        "firstorder": ("First Order", "#9c27b0"),
        "galacticrepublic": ("Galactic Republic", "#8bc34a"),
        "separatistalliance": ("Separatist Alliance", "#607d8b"),
    }
    
    def load_analytics(self):
        """Fetches player lists and computes faction/pilot statistics."""
        with Session(engine) as session:
            results = session.exec(select(PlayerResult)).all()
            
            faction_counter: Counter = Counter()
            pilot_counter: Counter = Counter()
            valid_lists = 0
            
            for r in results:
                xws = r.list_json
                if not xws or not isinstance(xws, dict):
                    continue
                
                valid_lists += 1
                
                # Count faction
                faction_raw = xws.get("faction", "unknown").lower().replace(" ", "")
                faction_counter[faction_raw] += 1
                
                # Count pilots
                for pilot in xws.get("pilots", []):
                    pilot_id = pilot.get("id") or pilot.get("name", "unknown")
                    pilot_counter[pilot_id] += 1
            
            self.total_lists = valid_lists
            
            # Build faction chart data
            self.faction_data = []
            for faction_key, count in faction_counter.most_common():
                name, color = self.FACTION_MAP.get(faction_key, (faction_key.title(), "#95a5a6"))
                self.faction_data.append({
                    "name": name,
                    "value": count,
                    "fill": color,
                })
            
            # Build pilot chart data (top 10)
            self.pilot_data = [
                {"name": self._prettify_pilot(p), "count": c}
                for p, c in pilot_counter.most_common(10)
            ]
    
    def _prettify_pilot(self, pilot_id: str) -> str:
        """Converts pilot IDs to readable names."""
        # Simple heuristic: replace hyphens with spaces and title case
        return pilot_id.replace("-", " ").replace("_", " ").title()
    
    def set_format_filter(self, value: str):
        self.format_filter = value
        self.load_analytics()


def faction_chart() -> rx.Component:
    """Pie chart showing faction distribution."""
    return rx.box(
        rx.vstack(
            rx.heading("Faction Distribution", size="5"),
            rx.recharts.pie_chart(
                rx.recharts.pie(
                    data=AnalyticsState.faction_data,
                    data_key="value",
                    name_key="name",
                    cx="50%",
                    cy="50%",
                    label=True,
                ),
                rx.recharts.legend(),
                width="100%",
                height=350,
            ),
            align="center",
            width="100%",
        ),
        padding="24px",
        background="rgba(255, 255, 255, 0.03)",
        border_radius="12px",
        border="1px solid rgba(255, 255, 255, 0.08)",
    )


def pilot_chart() -> rx.Component:
    """Bar chart showing top pilots by usage."""
    return rx.box(
        rx.vstack(
            rx.heading("Top 10 Pilots", size="5"),
            rx.recharts.bar_chart(
                rx.recharts.bar(
                    data_key="count",
                    fill="#00bcd4",
                ),
                rx.recharts.x_axis(data_key="name", angle=-45, text_anchor="end"),
                rx.recharts.y_axis(),
                data=AnalyticsState.pilot_data,
                width="100%",
                height=350,
            ),
            align="center",
            width="100%",
        ),
        padding="24px",
        background="rgba(255, 255, 255, 0.03)",
        border_radius="12px",
        border="1px solid rgba(255, 255, 255, 0.08)",
    )


def analytics_content() -> rx.Component:
    """Main content layout for the Analytics page."""
    return rx.vstack(
        # Header
        rx.hstack(
            rx.vstack(
                rx.heading("Meta Analytics", size="8"),
                rx.text("Explore faction and pilot trends across tournaments", size="3", color="gray"),
                align="start",
            ),
            rx.spacer(),
            rx.badge(
                AnalyticsState.total_lists.to_string() + " lists analyzed",
                color_scheme="cyan",
                size="2",
            ),
            width="100%",
            margin_bottom="24px",
        ),
        
        # Charts Grid
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
    """The Analytics page wrapped in the layout."""
    return layout(analytics_content())
