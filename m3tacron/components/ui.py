"""
Reusable UI components for M3taCron pages.
"""
import reflex as rx

from ..theme import (
    TERMINAL_PANEL_STYLE, TEXT_PRIMARY, TEXT_SECONDARY, BORDER_COLOR,
    MONOSPACE_FONT, SANS_FONT, RADIUS
)


def content_panel(title: str, content: rx.Component, icon: str = "activity") -> rx.Component:
    """
    A modern professional panel.
    """
    return rx.box(
        rx.vstack(
            # Header
            rx.hstack(
                rx.icon(icon, size=18, color=TEXT_SECONDARY),
                rx.text(
                    title, 
                    size="3", 
                    font_family=SANS_FONT,
                    weight="medium",
                    letter_spacing="0.05em",
                    color=TEXT_PRIMARY,
                ),
                width="100%",
                align="center",
                margin_bottom="16px",
                border_bottom=f"1px solid {BORDER_COLOR}",
                padding_bottom="12px",
            ),
            # Content
            rx.box(content, width="100%"),
            width="100%",
            spacing="0",
        ),
        padding="20px",
        style=TERMINAL_PANEL_STYLE,
        border_radius=RADIUS, # Use Reflex snake_case prop which maps to borderRadius
        width="100%",
        height="100%",
    )

def list_row(
    left_content: rx.Component, 
    right_content: rx.Component, 
    index: int = 0,
    border_color: str = "transparent"
) -> rx.Component:
    """
    A standardized high-density list row.
    """
    # Calculate delay class (max 500ms)
    # Safe delay calculation for Var index
    delay_ms = (index + 1) * 100
    delay_cls = rx.cond(
        delay_ms > 500,
        "delay-500",
        f"delay-{delay_ms}"
    )
    
    return rx.hstack(
        left_content,
        rx.spacer(),
        right_content,
        width="100%",
        padding="8px 12px", # High density
        border_bottom=f"1px solid {BORDER_COLOR}",
        border_left=rx.cond(
            border_color != "transparent", 
            f"2px solid {border_color}", 
            "none"
        ),
        align="center",
        class_name=f"animate-fade-in-up {delay_cls}",
        background="transparent",
        transition="background 0.2s ease",
        border_radius=RADIUS,
        _hover={
            "background": "rgba(255, 255, 255, 0.05)",
        }
    )


def stat_card(title: str, value: rx.Var, subtitle: str = "") -> rx.Component:
    """Minimalist stat card."""
    return rx.box(
        rx.vstack(
            rx.text(
                title, 
                size="1", 
                color=TEXT_SECONDARY, 
                font_family=SANS_FONT, 
                weight="medium",
                letter_spacing="0.05em",
                text_transform="uppercase",
            ),
            rx.text(
                value, 
                size="7", 
                weight="bold", 
                color=TEXT_PRIMARY,
                font_family=MONOSPACE_FONT, # Keep data mono
            ),
            rx.text(subtitle, size="1", color="#444444") if subtitle else rx.fragment(),
            spacing="1",
            align="start",
        ),
        padding="16px",
        style=TERMINAL_PANEL_STYLE,
        min_width="180px",
    )
