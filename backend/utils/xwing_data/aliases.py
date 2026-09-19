"""Read-time resolution of deprecated XWA ship/pilot ids.

When XWA folds a Configuration upgrade into a dedicated ship variant, old XWS
codes and old links still reference the pre-split ids and must keep resolving
to the variant they represent. This module is a small declarative alias map
plus resolution helpers. Adding the next XWA split means adding one
``ShipSplitAlias`` entry, not writing new branching logic.

Resolution is READ-TIME ONLY: nothing here rewrites squads, schemas or the
vendored game data.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import Iterable

from ...data_structures.data_source import DataSource


@dataclass(frozen=True)
class ShipSplitAlias:
    """A deprecated chassis whose split is selected by a trigger upgrade."""

    deprecated_id: str
    trigger_upgrades: frozenset[str]
    variant_id: str

    def is_triggered_by(self, upgrade_ids: Iterable[str]) -> bool:
        return bool(self.trigger_upgrades.intersection(upgrade_ids))

    def absorbed(self, upgrade_ids: Iterable[str]) -> frozenset[str]:
        """Trigger upgrades baked into the variant, so no longer separate cards."""
        return frozenset(self.trigger_upgrades.intersection(upgrade_ids))


# Add one entry per XWA upgrade-to-variant split. Deprecated ids must be unique.
SHIP_SPLIT_ALIASES: tuple[ShipSplitAlias, ...] = (
    ShipSplitAlias(
        deprecated_id="btanr2ywing",
        trigger_upgrades=frozenset({"wartimeloadout"}),
        variant_id="btanr2wywing",
    ),
)


@dataclass(frozen=True)
class PilotResolution:
    """Canonical identity for a possibly pre-split pilot reference."""

    pilot_xws: str
    ship_xws: str
    absorbed_upgrades: frozenset[str]


@lru_cache(maxsize=1)
def _aliases_by_deprecated_id() -> dict[str, ShipSplitAlias]:
    return {alias.deprecated_id: alias for alias in SHIP_SPLIT_ALIASES}


def normalize_upgrade_ids(upgrades: Iterable[str] | None) -> frozenset[str]:
    """Coerce a raw upgrade collection into a set of non-empty xws strings."""
    if not upgrades:
        return frozenset()
    return frozenset(u for u in upgrades if isinstance(u, str) and u)


@lru_cache(maxsize=8)
def _pilot_by_ship_and_name(source: DataSource) -> dict[tuple[str, str], str]:
    """Map (ship_xws, pilot display name) -> pilot xws for one data source.

    Moves a pre-split pilot onto the variant chassis without hardcoding a
    naming convention: the variant keeps the same card names.
    """
    from .pilots import load_all_pilots

    return {
        (info.get("ship_xws") or "", info.get("name") or ""): xws
        for xws, info in load_all_pilots(source).items()
    }


def resolve_ship_id(
    ship_xws: str,
    upgrades: Iterable[str] | None = None,
    source: DataSource = DataSource.XWA,
) -> str:
    """Return the canonical ship xws for a possibly deprecated reference.

    Resolves to the variant only when a trigger upgrade is present and the
    variant exists in the requested source; otherwise returns the id as-is.
    """
    alias = _aliases_by_deprecated_id().get(ship_xws)
    if alias is None:
        return ship_xws

    if not alias.is_triggered_by(normalize_upgrade_ids(upgrades)):
        return ship_xws

    from .ships import get_ship_info  # local import avoids an import cycle

    if get_ship_info(alias.variant_id, source) is None:
        return ship_xws
    return alias.variant_id


def resolve_pilot_reference(
    pilot_xws: str,
    upgrades: Iterable[str] | None = None,
    source: DataSource = DataSource.XWA,
) -> PilotResolution:
    """Resolve a pilot reference to its canonical identity.

    A pre-split pilot is re-pointed at the same card on the variant chassis
    when the reference carries a trigger upgrade and that variant exists.
    Without a trigger, or when the variant is absent from the source (e.g.
    Legacy), the reference is returned unchanged.
    """
    ids = normalize_upgrade_ids(upgrades)

    from .pilots import get_pilot_info

    info = get_pilot_info(pilot_xws, source)
    if not info:
        return PilotResolution(pilot_xws, "", frozenset())

    ship_xws = info.get("ship_xws") or ""
    alias = _aliases_by_deprecated_id().get(ship_xws)
    if alias is None or not alias.is_triggered_by(ids):
        return PilotResolution(pilot_xws, ship_xws, frozenset())

    variant_pilot = _pilot_by_ship_and_name(source).get(
        (alias.variant_id, info.get("name") or "")
    )
    if not variant_pilot:
        return PilotResolution(pilot_xws, ship_xws, frozenset())

    return PilotResolution(variant_pilot, alias.variant_id, alias.absorbed(ids))
