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


# Custom theme with dark mode - Star Wars Imperial style
theme = rx.theme(
    appearance="dark",
    accent_color="blue",
    gray_color="slate",
    radius="medium",
    scaling="100%",
)


# Create the app
app = rx.App(
    theme=theme,
    stylesheets=[
        # Google Fonts - Orbitron for sci-fi headers, Inter for body
        "https://fonts.googleapis.com/css2?family=Orbitron:wght@500;600;700;800;900&family=Inter:wght@400;500;600;700&display=swap",
    ],
    style={
        "font_family": "Inter, sans-serif",
        "background_color": "#0a0a0f",
        "background_image": """
            linear-gradient(rgba(42, 42, 58, 0.03) 1px, transparent 1px),
            linear-gradient(90deg, rgba(42, 42, 58, 0.03) 1px, transparent 1px),
            radial-gradient(circle at 20% 80%, rgba(79, 184, 255, 0.08), transparent 30%),
            radial-gradient(circle at 80% 20%, rgba(255, 71, 87, 0.05), transparent 30%)
        """,
        "background_size": "50px 50px, 50px 50px, 100% 100%, 100% 100%",
        "color": "#e8e8e8",
    },
)

# Register pages
app.add_page(home_page, route="/", title="M3taCron - Meta Snapshot")
app.add_page(tournaments_page, route="/tournaments", title="M3taCron - Tournaments")
app.add_page(tournament_detail_page, route="/tournament/[id]", title="M3taCron - Tournament")
app.add_page(analytics_page, route="/analytics", title="M3taCron - Analytics")
