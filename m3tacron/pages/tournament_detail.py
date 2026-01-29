"""
M3taCron Tournament Detail Page.
"""
import reflex as rx
from sqlmodel import Session, select, func

from ..components.sidebar import layout
from ..components.ui import content_panel as terminal_panel, stat_card
from ..backend.database import engine
from ..backend.models import Tournament, PlayerResult, Match
from ..backend.utils.xwing_data import parse_xws, get_faction_name, normalize_faction
from ..backend.utils.yasb import xws_to_yasb_url, get_xws_string
from ..theme import (
    TERMINAL_BG, BORDER_COLOR, TERMINAL_PANEL, TEXT_PRIMARY, TEXT_SECONDARY,
    MONOSPACE_FONT, SANS_FONT, TERMINAL_PANEL_STYLE, FACTION_COLORS
)
from ..components.card_tooltip import pilot_card_tooltip, upgrade_card_tooltip
from ..ui_utils.factions import faction_icon, get_faction_color


class TournamentDetailState(rx.State):
    """State for the Tournament Detail page."""
    tournament: Tournament | None = None
    players: list[dict] = []
    matches: list[dict] = []
    loading: bool = True
    error: str = ""
    
    open_list_id: int = 0
    open_list_data: dict = {}
    open_list_pilots: list[dict] = []
    open_list_xws: dict = {}
    yasb_url: str = ""
    
    def load_tournament(self):
        # Try multiple ways to get the tournament ID
        tournament_id_str = ""
        
        # Method 1: Try params dict
        if hasattr(self.router.page, "params") and isinstance(self.router.page.params, dict):
            tournament_id_str = self.router.page.params.get("id", "")
        
        # Method 2: Try from path segments
        if not tournament_id_str and hasattr(self.router.page, "raw_path"):
            path_parts = self.router.page.raw_path.split("/")
            if len(path_parts) >= 3 and path_parts[1] == "tournament":
                tournament_id_str = path_parts[2]
        
        if not tournament_id_str:
            self.error = "No tournament ID provided"
            self.loading = False
            return
        
        try:
            tournament_id = int(tournament_id_str)
        except ValueError:
            self.error = f"Invalid ID: {tournament_id_str}"
            self.loading = False
            return
        
        try:
            with Session(engine) as session:
                t = session.exec(select(Tournament).where(Tournament.id == tournament_id)).first()
                if not t:
                    self.error = "Tournament not found"
                    self.loading = False
                    return
                
                self.tournament = t
                
                players = session.exec(select(PlayerResult).where(PlayerResult.tournament_id == tournament_id).order_by(PlayerResult.rank)).all()
                self.players = []
                for p in players:
                    f_name, f_xws = self._extract_faction_data(p.list_json)
                    self.players.append({
                        "id": p.id,
                        "name": p.player_name,
                        "rank": p.rank,
                        "faction": f_name,
                        "faction_xws": f_xws,
                        "has_list": bool(p.list_json and isinstance(p.list_json, dict) and p.list_json.get("pilots")),
                        "xws": p.list_json if p.list_json else {},
                    })
                
                matches = session.exec(select(Match).where(Match.tournament_id == tournament_id).order_by(Match.round_number)).all()
                player_map = {p.id: p.player_name for p in players}
                self.matches = [{
                    "round": m.round_number,
                    "type": m.round_type,
                    "player1": player_map.get(m.player1_id, "Unknown"),
                    "player2": player_map.get(m.player2_id, "Bye") if not m.is_bye else "BYE",
                    "player1_id": m.player1_id,
                    "player2_id": m.player2_id,
                    "score1": m.player1_score,
                    "score2": m.player2_score,
                    "winner_id": m.winner_id,
                    "scenario": m.scenario,
                    "player1_first": m.first_player_id == m.player1_id if m.first_player_id else False,
                    "player2_first": m.first_player_id == m.player2_id if m.first_player_id else False,
                } for m in matches]
                
                self.loading = False
        except Exception as e:
            self.error = f"Error: {str(e)}"
            self.loading = False
    
    
    def _extract_faction_data(self, list_json: dict) -> tuple[str, str]:
        """Return (faction_name, faction_xws)."""
        if not list_json or not isinstance(list_json, dict): return "Unknown", "unknown"
        raw = list_json.get("faction", "Unknown")
        xws = normalize_faction(raw)
        name = get_faction_name(xws)
        return name, xws

    def open_list(self, player_id: int):
        self.open_list_id = player_id
        with Session(engine) as session:
            player = session.get(PlayerResult, player_id)
            if player and player.list_json:
                 # Store raw XWS for export/YASB
                 self.open_list_xws = player.list_json
                 # Parse for display
                 data = parse_xws(player.list_json)
                 
                 # Ensure faction XWS is available for UI logic
                 xws_faction = normalize_faction(player.list_json.get("faction", ""))
                 data["faction_xws"] = xws_faction
                 
                 self.open_list_data = data
                 # Generate YASB URL
                 tournament = session.exec(select(Tournament).where(Tournament.id == player.tournament_id)).first()
                 if tournament:
                     self.yasb_url = xws_to_yasb_url(player.list_json, tournament.format or "xwa")
                 pilots_list = []
                 for p in data.get("pilots", []):
                     upgrades_list = [{"name": u["name"], "type": u["type"], "xws": u.get("xws", "")} for u in p.get("upgrades", [])]
                     upgrades_text = ", ".join(u["name"] for u in p.get("upgrades", []))
                     pilots_list.append({
                         "name": p["name"],
                         "xws": p.get("xws", ""),
                         "ship": p["ship"],
                         "points": p["points"],
                         "upgrades": upgrades_list,
                         "upgrades_text": upgrades_text
                     })
                 self.open_list_pilots = pilots_list
            else:
                 self.open_list_data = {}
                 self.open_list_pilots = []
                 self.open_list_xws = {}
                 self.yasb_url = ""

    def close_list(self):
        self.open_list_id = 0
        self.open_list_data = {}
        self.open_list_pilots = []
        self.open_list_xws = {}
        self.yasb_url = ""

    def handle_open_change(self, is_open: bool):
        if not is_open: self.close_list()


