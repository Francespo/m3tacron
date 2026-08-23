"""Tests for format inference, including Legacy Pandorum."""
from backend.data_structures.formats import Format, MacroFormat, infer_format_from_xws


def _yasb_list(builder_url: str, ruleset: str | None = None, points: int = 200) -> dict:
    return {
        "pilots": [{"id": "jag-siegeofcoruscant-lsl", "ship": "arc170starfighter", "points": 47}],
        "points": points,
        "vendor": {
            "yasb": {
                "link": f"{builder_url}/?f=Rebel%20Alliance&d=v8ZeZ200Z60XWW&sn=Test",
                "builder": "YASB 2.0",
                "builder_url": builder_url,
            }
        },
        "faction": "rebelalliance",
        "version": "2.0.1",
    }


def test_pandorum_builder_url_detected():
    xws = _yasb_list("https://albogarelli.github.io/pandorumbuilder")
    assert infer_format_from_xws(xws) == Format.LEGACY_PANDORUM


def test_pandorum_with_trailing_slash_detected():
    xws = _yasb_list("https://albogarelli.github.io/pandorumbuilder/")
    assert infer_format_from_xws(xws) == Format.LEGACY_PANDORUM


def test_pandorum_macro_is_v2_0():
    assert Format.LEGACY_PANDORUM.macro == MacroFormat.V2_0
    assert "legacy_pandorum" in MacroFormat.V2_0.formats()


def test_existing_formats_still_work():
    xwa = {
        "pilots": [{"id": "anakinskywalker", "ship": "delta7aethersprite", "points": 16}],
        "points": 50,
        "vendor": {"yasb": {"link": "https://yasb.app/?f=X", "builder": "YASB - X-Wing 2.5 XWA", "builder_url": "https://yasb.app/"}},
        "ruleset": "XWA",
        "faction": "galacticrepublic",
    }
    assert infer_format_from_xws(xwa) == Format.XWA

    x2po = _yasb_list("https://xwing-legacy.com")
    assert infer_format_from_xws(x2po) == Format.LEGACY_X2PO
