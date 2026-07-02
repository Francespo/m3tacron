from backend.utils.stats import normalize_stat_count


def test_normalize_stat_count_treats_missing_and_negative_as_zero():
    assert normalize_stat_count(None) == 0
    assert normalize_stat_count(-1) == 0
    assert normalize_stat_count("-1") == 0


def test_normalize_stat_count_keeps_positive_values():
    assert normalize_stat_count(0) == 0
    assert normalize_stat_count(3) == 3
    assert normalize_stat_count("7") == 7