def render_upgrade_item(upgrade: dict) -> rx.Component:
    """Render upgrade badge with card tooltip."""
    return upgrade_card_tooltip(
        rx.badge(upgrade["name"], variant="outline", color_scheme="gray", size="1"),
        upgrade["xws"],  # XWS ID from dict - Reflex Var
    )


def render_pilot_card(pilot: dict) -> rx.Component:
    """Render pilot card with ship, points, and upgrades with tooltips."""
    return rx.box(
        rx.hstack(
            rx.vstack(
                pilot_card_tooltip(
                    rx.text(
                        pilot["name"], 
                        weight="bold", 
                        size="3", 
                        _hover={"color": TEXT_PRIMARY, "cursor": "help", "text_decoration": "underline"}, 
                        font_family=MONOSPACE_FONT
                    ),
                    pilot["xws"],  # XWS ID from dict - Reflex Var
                ),
                rx.text(pilot["ship"], size="1", color=TEXT_SECONDARY, font_family=MONOSPACE_FONT),
                align="start", spacing="1"
            ),
            rx.spacer(),
            rx.badge(pilot["points"], color_scheme="gray", variant="outline"),
            width="100%", align="center", margin_bottom="8px"
        ),
        rx.cond(
            pilot["upgrades"].to(list[dict]).length() > 0,
            rx.flex(rx.foreach(pilot["upgrades"].to(list[dict]), render_upgrade_item), wrap="wrap", spacing="2"),
            rx.text("NO UPGRADES", size="1", color=TEXT_SECONDARY, font_family=MONOSPACE_FONT),
        ),
        padding="12px",
        style=TERMINAL_PANEL_STYLE,
        width="100%",
    )




