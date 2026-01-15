"""
Responsive Sidebar/Layout Component for M3taCron.

Desktop: Fixed left sidebar with navigation.
Mobile: Collapsible drawer accessible via hamburger menu.
"""
import reflex as rx


def sidebar_link(text: str, href: str, icon: str) -> rx.Component:
    """Create a navigation link for the sidebar."""
    return rx.link(
        rx.hstack(
            rx.icon(icon, size=20),
            rx.text(text, size="3", weight="medium"),
            width="100%",
            padding="12px 16px",
            border_radius="8px",
            _hover={
                "background": "rgba(255, 255, 255, 0.1)",
                "box_shadow": "0 0 15px rgba(6, 182, 212, 0.3)",
                "border": "1px solid rgba(6, 182, 212, 0.3)",
            },
            transition="all 0.2s ease-in-out",
        ),
        href=href,
        style={"text_decoration": "none", "color": "inherit"},
    )


def sidebar_content() -> rx.Component:
    """The sidebar navigation content."""
    return rx.vstack(
        # Logo/Brand
        rx.hstack(
            rx.text(
                "M3TACRON",
                size="6",
                weight="bold",
                color="cyan",
                font_family="Rajdhani",
                letter_spacing="0.1em",
                _hover={
                    "text_shadow": "0 0 10px var(--accent-9)",
                    "cursor": "default",
                },
            ),
            padding="24px 16px",
        ),
        rx.divider(color_scheme="gray"),
        # Navigation links
        rx.vstack(
            sidebar_link("Home", "/", "home"),
            sidebar_link("Tournaments", "/tournaments", "trophy"),
            sidebar_link("Analytics", "/analytics", "bar-chart-2"),
            sidebar_link("Admin", "/admin", "shield"),
            width="100%",
            padding="16px 8px",
            spacing="2",
        ),
        # Spacer
        rx.spacer(),
        # Footer / Disclaimer
        rx.box(
            rx.text(
                "Unofficial. Not affiliated with Disney/Lucasfilm.",
                size="1",
                color="gray",
                text_align="center",
            ),
            padding="16px",
        ),
        width="100%",
        height="100vh",
        align_items="stretch",
    )


def sidebar() -> rx.Component:
    """Responsive sidebar component."""
    # Desktop sidebar (visible on large screens)
    return rx.box(
        sidebar_content(),
        position="fixed",
        left="0",
        top="0",
        width="240px",
        height="100vh",
        background="rgba(15, 23, 42, 0.6)",
        backdrop_filter="blur(20px)",
        border_right="1px solid rgba(255, 255, 255, 0.1)",
        display=["none", "none", "flex", "flex"],  # Hidden on mobile, visible on md+
        z_index="100",
    )


def mobile_header() -> rx.Component:
    """Mobile header with hamburger menu."""
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
                        background="rgba(15, 23, 42, 0.98)",
                        z_index="100",
                    ),
                ),
                direction="left",
            ),
            rx.text(
                "M3TACRON", 
                size="4", 
                weight="bold", 
                color="cyan",
                font_family="Rajdhani",
                letter_spacing="0.1em",
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
        background="rgba(15, 23, 42, 0.8)",
        backdrop_filter="blur(20px)",
        border_bottom="1px solid rgba(255, 255, 255, 0.1)",
        display=["flex", "flex", "none", "none"],  # Visible on mobile, hidden on md+
        z_index="100",
    )


def layout(page_content: rx.Component) -> rx.Component:
    """
    Main layout wrapper with responsive sidebar.
    
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
            # Margin left for sidebar on desktop, top for mobile header
            margin_left=["0", "0", "240px", "240px"],
            margin_top=["60px", "60px", "0", "0"],
            padding="24px",
            min_height="100vh",
            # Remove background from here as it's now global
            # background="linear-gradient(135deg, #0f172a 0%, #1e293b 100%)",
        ),
    )
