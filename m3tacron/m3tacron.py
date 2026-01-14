"""
M3taCron - X-Wing Meta Analytics Platform.

Main application entry point.
"""
import reflex as rx

from rxconfig import config
from .pages.home import home_page
from .pages.tournaments import tournaments_page
from .pages.tournament_detail import tournament_detail_page
from .pages.analytics import analytics_page
from .backend.database import create_db_and_tables


# Custom theme with dark mode
theme = rx.theme(
    appearance="dark",
    accent_color="cyan",
    gray_color="slate",
    radius="medium",
)


# Create the app
app = rx.App(
    theme=theme,
    stylesheets=[
        # Google Fonts - Inter for clean typography
        "https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap",
    ],
    style={
        "font_family": "Inter, sans-serif",
        "background": "#0f172a",
        "color": "#e2e8f0",
    },
)

# Register pages
app.add_page(home_page, route="/", title="M3taCron - Meta Snapshot")
app.add_page(tournaments_page, route="/tournaments", title="M3taCron - Tournaments")
app.add_page(tournament_detail_page, route="/tournament/[id]", title="M3taCron - Tournament")
app.add_page(analytics_page, route="/analytics", title="M3taCron - Analytics")
