"""Read-time resolution of pre-split XWA ship ids.

XWA sometimes takes a Configuration upgrade that used to be a separate card
and folds it into a dedicated ship variant with its own chassis entry and its
own pilots. Old XWS codes and old deep links still reference the pre-split
chassis paired with that upgrade, so both encodings of the same squad are in
the wild and must keep resolving to the same identity.

This module is a small declarative map plus resolution helpers. Adding the
next split of this class is one ``ShipSplitAlias`` entry, not new branching
logic. Resolution is READ-TIME ONLY: nothing here rewrites squads, stored
lists, schemas or the vendored game data.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import Iterable

from ...data_structures.data_source import DataSource


@dataclass(frozen=True)
class ShipSplitAlias:
    """A pre-split chassis that XWA now ships as a dedicated variant."""

    deprecated_id: str
    variant_id: str
    absorbed_upgrades: frozenset[str]

    def is_triggered_by(self, upgrade_ids: frozenset[str]) -> bool:
        """True when the reference carries an upgrade folded into the variant."""
        return bool(self.absorbed_upgrades & upgrade_ids)

    def still_separate(self, upgrade_ids: frozenset[str]) -> frozenset[str]:
        """Upgrade ids that must stay listed as their own card."""
        return upgrade_ids - self.absorbed_upgrades


# Add one entry per XWA upgrade-absorbed-into-a-variant split.
# ``deprecated_id`` must be unique and must not be the variant itself.
SHIP_SPLIT_ALIASES: tuple[ShipSplitAlias, ...] = (
    ShipSplitAlias(
        deprecated_id="btanr2ywing",
        variant_id="btanr2wywing",
        absorbed_upgrades=frozenset({"wartimeloadout"}),
    ),
)

_ALIASES_BY_DEPRECATED_ID: dict[str, ShipSplitAlias] = {
    alias.deprecated_id: alias for alias in SHIP_SPLIT_ALIASES
}


def get_ship_split_alias(ship_xws: str) -> ShipSplitAlias | None:
    """Return the split alias declared for ``ship_xws``, if any."""
    if not isinstance(ship_xws, str):
        return None
    return _ALIASES_BY_DEPRECATED_ID.get(ship_xws)


def normalize_upgrade_ids(upgrades: Iterable[str] | None) -> frozenset[str]:
    """Coerce an upgrade collection into a set of non-empty xws strings."""
    if not upgrades:
        return frozenset()
    if isinstance(upgrades, str):
        return frozenset({upgrades}) if upgrades else frozenset()
    return frozenset(u for u in upgrades if isinstance(u, str) and u)


def resolve_ship_id(
    ship_xws: str,
    upgrade_ids: Iterable[str] | None = None,
    source: DataSource = DataSource.XWA,
) -> str:
    """Return the canonical ship xws for a possibly pre-split reference.

    Resolves to the variant only when the context carries an absorbed upgrade
    AND the variant actually exists in ``source``; otherwise the id is
    returned untouched (e.g. Legacy has no integrated variant).
    """
    alias = get_ship_split_alias(ship_xws)
    if alias is None:
        return ship_xws
    if not alias.is_triggered_by(normalize_upgrade_ids(upgrade_ids)):
        return ship_xws

    from .ships import get_ship_info  # local import avoids an import cycle

    if get_ship_info(alias.variant_id, source=source) is None:
        return ship_xws
    return alias.variant_id


@dataclass(frozen=True)
class PilotResolution:
    """Canonical identity of a possibly pre-split pilot reference."""

    pilot_xws: str
    ship_xws: str
    absorbed_upgrades: frozenset[str]


def resolve_pilot_reference(
    pilot_xws: str,
    upgrade_ids: Iterable[str] | None = None,
    source: DataSource = DataSource.XWA,
) -> PilotResolution:
    """Resolve a pilot reference to the chassis it is actually played on.

    A pre-split pilot re-points at the same card name on the variant chassis
    when the context carries an absorbed upgrade and that variant exists.
    Otherwise the reference is returned unchanged.
    """
    from .pilots import get_pilot_info

    ids = normalize_upgrade_ids(upgrade_ids)
    info = get_pilot_info(pilot_xws, source=source)
    if not info:
        return PilotResolution(pilot_xws, "", frozenset())

    ship_xws = info.get("ship_xws") or ""
    alias = get_ship_split_alias(ship_xws)
    if alias is None or not alias.is_triggered_by(ids):
        return PilotResolution(pilot_xws, ship_xws, frozenset())

    variant_pilot = _pilot_on_ship_by_name(alias.variant_id, source).get(
        info.get("name") or ""
    )
    if not variant_pilot:
        return PilotResolution(pilot_xws, ship_xws, frozenset())

    return PilotResolution(variant_pilot, alias.variant_id, alias.absorbed_upgrades)


@lru_cache(maxsize=8)
def _pilot_on_ship_by_name(ship_xws: str, source: DataSource) -> dict[str, str]:
    """Map pilot display name -> pilot xws for one chassis (cached per source)."""
    from .pilots import load_all_pilots

    return {
        info.get("name") or "": xws
        for xws, info in load_all_pilots(source).items()
        if (info.get("ship_xws") or "") == ship_xws
    }
