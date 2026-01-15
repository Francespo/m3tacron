"""
M3taCron Tournament Detail Page - View single tournament with players and matches.
"""
import reflex as rx
from sqlmodel import Session, select, func

from ..components.sidebar import layout
from ..backend.database import engine
from ..backend.models import Tournament, PlayerResult, Match

from ..backend.xwing_data import parse_xws

class UpgradeItem(rx.Base):
    """Model for a single upgrade."""
    name: str
    type: str
    xws: str = ""

class PilotItem(rx.Base):
    """Model for a pilot card."""
    name: str
    ship: str
    points: int
    upgrades: list[UpgradeItem]

class TournamentDetailState(rx.State):
    """State for the Tournament Detail page."""
    # Note: 'id' is automatically provided by Reflex from the /tournament/[id] route
    
    tournament: dict = {}
    players: list[dict] = []
    matches: list[dict] = []
    loading: bool = True
    error: str = ""
    
    # List View State
    open_list_id: int = 0
    open_list_data: dict = {}
    open_list_pilots: list[PilotItem] = []
    
    def load_tournament(self):
        """Load tournament data from URL parameter."""
        # In Reflex, dynamic route segments like [id] are automatically 
        # populated as state variables, not read from router.page.params
        tournament_id_str = self.id
        
        if not tournament_id_str:
            self.error = "No tournament ID provided"
            self.loading = False
            return
        
        try:
            tournament_id = int(tournament_id_str)
        except ValueError:
            self.error = f"Invalid tournament ID: {tournament_id_str}"
            self.loading = False
            return
        
        try:
            with Session(engine) as session:
                # Fetch tournament
                t = session.exec(
                    select(Tournament).where(Tournament.id == tournament_id)
                ).first()
                
                if not t:
                    self.error = "Tournament not found"
                    self.loading = False
                    return
                
                self.tournament = {
                    "id": t.id,
                    "name": t.name,
                    "date": t.date.strftime("%Y-%m-%d") if t.date else "Unknown Date",
                    "platform": t.platform,
                    "format": t.format,
                    "macro_format": t.macro_format,
                    "sub_format": t.sub_format,
                    "url": t.url,
                }
                
                # Fetch players ordered by rank
                players = session.exec(
                    select(PlayerResult)
                    .where(PlayerResult.tournament_id == tournament_id)
                    .order_by(PlayerResult.rank)
                ).all()
                
                self.players = [{
                    "id": p.id,
                    "name": p.player_name,
                    "rank": p.rank,
                    "faction": self._extract_faction(p.list_json),
                    "has_list": bool(p.list_json and isinstance(p.list_json, dict) and p.list_json.get("pilots")),
                } for p in players]
                
                # Fetch matches
                matches = session.exec(
                    select(Match)
                    .where(Match.tournament_id == tournament_id)
                    .order_by(Match.round_number)
                ).all()
                
                # Build match data with player names
                player_map = {p.id: p.player_name for p in players}
                self.matches = [{
                    "round": m.round_number,
                    "type": m.round_type,
                    "player1": player_map.get(m.player1_id, "Unknown"),
                    "player2": player_map.get(m.player2_id, "Bye") if not m.is_bye else "BYE",
                    "score1": m.player1_score,
                    "score2": m.player2_score,
                    "winner_id": m.winner_id,
                } for m in matches]
                
                self.loading = False
        except Exception as e:
            self.error = f"Error loading tournament: {str(e)}"
            self.loading = False
    
    def _extract_faction(self, list_json: dict) -> str:
        """Extract faction from XWS list."""
        if not list_json or not isinstance(list_json, dict):
            return "Unknown"
        faction = list_json.get("faction", "Unknown")
        # Prettify faction names
        faction_map = {
            "rebelalliance": "Rebel Alliance",
            "galacticempire": "Galactic Empire",
            "scumandvillainy": "Scum and Villainy",
            "resistance": "Resistance",
            "firstorder": "First Order",
            "galacticrepublic": "Galactic Republic",
            "separatistalliance": "Separatist Alliance",
        }
        return faction_map.get(faction.lower().replace(" ", ""), faction)

    def open_list(self, player_id: int):
        """Open the list view modal for a player."""
        self.open_list_id = player_id
        with Session(engine) as session:
            player = session.get(PlayerResult, player_id)
            if player and player.list_json:
                 # Parse the raw JSON into our rich structure
                 data = parse_xws(player.list_json)
                 self.open_list_data = data
                 
                 # Convert to Pydantic models
                 pilots_list = []
                 for p in data.get("pilots", []):
                     upgrades_list = [
                         UpgradeItem(name=u["name"], type=u["type"], xws=u.get("xws", ""))
                         for u in p.get("upgrades", [])
                     ]
                     pilots_list.append(
                         PilotItem(
                             name=p["name"],
                             ship=p["ship"],
                             points=p["points"],
                             upgrades=upgrades_list
                         )
                     )
                 self.open_list_pilots = pilots_list
            else:
                 self.open_list_data = {}
                 self.open_list_pilots = []

    def close_list(self):
        """Close the list view modal."""
        self.open_list_id = 0
        self.open_list_data = {}
        self.open_list_pilots = []

    def handle_open_change(self, is_open: bool):
        """Handle dialog open state change."""
        if not is_open:
            self.close_list()


