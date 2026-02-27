"""
Card Image Tooltip Component

Provides a hover tooltip that displays card images for pilots and upgrades.
Images are sourced from Infinite Arenas CDN.
"""
import reflex as rx


# Base URL for card images
IMAGE_BASE = "https://infinitearenas.com/xw2/images"


def pilot_image_url(xws_id: str) -> str:
    """Construct pilot card image URL from XWS ID."""
    return f"{IMAGE_BASE}/pilots/{xws_id}.png"


def upgrade_image_url(xws_id: str) -> str:
    """Construct upgrade card image URL from XWS ID."""
    return f"{IMAGE_BASE}/upgrades/{xws_id}.png"


def card_tooltip(
    trigger: rx.Component,
    xws_id: str | rx.Var,
    card_type: str = "pilot",
    side: str = "top",
) -> rx.Component:
    """
    Wrap a component with a card image tooltip.
    
    Args:
        trigger: The component that triggers the tooltip on hover
        xws_id: XWS identifier for the card
        card_type: "pilot" or "upgrade"
        side: Tooltip position - "top", "bottom", "left", "right"
    
    Returns:
        A component with hover tooltip showing the card image
    """
    # Build image URL based on card type
    # Use to_string() to ensure proper var type for concatenation
    xws_str = xws_id.to_string()
    if card_type == "pilot":
        image_url = rx.Var.create(f"{IMAGE_BASE}/pilots/") + xws_str + ".png"
    else:
        image_url = rx.Var.create(f"{IMAGE_BASE}/upgrades/") + xws_str + ".png"
    
    return rx.hover_card.root(
        rx.hover_card.trigger(trigger),
        rx.hover_card.content(
            rx.box(
                rx.image(
                    src=image_url,
                    width="300px",
                    height="auto",
                    border_radius="12px",
                    box_shadow="0 8px 32px rgba(0, 0, 0, 0.5)",
                ),
                padding="4px",
            ),
            side=side,
            side_offset=5,
        ),
        open_delay=200,
    )


def pilot_card_tooltip(
    trigger: rx.Component,
    pilot_xws: str,
    side: str = "top",
) -> rx.Component:
    """Convenience wrapper for pilot card tooltips."""
    return card_tooltip(trigger, pilot_xws, card_type="pilot", side=side)


def upgrade_card_tooltip(
    trigger: rx.Component,
    upgrade_xws: str | rx.Var,
    side: str = "top",
) -> rx.Component:
    """Convenience wrapper for upgrade card tooltips."""
    return card_tooltip(trigger, upgrade_xws, card_type="upgrade", side=side)
