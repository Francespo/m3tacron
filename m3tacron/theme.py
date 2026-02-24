"""
M3taCron Design System - Modern Professional Spec.

Philosophy: "Chromatic Minimalism" (SaaS Style).
- Canvas: Pure Black (#050505)
- Geometry: Soft Rectangular (6px radius).
- Typography: Sans-Serif (Inter) for UI, Monospace for Data.
- Color: Semantic Faction Colors.
"""
import reflex as rx

# -----------------------------------------------------------------------------
# 1. THE CANVAS (MONOCHROME)
# -----------------------------------------------------------------------------
TERMINAL_BG = "#000000"      # Pure Depth
TERMINAL_PANEL = "#0A0A0A"   # Very dark grey
TEXT_PRIMARY = "#FFFFFF"     # Primary Text
TEXT_SECONDARY = "#AAAAAA"   # Softer Grey for Labels (contrast improved from #888888)
BORDER_COLOR = "#333333"     # Dividers

# Status Colors
STATUS_VICTORY = "#FFFFFF"   
STATUS_DEFEAT = "#666666"    

# -----------------------------------------------------------------------------
# 2. SEMANTIC FACTION COLORS (MANDATORY)
# -----------------------------------------------------------------------------
# These must be used for Faction Icons, Charts, and Badges.
FACTION_COLORS = {
    "rebelalliance": "#FF3333",       # Bright Red
    "galacticempire": "#2979FF",      # Vivid Blue (Readable)
    "scumandvillainy": "#006400",     # Dark Green
    "resistance": "#FF8C00",          # Orange
    "firstorder": "#800020",          # Wine Red
    "galacticrepublic": "#E6D690",    # Soft Golden Cream
    "separatistalliance": "#607D8B",  # Blue-Grey
    "unknown": "#666666"              # Grey
}

# -----------------------------------------------------------------------------
# 3. TYPOGRAPHY & SHAPES
# -----------------------------------------------------------------------------
SANS_FONT = '"Inter", "Segoe UI", "Roboto", sans-serif'
HEADER_FONT = SANS_FONT # Aliased for backward compatibility/clarity
MONOSPACE_FONT = '"JetBrains Mono", "Roboto Mono", monospace'
# Orbitron removed/deprecated for modern look

RADIUS = "6px" # Modern Standard

# -----------------------------------------------------------------------------
# 4. ICON MAPPINGS (X-WING FONT)
# -----------------------------------------------------------------------------
# Maps internal ID to xwing-miniatures-font character class
FACTION_ICONS = {
    "rebelalliance": "xwing-miniatures-font-rebel",
    "galacticempire": "xwing-miniatures-font-empire",
    "scumandvillainy": "xwing-miniatures-font-scum",
    "resistance": "xwing-miniatures-font-rebel",
    "firstorder": "xwing-miniatures-font-firstorder",
    "galacticrepublic": "xwing-miniatures-font-republic",
    "separatistalliance": "xwing-miniatures-font-separatists",
}

# -----------------------------------------------------------------------------
# 5. UI PRESETS (STYLES)
# -----------------------------------------------------------------------------

# Panel Style: Transparent or very dark with semantic borders
TERMINAL_PANEL_STYLE = {
    "background": TERMINAL_PANEL,
    "border": f"1px solid {BORDER_COLOR}",
    "borderRadius": RADIUS,
    # Subtle inward depth: pure dark, no color bleed.
    "boxShadow": "inset 0 1px 0 rgba(255, 255, 255, 0.03)",
    "padding": "16px",
}

# Input/Select Style
INPUT_STYLE = {
    "background": "#000000",
    "border": f"1px solid {BORDER_COLOR}",
    "border_radius": RADIUS,
    "color": TEXT_PRIMARY,
    "font_family": MONOSPACE_FONT,
    "_focus": {
        "border_color": TEXT_PRIMARY, 
        "box_shadow": "none"
    }
}
