from backend.api import cards as cards_api
from backend.api import lists as lists_api
from backend.api import ship_detail as ship_detail_api
from backend.api import ships as ships_api


def test_lists_endpoint_uses_sources_filter(monkeypatch):
    captured: dict = {}

    def fake_aggregate(filters, limit=10, data_source=None):
        captured["filters"] = filters
        return []

    monkeypatch.setattr(lists_api, "aggregate_list_stats", fake_aggregate)

    response = lists_api.get_lists(
        page=0,
        size=20,
        data_source="xwa",
        sort_metric="Games",
        sort_direction="desc",
        formats=None,
        factions=None,
        ships=None,
        min_games=0,
        points_min=0,
        points_max=200,
        sources=["longshanks"],
        continent=None,
        country=None,
        city=None,
        date_start=None,
        date_end=None,
        player_count_min=None,
        player_count_max=None,
    )

    assert response.total == 0
    assert captured["filters"]["sources"] == ["longshanks"]
    assert "platforms" not in captured["filters"]


def test_ships_endpoint_uses_sources_filter(monkeypatch):
    captured: dict = {}

    def fake_aggregate(filters, criteria=None, sort_direction=None, data_source=None):
        captured["filters"] = filters
        return []

    monkeypatch.setattr(ships_api, "aggregate_ship_stats", fake_aggregate)

    response = ships_api.get_ships(
        page=0,
        size=20,
        data_source="xwa",
        sort_metric="Popularity",
        sort_direction="desc",
        search=None,
        formats=None,
        factions=None,
        ships=None,
        continent=None,
        country=None,
        city=None,
        sources=["rollbetter"],
        date_start=None,
        date_end=None,
        player_count_min=None,
        player_count_max=None,
    )

    assert response.total == 0
    assert captured["filters"]["sources"] == ["rollbetter"]
    assert "platforms" not in captured["filters"]


def test_cards_endpoint_uses_search_text_and_sources(monkeypatch):
    captured: dict = {}

    def fake_aggregate(filters, criteria=None, sort_direction=None, mode="pilots", data_source=None):
        captured["filters"] = filters
        return []

    monkeypatch.setattr(cards_api, "aggregate_card_stats", fake_aggregate)

    response = cards_api.get_pilots(
        page=0,
        size=20,
        data_source="xwa",
        sort_metric="Popularity",
        sort_direction="desc",
        formats=None,
        factions=None,
        ships=None,
        initiatives=None,
        search_text="force",
        points_min=None,
        points_max=None,
        loadout_min=None,
        loadout_max=None,
        hull_min=None,
        hull_max=None,
        shields_min=None,
        shields_max=None,
        agility_min=None,
        agility_max=None,
        attack_min=None,
        attack_max=None,
        init_min=None,
        init_max=None,
        is_unique=False,
        is_limited=False,
        is_not_limited=False,
        base_sizes=None,
        sources=["listfortress"],
        continent=None,
        country=None,
        city=None,
        date_start=None,
        date_end=None,
        player_count_min=None,
        player_count_max=None,
    )

    assert response.total == 0
    assert captured["filters"]["search_text"] == "force"
    assert captured["filters"]["sources"] == ["listfortress"]
    assert "platforms" not in captured["filters"]


def test_ship_detail_lists_uses_ships_filter(monkeypatch):
    captured: dict = {}

    def fake_aggregate(filters, limit=10, data_source=None):
        captured["filters"] = filters
        return []

    monkeypatch.setattr(ship_detail_api, "aggregate_list_stats", fake_aggregate)

    response = ship_detail_api.get_ship_lists("t65xwing", data_source="xwa", limit=10)

    assert response == {"lists": []}
    assert captured["filters"] == {"ships": ["t65xwing"]}


def test_ship_detail_squadrons_uses_ships_filter(monkeypatch):
    captured: dict = {}

    def fake_aggregate(filters, sort_metric=None, sort_direction=None, data_source=None):
        captured["filters"] = filters
        return []

    monkeypatch.setattr(ship_detail_api, "aggregate_squadron_stats", fake_aggregate)

    response = ship_detail_api.get_ship_squadrons("t65xwing", data_source="xwa", limit=10)

    assert response == {"squadrons": []}
    assert captured["filters"] == {"ships": ["t65xwing"]}
