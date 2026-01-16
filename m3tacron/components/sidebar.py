"""
Responsive Sidebar/Layout Component for M3taCron.

Desktop: Fixed left sidebar with navigation - Star Wars Imperial style.
Mobile: Collapsible drawer accessible via hamburger menu.
"""
import reflex as rx


# Star Wars color palette
IMPERIAL_BLUE = "#4fb8ff"
IMPERIAL_RED = "#ff4757"
IMPERIAL_YELLOW = "#ffc312"
DARK_SPACE = "#0a0a0f"
STEEL_DARK = "#1a1a24"
STEEL_BORDER = "#2a2a3a"


def sidebar_link(text: str, href: str, icon: str) -> rx.Component:
    """Create a navigation link for the sidebar - Imperial style."""
    return rx.link(
        rx.hstack(
            rx.icon(icon, size=20, color=IMPERIAL_BLUE),
            rx.text(text, size="3", weight="medium", letter_spacing="0.05em"),
            width="100%",
            padding="12px 16px",
            border_radius="4px",
            border_left=f"2px solid transparent",
            _hover={
                "background": "rgba(79, 184, 255, 0.1)",
                "border_left": f"2px solid {IMPERIAL_BLUE}",
                "box_shadow": f"0 0 20px rgba(79, 184, 255, 0.2), inset 0 0 20px rgba(79, 184, 255, 0.05)",
            },
            transition="all 0.3s ease",
        ),
        href=href,
        style={"text_decoration": "none", "color": "inherit"},
    )


def sidebar_content() -> rx.Component:
    """The sidebar navigation content - Imperial control room style."""
    return rx.vstack(
        # Logo/Brand - Imperial style
        rx.hstack(
            rx.vstack(
                rx.text(
                    "M3TACRON",
                    size="6",
                    weight="bold",
                    color=IMPERIAL_BLUE,
                    font_family="Orbitron, sans-serif",
                    letter_spacing="0.15em",
                ),
                rx.box(
                    width="100%",
                    height="2px",
                    background=f"linear-gradient(90deg, {IMPERIAL_BLUE}, transparent)",
                    margin_top="4px",
                ),
                align="start",
            ),
            padding="24px 16px",
        ),
        # Decorative line
        rx.box(
            width="100%",
            height="1px",
            background=f"linear-gradient(90deg, {STEEL_BORDER}, transparent 80%)",
        ),
        # Navigation links
        rx.vstack(
            sidebar_link("Home", "/", "home"),
            sidebar_link("Tournaments", "/tournaments", "trophy"),
            sidebar_link("Analytics", "/analytics", "bar-chart-2"),
            width="100%",
            padding="16px 8px",
            spacing="2",
        ),
        # Spacer
        rx.spacer(),
        # Footer / Disclaimer
        rx.box(
            rx.vstack(
                rx.box(
                    width="60%",
                    height="1px",
                    background=f"linear-gradient(90deg, transparent, {STEEL_BORDER}, transparent)",
                    margin_bottom="12px",
                ),
                rx.text(
                    "UNOFFICIAL",
                    size="1",
                    color=IMPERIAL_YELLOW,
                    font_family="Orbitron, sans-serif",
                    letter_spacing="0.1em",
                    text_align="center",
                ),
                rx.text(
                    "Not affiliated with Disney/Lucasfilm",
                    size="1",
                    color="#6a6a7a",
                    text_align="center",
                ),
                align="center",
            ),
            padding="16px",
        ),
        width="100%",
        height="100vh",
        align_items="stretch",
    )


def sidebar() -> rx.Component:
    """Responsive sidebar component - Imperial style."""
    return rx.box(
        sidebar_content(),
        position="fixed",
        left="0",
        top="0",
        width="240px",
        height="100vh",
        background=f"linear-gradient(180deg, {DARK_SPACE} 0%, {STEEL_DARK} 100%)",
        backdrop_filter="blur(20px)",
        border_right=f"1px solid {STEEL_BORDER}",
        display=["none", "none", "flex", "flex"],
        z_index="100",
    )


def mobile_header() -> rx.Component:
    """Mobile header with hamburger menu - Imperial style."""
    return rx.box(
        rx.hstack(
            rx.drawer.root(
                rx.drawer.trigger(
                    rx.button(
                        rx.icon("menu", size=24),
                        variant="ghost",
                    ),
                ),
                rx.drawer.overlay(z_index="99"),
                rx.drawer.portal(
                    rx.drawer.content(
                        sidebar_content(),
                        width="240px",
                        background=f"linear-gradient(180deg, {DARK_SPACE} 0%, {STEEL_DARK} 100%)",
                        z_index="100",
                    ),
                ),
                direction="left",
            ),
            rx.text(
                "M3TACRON", 
                size="4", 
                weight="bold", 
                color=IMPERIAL_BLUE,
                font_family="Orbitron, sans-serif",
                letter_spacing="0.15em",
            ),
            rx.spacer(),
            rx.color_mode.button(size="2"),
            width="100%",
            padding="12px 16px",
            justify="between",
        ),
        position="fixed",
        top="0",
        left="0",
        right="0",
        background=f"rgba(10, 10, 15, 0.95)",
        backdrop_filter="blur(20px)",
        border_bottom=f"1px solid {STEEL_BORDER}",
        display=["flex", "flex", "none", "none"],
        z_index="100",
    )


def layout(page_content: rx.Component) -> rx.Component:
    """
    Main layout wrapper with responsive sidebar - Imperial style.
    
    Args:
        page_content: The page content to render in the main area.
    
    Returns:
        A layout component with sidebar and main content area.
    """
    return rx.box(
        sidebar(),
        mobile_header(),
        rx.box(
            page_content,
            margin_left=["0", "0", "240px", "240px"],
            margin_top=["60px", "60px", "0", "0"],
            padding="24px",
            min_height="100vh",
        ),
    )

