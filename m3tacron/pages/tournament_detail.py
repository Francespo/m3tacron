"""
M3taCron Tournament Detail Page - Imperial Data Terminal Spec.
"""
import reflex as rx
from sqlmodel import Session, select, func

from ..components.sidebar import layout
from ..components.ui import terminal_panel, stat_card
from ..backend.database import engine
from ..backend.models import Tournament, PlayerResult, Match
from ..backend.xwing_data import parse_xws
from ..theme import (
    TERMINAL_BG, BORDER_COLOR, TERMINAL_PANEL, TEXT_PRIMARY, TEXT_SECONDARY,
    MONOSPACE_FONT, SANS_FONT, TERMINAL_PANEL_STYLE, FACTION_COLORS
)
from ..components.card_tooltip import pilot_card_tooltip, upgrade_card_tooltip


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
    
    def load_tournament(self):
        tournament_id_str = self.router.page.params.get("id", "")
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
                    "sub_format": t.sub_format,
                    "url": t.url,
                }
                
                players = session.exec(select(PlayerResult).where(PlayerResult.tournament_id == tournament_id).order_by(PlayerResult.rank)).all()
                self.players = [{
                    "id": p.id,
                    "name": p.player_name,
                    "rank": p.rank,
                    "faction": self._extract_faction(p.list_json),
                    "has_list": bool(p.list_json and isinstance(p.list_json, dict) and p.list_json.get("pilots")),
                } for p in players]
                
                matches = session.exec(select(Match).where(Match.tournament_id == tournament_id).order_by(Match.round_number)).all()
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
            self.error = f"Error: {str(e)}"
            self.loading = False
    
    def _extract_faction(self, list_json: dict) -> str:
        if not list_json or not isinstance(list_json, dict): return "Unknown"
        return list_json.get("faction", "Unknown").capitalize()

    def open_list(self, player_id: int):
        self.open_list_id = player_id
        with Session(engine) as session:
            player = session.get(PlayerResult, player_id)
            if player and player.list_json:
                 data = parse_xws(player.list_json)
                 self.open_list_data = data
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
                 self.open_list_pilots = [] # Fixed from list literal in original check?

    def close_list(self):
        self.open_list_id = 0
        self.open_list_data = {}
        self.open_list_pilots = []

    def handle_open_change(self, is_open: bool):
        if not is_open: self.close_list()


def render_upgrade_item(upgrade: dict) -> rx.Component:
    return upgrade_card_tooltip(
        rx.badge(upgrade["name"], variant="outline", color_scheme="gray", size="1"),
        upgrade["xws"],
    )


def render_pilot_card(pilot: dict) -> rx.Component:
    return rx.box(
        rx.hstack(
            rx.vstack(
                pilot_card_tooltip(
                    rx.text(pilot["name"], weight="bold", size="3", _hover={"color": TEXT_PRIMARY, "cursor": "help", "text_decoration": "underline"}, font_family=MONOSPACE_FONT),
                    pilot.get("xws", ""),
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
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title(
                rx.hstack(
                    rx.text(TournamentDetailState.open_list_data["faction"], size="4", font_family=SANS_FONT, weight="bold"),
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
                rx.dialog.close(rx.button("CLOSE", variant="soft", color_scheme="gray", on_click=TournamentDetailState.close_list)),
                justify="end", margin_top="16px"
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
        rx.badge(player["rank"], color_scheme="gray", size="2", variant="solid"),
        rx.vstack(
            rx.text(player["name"], size="2", weight="medium", font_family=MONOSPACE_FONT, color=TEXT_PRIMARY),
            rx.text(player["faction"], size="1", color=TEXT_SECONDARY, font_family=MONOSPACE_FONT),
            spacing="0", align="start"
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
    return rx.hstack(
        rx.text(match["round"], color=TEXT_SECONDARY, size="1", font_family=MONOSPACE_FONT),
        rx.text(match["player1"], size="2", color=TEXT_PRIMARY, font_family=MONOSPACE_FONT),
        rx.hstack(
            rx.text(match["score1"], size="2", color=TEXT_PRIMARY, font_family=MONOSPACE_FONT, weight="bold"),
            rx.text("-", size="2", color=TEXT_SECONDARY),
            rx.text(match["score2"], size="2", color=TEXT_PRIMARY, font_family=MONOSPACE_FONT, weight="bold"),
            spacing="1",
        ),
        rx.text(match["player2"], size="2", color=TEXT_PRIMARY, font_family=MONOSPACE_FONT),
        width="100%", padding="8px 12px", border_bottom=f"1px solid {BORDER_COLOR}", justify="between"
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