def render_pilot_card(pilot: PilotItem) -> rx.Component:
    """Render a single pilot with upgrades."""
    return rx.box(
        rx.hstack(
            # Pilot Info
            rx.vstack(
                rx.text(pilot.name, weight="bold", size="3"),
                rx.text(pilot.ship, size="1", color="gray"),
                align="start",
                spacing="1",
            ),
            rx.spacer(),
            # Points
            rx.badge(pilot.points.to_string(), color_scheme="gray", variant="outline"),
            width="100%",
            align="center",
            margin_bottom="8px",
        ),
        # Upgrades
        rx.flex(
            rx.foreach(
                pilot.upgrades,
                lambda u: rx.badge(
                    u.name, 
                    color_scheme="gray", 
                    variant="soft",
                    padding="4px 8px",
                )
            ),
            wrap="wrap",
            gap="4px",
        ),
        padding="12px",
        background="rgba(255, 255, 255, 0.05)",
        border_radius="6px",
        width="100%",
    )


def render_list_modal() -> rx.Component:
    """Render the modal for viewing a squad list."""
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title(
                rx.hstack(
                    rx.text(TournamentDetailState.open_list_data["faction"], size="4"),
                    rx.spacer(),
                    # Safety check for points
                    rx.cond(
                         TournamentDetailState.open_list_data.contains("points"),
                         rx.badge(
                            TournamentDetailState.open_list_data["points"].to_string() + " pts", 
                            color_scheme="yellow", 
                            size="3"
                        ),
                        rx.fragment()
                    ),
                    width="100%",
                    align="center",
                ),
            ),
            rx.dialog.description(
                rx.vstack(
                   rx.foreach(
                       TournamentDetailState.open_list_pilots,
                       render_pilot_card
                   ),
                   spacing="3",
                   margin_top="16px",
                ),
            ),
            rx.flex(
                rx.dialog.close(
                    rx.button(
                        "Close", 
                        variant="soft", 
                        color_scheme="gray",
                        on_click=TournamentDetailState.close_list,
                    ),
                ),
                justify="end",
                margin_top="16px",
            ),
            max_width="500px",
        ),
        open=TournamentDetailState.open_list_id != 0,
        on_open_change=TournamentDetailState.handle_open_change,
    )


def player_row(player: dict) -> rx.Component:
    """A row displaying player info."""
    return rx.hstack(
        rx.badge(
            player["rank"],
            color_scheme="cyan",
            size="2",
            variant="soft",
        ),
        rx.vstack(
            rx.text(player["name"], size="3", weight="medium"),
            rx.text(player["faction"], size="1", color="gray"),
            spacing="1",
            align="start",
        ),
        rx.spacer(),
        rx.cond(
            player["has_list"],
            rx.button(
                "View List",
                rx.icon("file-text", size=16),
                size="1", 
                variant="outline",
                on_click=TournamentDetailState.open_list(player["id"]),
            ),
            rx.fragment(),
        ),
        width="100%",
        padding="12px 16px",
        background="rgba(255, 255, 255, 0.02)",
        border_radius="8px",
        _hover={"background": "rgba(255, 255, 255, 0.05)"},
    )


def match_row(match: dict) -> rx.Component:
    """A row displaying match result."""
    return rx.hstack(
        rx.badge(
            match["round"],
            color_scheme="purple",
            size="1",
        ),
        rx.text(match["player1"], size="2", weight="medium"),
        rx.hstack(
            rx.text(match["score1"], size="2", color="cyan"),
            rx.text("-", size="2", color="gray"),
            rx.text(match["score2"], size="2", color="cyan"),
            spacing="1",
        ),
        rx.text(match["player2"], size="2", weight="medium"),
        width="100%",
        padding="8px 12px",
        background="rgba(255, 255, 255, 0.02)",
        border_radius="6px",
        justify="between",
    )


