"""
Responsive Sidebar/Layout Component - Imperial Data Terminal Spec.
"""
import reflex as rx

from ..theme import (
    TERMINAL_BG, TERMINAL_PANEL, TEXT_PRIMARY, TEXT_SECONDARY, BORDER_COLOR,
    MONOSPACE_FONT, SANS_FONT
)


def sidebar_link(text: str, href: str, icon: str) -> rx.Component:
    """Navigation link - Console Menu style."""
    is_active = rx.State.router.page.path == href
    
    return rx.link(
        rx.hstack(
            rx.icon(icon, size=18, color=rx.cond(is_active, TEXT_PRIMARY, TEXT_SECONDARY)),
            rx.text(
                text, 
                size="2", 
                weight="medium", 
                color=rx.cond(is_active, TEXT_PRIMARY, TEXT_SECONDARY),
                font_family=SANS_FONT,
            ),
            # Active Indicator (Bracket)
            rx.cond(
                is_active,
                rx.text("<", color=TEXT_PRIMARY, font_family=MONOSPACE_FONT),
                rx.fragment()
            ),
            width="100%",
            padding="12px 16px",
            background=rx.cond(
                is_active, 
                "rgba(255, 255, 255, 0.05)", 
                "transparent"
            ),
            border_left=rx.cond(
                is_active,
                f"2px solid {TEXT_PRIMARY}",
                "2px solid transparent"
            ),
            _hover={
                "background": "rgba(255, 255, 255, 0.03)",
                "color": TEXT_PRIMARY,
            },
            transition="all 0.2s ease",
            align="center",
            spacing="3",
        ),
        href=href,
        style={"text_decoration": "none", "width": "100%"},
    )


def sidebar_content() -> rx.Component:
    """The sidebar navigation content."""
    return rx.vstack(
        # Header / Brand
        rx.box(
            rx.vstack(
                rx.text(
                    "M3TACRON",
                    size="5",
                    weight="bold",
                    color=TEXT_PRIMARY,
                    font_family=SANS_FONT,
                    letter_spacing="-0.02em",
                ),
                rx.text(
                    "v2.0.0",
                    size="1",
                    color=TEXT_SECONDARY,
                    font_family=MONOSPACE_FONT,
                ),
                align="start",
                spacing="0"
            ),
            padding="24px 16px",
            border_bottom=f"1px solid {BORDER_COLOR}",
            width="100%"
        ),
        
        # Navigation
        rx.vstack(
            sidebar_link("DASHBOARD", "/", "home"),
            sidebar_link("TOURNAMENTS", "/tournaments", "database"),
            sidebar_link("SQUADRONS", "/squadrons", "layers"),
            sidebar_link("CARDS", "/cards", "cpu"),
            width="100%",
            padding="16px 0",
            spacing="1",
        ),
        
        rx.spacer(),
        
        # Footer
        rx.box(
            rx.vstack(
                rx.text(
                    "M3taCron Analytics",
                    size="1",
                    color=TEXT_SECONDARY,
                    font_family=SANS_FONT,
                    text_align="center",
                ),
                rx.text(
                    "Community Managed",
                    size="1",
                    color="#444444",
                    font_family=SANS_FONT,
                    text_align="center",
                ),
                align="center",
                spacing="1"
            ),
            padding="16px",
            border_top=f"1px solid {BORDER_COLOR}",
            width="100%"
        ),
        
        width="100%",
        height="100vh",
        background=TERMINAL_PANEL,
        border_right=f"1px solid {BORDER_COLOR}",
    )


def sidebar() -> rx.Component:
    """Responsive sidebar component."""
    return rx.box(
        sidebar_content(),
        position="fixed",
        left="0",
        top="0",
        width="260px",
        height="100vh",
        display=["none", "none", "flex", "flex"],
        z_index="100",
    )


def mobile_header() -> rx.Component:
    """Mobile header."""
    return rx.box(
        rx.hstack(
            rx.drawer.root(
                rx.drawer.trigger(
                    rx.button(
                        rx.icon("menu", size=24),
                        variant="ghost",
                        color=TEXT_PRIMARY
                    ),
                ),
                rx.drawer.overlay(z_index="99"),
                rx.drawer.portal(
                    rx.drawer.content(
                        sidebar_content(),
                        width="260px",
                        background=TERMINAL_PANEL,
                        z_index="100",
                    ),
                ),
                direction="left",
            ),
            rx.text(
                "M3TACRON", 
                size="4", 
                font_family=SANS_FONT,
                weight="bold",
                color=TEXT_PRIMARY
            ),
            rx.spacer(),
            width="100%",
            padding="12px 16px",
            justify="between",
            border_bottom=f"1px solid {BORDER_COLOR}",
            background=TERMINAL_BG
        ),
        position="fixed",
        top="0",
        left="0",
        right="0",
        display=["flex", "flex", "none", "none"],
        z_index="100",
    )


def layout(page_content: rx.Component) -> rx.Component:
    """Layout wrapper."""
    return rx.box(
        sidebar(),
        mobile_header(),
        rx.box(
            page_content,
            margin_left=["0", "0", "260px", "260px"],
            margin_top=["60px", "60px", "0", "0"],
            padding="32px",
            min_height="100vh",
            background=TERMINAL_BG
        ),
    )
