"""
M3taCron Tournament Detail Page - Imperial Data Terminal Spec.
"""
import reflex as rx
from sqlmodel import Session, select, func

from ..components.sidebar import layout
from ..components.ui import content_panel, stat_card
from ..backend.database import engine
from ..backend.models import Tournament, PlayerResult, Match
from ..backend.utils import parse_xws, get_faction_name, normalize_faction
from ..backend.utils import xws_to_yasb_url, get_xws_string
from ..theme import (
    TERMINAL_BG, BORDER_COLOR, TERMINAL_PANEL, TEXT_PRIMARY, TEXT_SECONDARY,
    MONOSPACE_FONT, SANS_FONT, TERMINAL_PANEL_STYLE, FACTION_COLORS,
)
from ..ui_utils.factions import get_faction_color
from ..components.card_tooltip import pilot_card_tooltip, upgrade_card_tooltip
from ..components.icons import xwing_icon


class TournamentDetailState(rx.State):
    """State for the Tournament Detail page."""
    tournament: dict = {}
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
                
                self.tournament = {
                    "id": t.id,
                    "name": t.name,
                    "date": t.date.strftime("%Y-%m-%d") if t.date else "Unknown",
                    "platform": t.platform,
                    "format": t.format,
                    "macro_format": t.macro_format,
                    "url": t.url,
                }
                
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
                self.matches = []
                for m in matches:
                    p1_id = m.player1_id
                    p2_id = m.player2_id
                    winner_id = m.winner_id
                    
                    # Determine result for coloring
                    # If draw or no winner, "neutral" or "draw"
                    p1_result = "draw"
                    p2_result = "draw"
                    
                    if winner_id:
                        if winner_id == p1_id:
                            p1_result = "win"
                            p2_result = "loss"
                        elif winner_id == p2_id:
                            p1_result = "loss"
                            p2_result = "win"
                            
                    self.matches.append({
                        "round": m.round_number,
                        "type": m.round_type,
                        "player1": player_map.get(m.player1_id, "Unknown"),
                        "player2": player_map.get(m.player2_id, "Bye") if not m.is_bye else "BYE",
                        "score1": m.player1_score,
                        "score2": m.player2_score,
                        "winner_id": m.winner_id,
                        "scenario": m.scenario,
                        "player1_first": m.first_player_id == m.player1_id if m.first_player_id else False,
                        "player2_first": m.first_player_id == m.player2_id if m.first_player_id else False,
                        "p1_result": p1_result,
                        "p2_result": p2_result,
                    })
                
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


# faction_icon was here - now using xwing_icon


def render_list_modal() -> rx.Component:
    """Render squadron list modal with faction icon, colors, and card tooltips."""
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title(
                rx.hstack(
                    # Faction icon + name with color
                    rx.hstack(
                        xwing_icon(TournamentDetailState.open_list_data["faction_xws"], size="24px", color=get_faction_color(TournamentDetailState.open_list_data["faction_xws"])),
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


# get_faction_color was here - now using theme.get_faction_color

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
                xwing_icon(player["faction_xws"], size="14px", color=get_faction_color(player["faction_xws"])),
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


def get_result_color(result: str | rx.Var) -> str | rx.Var:
    """Return color for win/loss/draw."""
    return rx.cond(result == "win", "#4CAF50",  # Green
           rx.cond(result == "loss", "#F44336",  # Red
           TEXT_PRIMARY))


def match_row(match: dict) -> rx.Component:
    """
    Revised Match Row Layout:
    [Round #] [Scenario Column (Fixed)] [Left Player P1] [Score] - [Score] [Right Player P2]
    """
    return rx.flex(
        # 1. Round Number (Fixed Width Left)
        rx.box(
            rx.text(match["round"], color=TEXT_SECONDARY, size="1", font_family=MONOSPACE_FONT),
            width="30px",
            display="flex", align_items="center", justify_content="center",
            border_right=f"1px solid {BORDER_COLOR}",
            padding_right="8px"
        ),
        
        # 2. Scenario Column (Fixed Width) - Empty if None but present
        rx.box(
            rx.cond(
                match["scenario"],
                rx.badge(match["scenario"], variant="outline", size="1", color_scheme="gray", style={"max-width": "100%", "overflow": "hidden", "text-overflow": "ellipsis", "white-space": "nowrap"}),
                rx.fragment() 
            ),
            width="120px",  # Fixed width for alignment
            padding_left="12px",
            padding_right="12px",
            display="flex", align_items="center", justify_content="start",
            border_right=f"1px solid {BORDER_COLOR}",
        ),
        
        # 3. Match Details Container (Flex Grow)
        rx.flex(
            # Left Side (Player 1)
            rx.hstack(
                # First Player Icon (Left of name)
                rx.cond(
                     match["player1_first"],
                     rx.text("♔", color="yellow", size="2"),
                     rx.box(width="18px") # Spacer
                ),
                rx.text(
                    match["player1"], 
                    size="2", 
                    color=get_result_color(match["p1_result"]), 
                    font_family=MONOSPACE_FONT,
                    weight="bold",
                    align="right"
                ),
                rx.text(match["score1"], size="2", color=TEXT_PRIMARY, font_family=MONOSPACE_FONT),
                spacing="3", 
                align="center",
                justify="end",
                width="45%" # Take up slightly less than half
            ),
            
            # Center Divider/Dash
            rx.box(
                 rx.text("-", size="2", color=TEXT_SECONDARY),
                 width="10%",
                 display="flex", justify_content="center"
            ),
            
            # Right Side (Player 2)
            rx.hstack(
                rx.text(match["score2"], size="2", color=TEXT_PRIMARY, font_family=MONOSPACE_FONT),
                rx.text(
                    match["player2"], 
                    size="2", 
                    color=get_result_color(match["p2_result"]),
                    font_family=MONOSPACE_FONT,
                    weight="bold",
                    align="left"
                ),
                # First Player Icon (Right of name)
                rx.cond(
                     match["player2_first"],
                     rx.text("♔", color="yellow", size="2"),
                     rx.box(width="18px")
                ),
                spacing="3",
                align="center",
                justify="start",
                width="45%"
            ),
            
            align="center",
            width="100%",
            padding_left="12px"
        ),
        
        width="100%",
        padding="8px 0px",
        border_bottom=f"1px solid {BORDER_COLOR}",
        align="center"
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
                            rx.heading(TournamentDetailState.tournament["name"], size="6", font_family=SANS_FONT, weight="bold"),
                            rx.hstack(
                                rx.badge(TournamentDetailState.tournament["macro_format"], color_scheme="gray"),
                                rx.text(TournamentDetailState.tournament["date"], size="2", color=TEXT_SECONDARY, font_family=MONOSPACE_FONT),
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
                        content_panel("RANKINGS", rx.vstack(rx.foreach(TournamentDetailState.players.to(list[dict]), player_row), spacing="0", width="100%")),
                        rx.cond(
                            TournamentDetailState.matches.length() > 0,
                            content_panel("MATCHES", rx.vstack(rx.foreach(TournamentDetailState.matches.to(list[dict]), match_row), spacing="0", width="100%")),
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