def tournament_detail_content() -> rx.Component:
    """The main content for the Tournament Detail page."""
    return rx.vstack(
        # Modal
        render_list_modal(),
        
        # Loading state
        rx.cond(
            TournamentDetailState.loading,
            rx.center(
                rx.spinner(size="3"),
                padding="64px",
            ),
            rx.fragment(),
        ),
        
        # Error state
        rx.cond(
            TournamentDetailState.error != "",
            rx.center(
                rx.vstack(
                    rx.icon("circle-alert", size=48, color="red"),
                    rx.text(TournamentDetailState.error, color="red"),
                    rx.link(
                        rx.button("Back to Tournaments", variant="outline"),
                        href="/tournaments",
                    ),
                    spacing="4",
                    align="center",
                ),
                padding="64px",
            ),
            rx.fragment(),
        ),
        
        # Main content
        rx.cond(
            (TournamentDetailState.loading == False) & (TournamentDetailState.error == ""),
            rx.vstack(
                # Header
                rx.hstack(
                    rx.link(
                        rx.button(rx.icon("arrow-left", size=16), variant="ghost", size="1"),
                        href="/tournaments",
                    ),
                    rx.vstack(
                        rx.heading(TournamentDetailState.tournament["name"], size="7"),
                        rx.hstack(
                            rx.badge(TournamentDetailState.tournament["macro_format"], color_scheme="purple"),
                            rx.badge(TournamentDetailState.tournament["sub_format"], color_scheme="cyan", variant="outline"),
                            rx.badge(TournamentDetailState.tournament["platform"], color_scheme="blue", variant="soft"),
                            rx.text(TournamentDetailState.tournament["date"], size="2", color="gray"),
                            spacing="2",
                        ),
                        align="start",
                        spacing="2",
                    ),
                    spacing="4",
                    width="100%",
                    margin_bottom="24px",
                ),
                
                # Stats
                rx.hstack(
                    rx.box(
                        rx.vstack(
                            rx.text("Players", size="1", color="gray"),
                            rx.text(TournamentDetailState.players.length(), size="5", weight="bold", color="cyan"),
                            spacing="1",
                        ),
                        padding="16px",
                        background="rgba(255, 255, 255, 0.03)",
                        border_radius="8px",
                    ),
                    rx.box(
                        rx.vstack(
                            rx.text("Rounds", size="1", color="gray"),
                            rx.text(TournamentDetailState.matches.length(), size="5", weight="bold", color="cyan"),
                            spacing="1",
                        ),
                        padding="16px",
                        background="rgba(255, 255, 255, 0.03)",
                        border_radius="8px",
                    ),
                    rx.link(
                        rx.button(
                            rx.icon("external-link", size=14),
                            "View Source",
                            variant="outline",
                            size="2",
                        ),
                        href=TournamentDetailState.tournament["url"],
                        is_external=True,
                    ),
                    spacing="4",
                    margin_bottom="24px",
                ),
                
                # Two columns: Players and Matches
                rx.grid(
                    # Players list
                    rx.box(
                        rx.vstack(
                            rx.heading("Players", size="5", margin_bottom="12px"),
                            rx.foreach(TournamentDetailState.players, player_row),
                            align="stretch",
                            width="100%",
                        ),
                        padding="20px",
                        background="rgba(255, 255, 255, 0.03)",
                        border_radius="12px",
                        border="1px solid rgba(255, 255, 255, 0.08)",
                    ),
                    # Matches (if available)
                    rx.cond(
                        TournamentDetailState.matches.length() > 0,
                        rx.box(
                            rx.vstack(
                                rx.heading("Matches", size="5", margin_bottom="12px"),
                                rx.foreach(TournamentDetailState.matches, match_row),
                                align="stretch",
                                width="100%",
                            ),
                            padding="20px",
                            background="rgba(255, 255, 255, 0.03)",
                            border_radius="12px",
                            border="1px solid rgba(255, 255, 255, 0.08)",
                        ),
                        rx.fragment(),
                    ),
                    columns="2",
                    spacing="6",
                    width="100%",
                ),
                
                align="start",
                width="100%",
                max_width="1100px",
            ),
            rx.fragment(),
        ),
        
        align="start",
        width="100%",
        on_mount=TournamentDetailState.load_tournament,
    )


def tournament_detail_page() -> rx.Component:
    """The Tournament Detail page wrapped in the layout."""
    return layout(tournament_detail_content())
