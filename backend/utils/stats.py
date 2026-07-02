def normalize_stat_count(value) -> int:
    try:
        count = int(value)
    except Exception:
        return 0

    return count if count > 0 else 0