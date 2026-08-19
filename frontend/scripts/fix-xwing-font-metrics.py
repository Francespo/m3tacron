#!/usr/bin/env python3
"""
fix-xwing-font-metrics.py — centre the X-Wing Miniatures faux/icon fonts.

The X-Wing Miniatures fonts (xwing-miniatures / xwing-miniatures-ships) are
FAUX fonts: they are icon fonts, not text fonts. Their glyphs must be treated
as icons and rendered centred inside their box — they must NOT sit on the text
baseline.

The shipped "-centered" variants already moved the bulk of the glyphs onto the
typographic box centre, but the job was left half done:

  * A few glyphs were never re-centred (e.g. underscore/grave/control chars,
    bracketright, I-acute family, asciicircum/agility) — those still float off
    the box centre.
  * The vertical metrics are inconsistent between the tables browsers/OSes
    consult:
      - hhea.ascent / descent        -> used by Linux/macOS + canvas
      - OS/2 sTypoAscender/Descender -> used when fsSelection bit 7 is set
      - OS/2 usWinAscent/Descent     -> used by Windows browsers when bit 7
                                        is NOT set
    For the faction font the Win box centre (407) is 157 units below the glyph
    centre (250) -> on Windows every glyph appears shifted DOWN. The OS/2
    fsSelection bit 7 (USE_TYPO_METRICS) is also not set.

What this script does (per font):

  1. Re-centres EVERY glyph's ink bbox so its vertical centre lands exactly on
     the metrics-box centre. Composite glyphs are handled by shifting their
     components (this font has none, but the code is generic).
  2. Makes the vertical metrics symmetric and identical across all tables:
       hhea.ascent            = +UPM/2        hhea.descent            = -UPM/2
       sTypoAscender          = +UPM/2        sTypoDescender          = -UPM/2
       usWinAscent            = +UPM/2        usWinDescent            = +UPM/2
       fsSelection bit 7 (USE_TYPO_METRICS) = set
     With a symmetric box centred on the baseline (y=0) every platform/browser
     computes the SAME line box, and each glyph's ink centre == box centre.
  3. Recomputes head.hhea/OS2 metric fields that describe the em box
     (head.yMin/yMax, hhea.advanceWidthMax/minLeftSideBearing/etc.,
     OS/2.usXMaxExtent) from the actual glyph data.

The result: every icon glyph (faction symbols, ship glyphs, stat/upgrade
glyphs, "special characters") renders vertically centred in a `line-height: 1`
box on Linux, macOS AND Windows, in Chrome/Firefox/Safari/Edge, in the DOM and
in <canvas> alike — with zero per-element CSS hacks.

Usage:
    python3 fix-xwing-font-metrics.py [--dist DIR] [--dry-run] [--verbose]

    --dist DIR   directory containing xwing-miniatures-centered.ttf and
                 xwing-miniatures-ships-centered.ttf
                 (default: ../../external_data/xwing-miniatures-font/dist)
    --dry-run    print the plan and diagnostics without writing any files
    --verbose    per-glyph detail

Requires: pip install fonttools
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from fontTools.ttLib import TTFont
from fontTools.ttLib.tables._g_l_y_f import Glyph

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

# A symmetric em box centred on the baseline has its centre at y = 0, so the
# target glyph-ink centre is 0 font units.
TARGET_CENTRE = 0.0

DEFAULT_DIST = (
    Path(__file__).resolve().parent.parent.parent
    / "external_data"
    / "xwing-miniatures-font"
    / "dist"
)

FONTS = [
    "xwing-miniatures-centered.ttf",
    "xwing-miniatures-ships-centered.ttf",
]

# Glyphs whose ink bbox centre is allowed to deviate from the target centre by
# less than this many font units without being re-centred (rounding noise).
CENTRE_EPSILON = 1.0


# ---------------------------------------------------------------------------
# Glyph helpers
# ---------------------------------------------------------------------------

def glyph_ink_bbox(glyph: Glyph, glyf) -> tuple[float, float, float, float]:
    """Return (xMin, yMin, xMax, yMax) of a simple or composite glyph."""
    if glyph.numberOfContours >= 0:
        return glyph.xMin, glyph.yMin, glyph.xMax, glyph.yMax
    # Composite: union of transformed component bboxes.
    xMin = yMin = float("inf")
    xMax = yMax = float("-inf")
    for comp in glyph.components:
        base = glyf[comp.glyphName]
        tx, ty = comp.transform.transformPoint((comp.x, comp.y))
        bx0, by0, bx1, by1 = glyph_ink_bbox(base, glyf)
        xMin = min(xMin, bx0 + tx)
        yMin = min(yMin, by0 + ty)
        xMax = max(xMax, bx1 + tx)
        yMax = max(yMax, by1 + ty)
    return xMin, yMin, xMax, yMax


def translate_glyph(glyph: Glyph, dx: float, dy: float, glyf) -> None:
    """Translate a simple or composite glyph by (dx, dy) font units."""
    if glyph.numberOfContours >= 0:
        glyph.coordinates.translate((dx, dy))
        glyph.recalcBounds(glyf)
    else:
        for comp in glyph.components:
            comp.x += dx
            comp.y += dy


def glyph_xmax(name: str, font: TTFont) -> float:
    glyf = font["glyf"]
    glyph = glyf[name]
    if glyph.numberOfContours == 0:
        return 0.0
    x0, _, x1, _ = glyph_ink_bbox(glyph, glyf)
    return max(x0, x1)


# ---------------------------------------------------------------------------
# Font fixer
# ---------------------------------------------------------------------------

def fix_font(path: Path, dry_run: bool, verbose: bool) -> dict:
    font = TTFont(str(path))
    upm = font["head"].unitsPerEm
    glyf = font["glyf"]
    hmtx = font["hmtx"]
    hhea = font["hhea"]
    os2 = font["OS/2"]

    # Each glyph needs a back-reference to the font for composite handling.
    glyf._font = font

    report = {
        "font": path.name,
        "upm": upm,
        "glyphs_centered": 0,
        "glyphs_left": 0,
        "shifted_by": [],
    }

    # --- 1. Recentre every glyph ------------------------------------------
    for name in font.getGlyphOrder():
        if name in (".notdef", ".null", "space", "nonmarkingreturn"):
            continue
        glyph = glyf[name]
        if glyph.numberOfContours == 0:
            continue
        x0, y0, x1, y1 = glyph_ink_bbox(glyph, glyf)
        ink_cy = (y0 + y1) / 2.0
        shift = TARGET_CENTRE - ink_cy
        if abs(shift) > CENTRE_EPSILON:
            translate_glyph(glyph, 0.0, shift, glyf)
            report["glyphs_centered"] += 1
            report["shifted_by"].append((name, round(shift, 1)))
        else:
            report["glyphs_left"] += 1

    # --- 2. Symmetric vertical metrics -------------------------------------
    ascent = upm / 2.0
    descent = -upm / 2.0
    half = int(round(ascent))

    hhea.ascent = half
    hhea.descent = -half
    hhea.lineGap = 0
    os2.sTypoAscender = half
    os2.sTypoDescender = -half
    os2.sTypoLineGap = 0
    os2.usWinAscent = half
    os2.usWinDescent = half

    # USE_TYPO_METRICS (fsSelection bit 7) is only defined for OS/2 version 4+.
    # Bump the table so every rasteriser (notably Windows) honours the
    # symmetric typographic metrics we just wrote, and fill in the v4 fields
    # (typographic x/cap heights are set to the em half so vertical alignment
    # of these icon glyphs is symmetric in all line-layout engines).
    if os2.version < 4:
        os2.version = 4
    os2.sxHeight = half
    os2.sCapHeight = half
    os2.usDefaultChar = 0
    os2.usBreakChar = 32
    if os2.usMaxContext is None or os2.usMaxContext < 1:
        os2.usMaxContext = 1
    os2.fsSelection |= 0x80  # USE_TYPO_METRICS

    # --- 3. Recompute box / metric fields ----------------------------------
    font["head"].recalcBBoxes = True
    # Deterministic output: fontTools stamps head.modified with the current
    # time on save (ttFont.recalcTimestamp), which makes repeated runs produce
    # different bytes. Disable it so the script is byte-idempotent (identical
    # output every run).
    font.recalcTimestamp = False
    font["head"].created = font["head"].modified = 0
    if hmtx is not None:
        hhea.advanceWidthMax = max(a for a, _ in hmtx.metrics.values())
        hhea.minLeftSideBearing = min(lsb for _, lsb in hmtx.metrics.values())
        hhea.minRightSideBearing = min(
            a - (lsb + max(0.0, glyph_xmax(name, font)))
            for name, (a, lsb) in hmtx.metrics.items()
        )
        hhea.xMaxExtent = max(
            lsb + glyph_xmax(name, font) for name, (_, lsb) in hmtx.metrics.items()
        )
        hhea.numberOfHMetrics = len(hmtx.metrics)

    report["metrics"] = {
        "ascent": hhea.ascent,
        "descent": hhea.descent,
        "sTypoAscender": os2.sTypoAscender,
        "sTypoDescender": os2.sTypoDescender,
        "usWinAscent": os2.usWinAscent,
        "usWinDescent": os2.usWinDescent,
        "fsSelection": f"0x{os2.fsSelection:04X}",
    }

    if not dry_run:
        font.save(str(path))
        print(f"  wrote {path}")

    if verbose:
        for name, shift in report["shifted_by"]:
            print(f"    {name}: shifted {shift}")

    return report


# ---------------------------------------------------------------------------
# Diagnostics
# ---------------------------------------------------------------------------

def diagnose(path: Path) -> None:
    font = TTFont(str(path))
    upm = font["head"].unitsPerEm
    hhea = font["hhea"]
    os2 = font["OS/2"]
    glyf = font["glyf"]

    centres = []
    for name in font.getGlyphOrder():
        if name in (".notdef", ".null", "space", "nonmarkingreturn"):
            continue
        glyph = glyf[name]
        if glyph.numberOfContours == 0:
            continue
        x0, y0, x1, y1 = glyph_ink_bbox(glyph, glyf)
        centres.append((y0 + y1) / 2.0)

    print(f"--- {path.name} ---")
    print(f"  UPM={upm}")
    print(
        f"  hhea: ascent={hhea.ascent} descent={hhea.descent} lineGap={hhea.lineGap} "
        f"-> box centre={(hhea.ascent + hhea.descent)/2:.1f}"
    )
    print(
        f"  OS/2: sTypoAsc={os2.sTypoAscender} sTypoDesc={os2.sTypoDescender} "
        f"sTypoLineGap={os2.sTypoLineGap} -> box centre={(os2.sTypoAscender + os2.sTypoDescender)/2:.1f}"
    )
    print(
        f"  OS/2: usWinAsc={os2.usWinAscent} usWinDesc={os2.usWinDescent} "
        f"-> box centre={(os2.usWinAscent - os2.usWinDescent)/2:.1f}"
    )
    print(
        "  OS/2: fsSelection="
        f"0x{os2.fsSelection:04X} USE_TYPO_METRICS={'yes' if os2.fsSelection & 0x80 else 'no'}"
    )
    if centres:
        print(
            f"  glyph centres: min={min(centres):.1f} max={max(centres):.1f} "
            f"avg={sum(centres)/len(centres):.1f} (target box centre=0.0)"
        )
        off = [c for c in centres if abs(c) > 5]
        print(f"  glyphs still off-centre (>5u): {len(off)}")
    print()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dist",
        type=Path,
        default=DEFAULT_DIST,
        help="directory containing the -centered.ttf fonts",
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="diagnose and plan without writing files"
    )
    parser.add_argument("--verbose", action="store_true", help="per-glyph detail")
    args = parser.parse_args()

    dist: Path = args.dist
    if not dist.is_dir():
        print(f"error: dist directory not found: {dist}", file=sys.stderr)
        return 1

    missing = [f for f in FONTS if not (dist / f).exists()]
    if missing:
        print(f"error: missing fonts in {dist}: {', '.join(missing)}", file=sys.stderr)
        return 1

    print("== BEFORE ==")
    for name in FONTS:
        diagnose(dist / name)

    print("== PLAN ==")
    for name in FONTS:
        report = fix_font(dist / name, dry_run=True, verbose=args.verbose)
        print(
            f"  {name}: centre {report['glyphs_centered']} glyphs, "
            f"leave {report['glyphs_left']} (already centred)"
        )

    if args.dry_run:
        print("\n(dry run: nothing written)")
        return 0

    print("\n== FIXING ==")
    for name in FONTS:
        fix_font(dist / name, dry_run=False, verbose=args.verbose)

    print("\n== AFTER ==")
    for name in FONTS:
        diagnose(dist / name)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
