import random

from backend.analytics.factions import _limit_snapshot_lists


def _sample(n=1000):
    random.seed(7)
    out = []
    for i in range(n):
        games = random.randint(0, 100)
        out.append(
            {
                "signature": f"sig-{i}",
                "games": games,
                "entries": random.randint(0, 50),
                "win_rate": round(random.uniform(0, 100), 1),
            }
        )
    return out


def test_limit_keeps_every_sort_leader():
    lists = _sample(1000)
    trimmed = _limit_snapshot_lists(lists, 20)
    assert len(trimmed) <= 60

    by_games = max(lists, key=lambda x: x["games"])["signature"]
    by_entries = max(lists, key=lambda x: x["entries"])["signature"]
    by_wr = max((x for x in lists if x["games"] >= 3), key=lambda x: x["win_rate"])["signature"]
    kept = {x["signature"] for x in trimmed}
    assert {by_games, by_entries, by_wr} <= kept


def test_limit_zero_or_large_keeps_everything():
    lists = _sample(50)
    assert _limit_snapshot_lists(lists, 0) is lists
    assert _limit_snapshot_lists(lists, 100) is lists


def test_limit_deduplicates_signatures():
    lists = _sample(200)
    trimmed = _limit_snapshot_lists(lists, 10)
    signatures = [x["signature"] for x in trimmed]
    assert len(signatures) == len(set(signatures))
