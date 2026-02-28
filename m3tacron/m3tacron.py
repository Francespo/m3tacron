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
    head_components=[
        rx.el.meta(name="viewport", content="width=device-width, initial-scale=1"),
        rx.el.meta(name="description", content="M3taCron - X-Wing Miniatures Meta Analytics Platform. Discover the competitive landscape, ship stats, and tournament results for AMG, XWA, and Legacy formats."),
        rx.el.meta(property="og:title", content="M3taCron - X-Wing Meta Analytics"),
        rx.el.meta(property="og:description", content="Superior meta analytics for the X-Wing Miniatures game. Tracking AMG, XWA, and Legacy formats."),
        rx.el.meta(property="og:type", content="website"),
    ],
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
    },
)

# Register pages
app.add_page(home_page, route="/", title="M3taCron - Meta Snapshot")
app.add_page(tournaments_browser_page, route="/tournaments", title="M3taCron - Tournaments Browser")
app.add_page(tournament_detail_page, route="/tournament/[id]", title="M3taCron - Tournament")

# from .pages.squadrons_browser import squadrons_browser_page
from .pages.cards_browser import cards_browser_page
from .pages.ships_browser import ships_browser_page

app.add_page(squadrons_browser_page, route="/squadrons", title="M3taCron - Squadrons Browser")
app.add_page(cards_browser_page, route="/cards", title="M3taCron - Cards Browser")
app.add_page(ships_browser_page, route="/ships", title="M3taCron - Ships Browser")

from .pages.list_browser import list_browser
app.add_page(list_browser, route="/lists", title="M3taCron - List Browser")

from .pages.pilot_detail import pilot_detail_page
from .pages.upgrade_detail import upgrade_detail_page
app.add_page(pilot_detail_page, route="/pilot/[id]", title="M3taCron - Pilot Detail")
app.add_page(upgrade_detail_page, route="/upgrade/[id]", title="M3taCron - Upgrade Detail")


