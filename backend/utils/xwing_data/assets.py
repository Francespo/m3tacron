"""Read-time card-art fallbacks for split chassis whose own art does not exist.

Some XWA splits ship a chassis whose pilots point at card PNGs the artwork
host never published. Resolving those references at read time keeps the UI
intact without touching the vendored data, the generated manifests or any
stored row.

Inventory (checked 2026-09-19 against ``infinitearenas.com``, the host the
vendored ``xwing-data2`` files reference):

* plain ``bta-nr2-y-wing.json`` — every rider ``image``
  (``pilots/<pilot>.png``) returns HTTP 200.
* integrated ``bta-nr2-w-y-wing.json`` — every rider ``image``
  (``pilots/<pilot>-wartime.png``) returns HTTP 404, ten of ten. No
  alternative path exists either: ``pilots/<pilot>-btanr2wywing.png`` 404,
  ``shipicons/resistance/I_Y-wing-bta-nr2-w.png`` 404, and YASB 2 publishes no
  pilot art of its own (it reuses the plain chassis glyph on its variant entry:
  ``"BTA-NR2-W Y-wing":{...,icon:"btanr2ywing",...}``).
* ``artwork/pilots/<pilot>-btanr2wywing.png`` exists for 9 of 10 pilots but is
  the plain illustration under a variant filename (6 of them byte-identical to
  ``artwork/pilots/<pilot>.png``, 3 a downscale of it), referenced by nothing.
  It is therefore not variant art.

The fallback borrows the card of the same-named pilot on the donor chassis —
the plain chassis art the requirement explicitly allows. Nothing is downloaded,
renamed, remapped or synthesised, and the donor URL is the one the vendored
data already carries (no invented URLs).
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CardArtFallback:
    """A variant chassis whose own pilot art is missing, and its art donor."""

    variant_id: str
    donor_id: str
    reason: str
    verified_on: str


CARD_ART_FALLBACKS: tuple[CardArtFallback, ...] = (
    CardArtFallback(
        variant_id="btanr2wywing",
        donor_id="btanr2ywing",
        reason=(
            "upstream ships no W-variant card PNG: all 10 pilots/<pilot>-wartime.png "
            "return HTTP 404 and no alternative path exists"
        ),
        verified_on="2026-09-19",
    ),
)

_BY_VARIANT: dict[str, CardArtFallback] = {
    fallback.variant_id: fallback for fallback in CARD_ART_FALLBACKS
}


def card_art_fallback(ship_xws: str) -> CardArtFallback | None:
    """Return the card-art fallback declared for ``ship_xws``, if any."""
    if not isinstance(ship_xws, str):
        return None
    return _BY_VARIANT.get(ship_xws)


def apply_card_art_fallbacks(pilots: dict[str, dict]) -> dict[str, dict]:
    """Point variant pilots at the donor chassis' card art.

    ``pilots`` is the mapping returned by ``load_all_pilots`` (pilot xws ->
    info, each carrying ``name``, ``ship_xws`` and ``image``). Pilots on a
    chassis without a declared fallback, and pilots whose donor has no
    same-named card, keep their declared image untouched. Returns the same
    mapping for convenience.
    """
    if not CARD_ART_FALLBACKS or not pilots:
        return pilots

    donor_images: dict[str, dict[str, str]] = {}
    for fallback in CARD_ART_FALLBACKS:
        donor_images[fallback.donor_id] = {
            info.get("name") or "": info.get("image") or ""
            for info in pilots.values()
            if (info.get("ship_xws") or "") == fallback.donor_id
        }

    for info in pilots.values():
        fallback = _BY_VARIANT.get(info.get("ship_xws") or "")
        if fallback is None:
            continue
        donor_image = donor_images.get(fallback.donor_id, {}).get(
            info.get("name") or ""
        )
        if donor_image:
            info["image"] = donor_image

    return pilots