def render_list_modal() -> rx.Component:
    """Render squadron list modal with faction icon, colors, and card tooltips."""
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title(
                rx.hstack(
                    # Faction icon + name with color
                    rx.hstack(
                        faction_icon(TournamentDetailState.open_list_data["faction_xws"]),
                        rx.text(
                            TournamentDetailState.open_list_data["faction"], 
                            size="4", 
                            font_family=SANS_FONT, 
                            weight="bold"
                        ),
                        spacing="2",
                        align="center",
                    ),
                    rx.spacer(),
                    rx.cond(
                         TournamentDetailState.open_list_data.contains("points"),
                         rx.text(TournamentDetailState.open_list_data["points"].to_string() + " PTS", font_family=MONOSPACE_FONT),
                         rx.fragment()
                    ),
                    width="100%", align="center"
                ),
            ),
            rx.dialog.description(
                rx.vstack(rx.foreach(TournamentDetailState.open_list_pilots, render_pilot_card), spacing="3", margin_top="16px"),
            ),
            rx.flex(
                rx.cond(
                    TournamentDetailState.yasb_url != "",
                    rx.link(
                        rx.button("VIEW ON YASB", variant="outline", color_scheme="blue", style={"font_family": MONOSPACE_FONT}),
                        href=TournamentDetailState.yasb_url,
                        is_external=True,
                    ),
                    rx.fragment(),
                ),
                rx.button(
                    "COPY XWS",
                    variant="outline",
                    color_scheme="gray",
                    on_click=rx.set_clipboard(TournamentDetailState.open_list_xws.to_string()),
                    style={"font_family": MONOSPACE_FONT}
                ),
                rx.dialog.close(rx.button("CLOSE", variant="soft", color_scheme="gray", on_click=TournamentDetailState.close_list)),
                justify="end", margin_top="16px", spacing="2"
            ),
            max_width="600px",
            background=TERMINAL_BG,
            border=f"1px solid {BORDER_COLOR}",
        ),
        open=TournamentDetailState.open_list_id != 0,
        on_open_change=TournamentDetailState.handle_open_change,
    )



def player_row(player: dict) -> rx.Component:
    return rx.hstack(
        rx.badge(
            player["rank"], 
            style={"background_color": get_faction_color(player["faction_xws"])}, 
            size="2", 
            variant="solid"
        ),
        rx.vstack(
            rx.text(player["name"], size="2", weight="medium", font_family=MONOSPACE_FONT, color=TEXT_PRIMARY),
            rx.hstack(
                # Faction Icon + Colored Text
                faction_icon(player["faction_xws"], size="14px"),
                rx.text(
                    player["faction"], 
                    size="1", 
                    color=get_faction_color(player["faction_xws"]), 
                    font_family=MONOSPACE_FONT,
                    weight="bold"
                ), 
                spacing="2",
                align="center",
                # Hide if unknown faction to keep clean
                display=rx.cond(player["faction_xws"] == "unknown", "none", "flex")
            ),
            spacing="1", align="start"
        ),
        rx.spacer(),
        rx.cond(
            player["has_list"],
            rx.button("LIST", variant="outline", size="1", on_click=TournamentDetailState.open_list(player["id"]), style={"font_family": MONOSPACE_FONT}),
            rx.fragment(),
        ),
        width="100%",
        padding="8px 12px",
        border_bottom=f"1px solid {BORDER_COLOR}",
        _hover={"background": "rgba(255, 255, 255, 0.05)"},
    )


