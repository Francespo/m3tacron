from backend.data_structures.data_source import DataSource
from backend.utils.xwing_data.pilots import load_all_pilots
from backend.analytics.filter_helpers import huge_ships_exclusion_clause


def test_epic_pilots_in_xwa_and_legacy_catalogs():
    xwa_pilots = load_all_pilots(DataSource.XWA)
    legacy_pilots = load_all_pilots(DataSource.LEGACY)

    assert "outerrimpatrol" in xwa_pilots
    assert xwa_pilots["outerrimpatrol"]["epic"] is True
    assert xwa_pilots["outerrimpatrol"]["valid_in_standard"] is False

    assert "outerrimpatrol" in legacy_pilots
    assert legacy_pilots["outerrimpatrol"]["epic"] is True
    assert legacy_pilots["outerrimpatrol"]["valid_in_standard"] is False


def test_epic_pilots_filtering_in_catalog():
    all_xwa = load_all_pilots(DataSource.XWA)
    p_info = all_xwa["outerrimpatrol"]
    is_legal = p_info.get("valid_in_standard", False)
    is_epic = p_info.get("epic", False)

    allowed_formats = ["xwa"]

    # When epic is OFF and formats=["xwa"], epic-only pilot is NOT shown
    include_epic = False
    show_card = False
    if ("xwa" in allowed_formats) and is_legal:
        show_card = True
    if include_epic and is_epic:
        show_card = True
    assert show_card is False

    # When epic is ON and formats=["xwa"] (no AMG added!), epic-only pilot IS shown
    include_epic = True
    show_card = False
    if ("xwa" in allowed_formats) and is_legal:
        show_card = True
    if include_epic and is_epic:
        show_card = True
    assert show_card is True


def test_huge_ships_exclusion_clause():
    params = {}
    clause_off = huge_ships_exclusion_clause(include_epic=False, source=DataSource.XWA, params=params)
    assert clause_off.startswith("NOT (")
    assert "cr90corelliancorvette" in params.values()
    assert "syliureclasshyperspacering" in params.values()

    params_on = {}
    clause_on = huge_ships_exclusion_clause(include_epic=True, source=DataSource.XWA, params=params_on)
    assert clause_on == ""
    assert len(params_on) == 0
