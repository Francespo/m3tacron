"""
Responsive Sidebar/Layout Component - Imperial Data Terminal Spec.
"""
import reflex as rx

from ..theme import (
    TERMINAL_BG, TERMINAL_PANEL, TEXT_PRIMARY, TEXT_SECONDARY, BORDER_COLOR,
    MONOSPACE_FONT, SANS_FONT
)


class SidebarState(rx.State):
    """State for sidebar collapsibility."""
    is_collapsed: bool = False
    
    def toggle_sidebar(self):
        self.is_collapsed = not self.is_collapsed


def sidebar_link(text: str, href: str, icon: str, collapsed: rx.Var = False) -> rx.Component:
    """Navigation link - Console Menu style."""
    is_active = rx.State.router.page.path == href
    
    return rx.link(
        rx.hstack(
            rx.icon(icon, size=18, color=rx.cond(is_active, TEXT_PRIMARY, TEXT_SECONDARY)),
            # Only show text when not collapsed
            rx.cond(
                collapsed,
                rx.fragment(),
                rx.text(
                    text, 
                    size="2", 
                    weight="medium", 
                    color=rx.cond(is_active, TEXT_PRIMARY, TEXT_SECONDARY),
                    font_family=SANS_FONT,
                ),
            ),
            # Active Indicator (Bracket) - only when expanded
            rx.cond(
                is_active & ~collapsed,
                rx.text("<", color=TEXT_PRIMARY, font_family=MONOSPACE_FONT),
                rx.fragment()
            ),
            width="100%",
            padding=rx.cond(collapsed, "12px 0", "12px 16px"),
            justify=rx.cond(collapsed, "center", "start"),
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


def sidebar_content(collapsed: rx.Var = False) -> rx.Component:
    """The sidebar navigation content."""
    return rx.vstack(
        # Header / Brand
        rx.box(
            rx.vstack(
                rx.cond(
                    collapsed,
                    rx.text(
                        "M3",
                        size="4",
                        weight="bold",
                        color=TEXT_PRIMARY,
                        font_family=SANS_FONT,
                        letter_spacing="-0.02em",
                    ),
                    rx.text(
                        "M3TACRON",
                        size="5",
                        weight="bold",
                        color=TEXT_PRIMARY,
                        font_family=SANS_FONT,
                        letter_spacing="-0.02em",
                    ),
                ),
                rx.cond(
                    collapsed,
                    rx.fragment(),
                    rx.text(
                        "v2.0.0",
                        size="1",
                        color=TEXT_SECONDARY,
                        font_family=MONOSPACE_FONT,
                    ),
                ),
                align=rx.cond(collapsed, "center", "start"),
                spacing="0"
            ),
            padding=rx.cond(collapsed, "24px 8px", "24px 16px"),
            border_bottom=f"1px solid {BORDER_COLOR}",
            width="100%"
        ),
        
        # Collapse Toggle Button
        rx.box(
            rx.icon_button(
                rx.cond(
                    collapsed,
                    rx.icon("chevron-right", size=16),
                    rx.icon("chevron-left", size=16)
                ),
                on_click=SidebarState.toggle_sidebar,
                variant="ghost",
                color_scheme="gray",
                size="1",
            ),
            width="100%",
            display="flex",
            justify=rx.cond(collapsed, "center", "end"),
            padding="8px",
        ),
        
        # Navigation
        rx.vstack(
            sidebar_link("DASHBOARD", "/", "home", collapsed),
            sidebar_link("TOURNAMENTS", "/tournaments", "database", collapsed),
            sidebar_link("SQUADRONS", "/squadrons", "swords", collapsed),
            sidebar_link("LISTS", "/lists", "list", collapsed),
            sidebar_link("SHIPS", "/ships", "rocket", collapsed),
            sidebar_link("CARDS", "/cards", "sticky-note", collapsed),
            width="100%",
            padding="16px 0",
            spacing="1",
        ),
        
        rx.spacer(),
        
        # Footer (hidden when collapsed)
        rx.cond(
            collapsed,
            rx.fragment(),
            rx.box(
                rx.vstack(
                    rx.text(
                        "M3taCron Analytics",
                        size="1",
                        color=TEXT_SECONDARY,
                        font_family=SANS_FONT,
                        weight="bold",
                    ),
                    rx.text(
                        "Built by Francespo",
                        size="1",
                        color=TEXT_SECONDARY,
                        font_family=SANS_FONT,
                    ),
                    rx.link(
                        rx.button(
                            rx.icon("coffee", size=16),
                            "Support on Ko-fi",
                            variant="soft",
                            color_scheme="orange",
                            size="1",
                            cursor="pointer",
                            width="100%",
                            margin_top="8px",
                            style={"font_family": MONOSPACE_FONT},
                        ),
                        href="https://ko-fi.com/francespo",
                        is_external=True,
                        style={"text_decoration": "none", "width": "100%"}
                    ),
                    rx.divider(margin_top="8px", margin_bottom="8px", opacity=0.1),
                    rx.text(
                        "Star Wars and all related properties are © & ™ Lucasfilm Ltd. and/or The Walt Disney Company. This fan-created site is for informational purposes only and is not affiliated with, endorsed by, or sponsored by Lucasfilm Ltd. or The Walt Disney Company.",
                        size="1",
                        color="#555555",
                        font_family=SANS_FONT,
                        text_align="center",
                        line_height="1.3",
                    ),
                    align="center",
                    spacing="1"
                ),
                padding="16px",
                border_top=f"1px solid {BORDER_COLOR}",
                width="100%"
            ),
        ),
        
        width="100%",
        height="100vh",
        background=TERMINAL_PANEL,
        border_right=f"1px solid {BORDER_COLOR}",
    )


def sidebar() -> rx.Component:
    """Responsive sidebar component with collapsibility."""
    return rx.box(
        sidebar_content(SidebarState.is_collapsed),
        position="fixed",
        left="0",
        top="0",
        width=rx.cond(SidebarState.is_collapsed, "60px", "260px"),
        height="100vh",
        display=["none", "none", "flex", "flex"],
        z_index="100",
        transition="width 0.2s ease",
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
                        sidebar_content(False),
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


def layout(page_content: rx.Component, **kwargs) -> rx.Component:
    """Layout wrapper with collapsible sidebar."""
    return rx.box(
        sidebar(),
        mobile_header(),
        rx.box(
            page_content,
            margin_left=rx.cond(
                SidebarState.is_collapsed,
                ["0", "0", "60px", "60px"],
                ["0", "0", "260px", "260px"]
            ),
            margin_top=["60px", "60px", "0", "0"],
            padding="0",
            height="100vh",
            width="auto",
            overflow_y="auto",
            overflow_x="hidden",
            background=TERMINAL_BG,
            style={"position": "relative"},
            transition="margin-left 0.2s ease",
        ),
        **kwargs
    )

def dashboard_layout(filters_sidebar: rx.Component, main_content: rx.Component) -> rx.Component:
    """
    A 2-column dashboard layout (Filters | Content) to be used within the main layout.
    """
    return rx.flex(
        # Filters Column
        rx.box(
            filters_sidebar,
            width=["100%", "100%", "300px", "350px"],
            height="100%",
            overflow_y="auto",
            border_right=f"1px solid {BORDER_COLOR}",
            padding="24px",
            background=TERMINAL_BG,
            class_name="scrollbar-thin",
            scrollbar_gutter="stable",
        ),
        # Main Content Column
        rx.box(
            main_content,
            flex="1",
            height="100%",
            overflow_y="auto",
            padding="24px",
            background=TERMINAL_BG,
            class_name="scrollbar-thin",
            scrollbar_gutter="stable",
        ),
        flex_direction=["column", "row"],
        width="100%",
        height="100%",
        overflow="hidden",
        style={"box_shadow": "none", "border": "none"}
    )