def match_row(match: dict) -> rx.Component:
    """
    Render a match row with:
    [Round] [Scenario Space] [P1 Name + Score -- Score + P2 Name]
    """
    # Color logic: Green for winner, Red for loser
    p1_color = rx.cond(match["winner_id"] == match["player1_id"], "green", "red")
    p2_color = rx.cond(match["winner_id"] == match["player2_id"], "green", "red")
    
    return rx.hstack(
        # 1. Round Number
        rx.text(match["round"], color=TEXT_SECONDARY, size="1", font_family=MONOSPACE_FONT, width="30px"),
        
        # 2. Scenario Space (Fixed width, always present)
        rx.box(
            rx.cond(
                match["scenario"],
                rx.badge(match["scenario"], variant="outline", size="1", color_scheme="gray"),
                rx.fragment()
            ),
            width="120px", # Fixed space for scenario
            display="flex",
            align_items="center",
            justify_content="center",
        ),
        
        # 3. Match Sub-container
        rx.hstack(
            # Player 1 (Left)
            rx.hstack(
                rx.icon(tag="user", size=14, color=TEXT_SECONDARY), # Icon for P1
                rx.text(
                    match["player1"], 
                    size="2", 
                    color=p1_color, 
                    font_family=MONOSPACE_FONT,
                    weight="medium",
                    text_align="left",
                    width="100%"
                ),
                rx.cond(
                     match["player1_first"],
                     rx.badge("1st", variant="solid", color_scheme="yellow", size="1"),
                     rx.fragment()
                ),
                 width="40%", # Allocate space for name
                 justify="start",
                 align="center",
                 spacing="2"
            ),
            
            # Scores (Center)
            rx.hstack(
                rx.text(match["score1"], size="2", color=p1_color, font_family=MONOSPACE_FONT, weight="bold"),
                rx.text("-", size="2", color=TEXT_SECONDARY),
                rx.text(match["score2"], size="2", color=p2_color, font_family=MONOSPACE_FONT, weight="bold"),
                justify="center",
                width="20%",
                align="center",
                spacing="2"
            ),

            # Player 2 (Right)
            rx.hstack(
                rx.cond(
                     match["player2_first"],
                     rx.badge("1st", variant="solid", color_scheme="yellow", size="1"),
                     rx.fragment()
                ),
                rx.text(
                    match["player2"], 
                    size="2", 
                    color=p2_color, 
                    font_family=MONOSPACE_FONT,
                    weight="medium",
                    text_align="right",
                    width="100%"
                ),
                width="40%", # Allocate space for name
                justify="end",
                align="center",
                spacing="2"
            ),
            
            flex="1", # Take remaining space
            align="center",
            justify="between",
            style={"background_color": "rgba(255, 255, 255, 0.02)", "border_radius": "4px", "padding": "4px 8px"}
        ),
        
        width="100%", 
        padding="8px 12px", 
        border_bottom=f"1px solid {BORDER_COLOR}", 
        align="center",
        spacing="4"
    )


def tournament_detail_content() -> rx.Component:
    return rx.vstack(
        render_list_modal(),
        rx.cond(
            TournamentDetailState.loading,
            rx.spinner(),
            rx.cond(
                TournamentDetailState.error != "",
                rx.text(TournamentDetailState.error, color="red"),
                rx.vstack(
                    rx.hstack(
                        rx.link(rx.button("< BACK", variant="ghost", size="1", style={"font_family": MONOSPACE_FONT}), href="/tournaments"),
                        rx.vstack(
                            rx.heading(TournamentDetailState.tournament.name, size="6", font_family=SANS_FONT, weight="bold"),
                            rx.hstack(
                                rx.badge(TournamentDetailState.tournament.format.macro.value, color_scheme="gray"),
                                rx.text(TournamentDetailState.tournament.date.to(str), size="2", color=TEXT_SECONDARY, font_family=MONOSPACE_FONT),
                                spacing="2",
                            ),
                            align="start", spacing="2",
                        ),
                        spacing="4", width="100%", margin_bottom="24px",
                    ),
                    rx.hstack(
                        stat_card("PLAYERS", TournamentDetailState.players.length()),
                        stat_card("ROUNDS", TournamentDetailState.matches.length()),
                        margin_bottom="24px",
                    ),
                    rx.grid(
                        terminal_panel("RANKINGS", rx.vstack(rx.foreach(TournamentDetailState.players.to(list[dict]), player_row), spacing="0", width="100%")),
                        rx.cond(
                            TournamentDetailState.matches.length() > 0,
                            terminal_panel("MATCHES", rx.vstack(rx.foreach(TournamentDetailState.matches.to(list[dict]), match_row), spacing="0", width="100%")),
                            rx.fragment(),
                        ),
                        columns="2", spacing="6", width="100%",
                    ),
                    width="100%", max_width="1200px",
                )
            ),
        ),
        align="start", width="100%", padding_bottom="60px",
        on_mount=TournamentDetailState.load_tournament,
    )


def tournament_detail_page() -> rx.Component:
    return layout(tournament_detail_content())
