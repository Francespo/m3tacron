"""
M3taCron - X-Wing Meta Analytics Platform.

Main application entry point.
"""
import reflex as rx

from rxconfig import config
from .pages.home import home_page
from .pages.tournaments_browser import tournaments_browser_page
from .pages.tournament_detail import tournament_detail_page

from .pages.squadrons_browser import squadrons_browser_page
from .pages.cards_browser import cards_browser_page
from .backend.database import create_db_and_tables


# Custom theme with dark mode - Functional Sci-Fi style
theme = rx.theme(
    appearance="dark",
    accent_color="gray",
    gray_color="gray",
    radius="none",  # Sharp edges everywhere
    scaling="100%",
)


# Create the app
app = rx.App(
    theme=theme,
    stylesheets=[
        # Google Fonts - JetBrains Mono for body, Orbitron for headers
        "https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600;700&family=Orbitron:wght@500;600;700;800;900&display=swap",
        "https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap", # Added Inter
        # X-Wing Miniatures Font integration
        "/global.css",
        "/xwing-miniatures-font_LINK/xwing-miniatures.css",
    ],
    style={
        "font_family": "'JetBrains Mono', 'Roboto Mono', monospace",
        "background_color": "#000000", # Pure Black
        "color": "#FFFFFF",
        "overflow": "hidden", # Prevent global scrollbar
    },
)

# Register pages
app.add_page(home_page, route="/", title="M3taCron - Meta Snapshot")
app.add_page(tournaments_browser_page, route="/tournaments", title="M3taCron - Tournaments Browser")
app.add_page(tournament_detail_page, route="/tournament/[id]", title="M3taCron - Tournament")

# from .pages.squadrons_browser import squadrons_browser_page
from .pages.cards_browser import cards_browser_page

app.add_page(squadrons_browser_page, route="/squadrons", title="M3taCron - Squadrons Browser")
app.add_page(cards_browser_page, route="/cards", title="M3taCron - Cards Browser")

from .pages.pilot_detail import pilot_detail_page
from .pages.upgrade_detail import upgrade_detail_page
app.add_page(pilot_detail_page, route="/pilot/[id]", title="M3taCron - Pilot Detail")
app.add_page(upgrade_detail_page, route="/upgrade/[id]", title="M3taCron - Upgrade Detail")

