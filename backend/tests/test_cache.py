import backend.cache as c


def test_cache_redeploy_persistence_and_version_invalidation():
    c._cache.clear()
    c._cached_version = "200"
    c._last_version_check = 0

    # Mock _get_db_version
    c._get_db_version = lambda: "200"

    # Store entries
    c.get_cached_or_compute("key1", lambda: {"hello": "world"})
    c.save_cache()
    assert "key1" in c._cache

    # Simulate container restart / redeploy: RAM is cleared
    c._cache.clear()
    assert len(c._cache) == 0

    # On startup of new container with data_version 200:
    c.set_cached_version("200")
    assert "key1" in c._cache
    assert c._cache["key1"] == {"hello": "world"}

    # Now simulate daily scrape bumping version to 201
    c._last_version_check = 0
    c._get_db_version = lambda: "201"
    c.get_cached_or_compute("key2", lambda: {"fresh": "scrape"})
    assert "key1" not in c._cache
    assert "key2" in c._cache
    assert c._cached_version == "201"

    # Clean up test files
    c.invalidate_cache()


def test_disk_cache_is_keyed_by_code_fingerprint():
    """A deploy must never restore pickles written by older analytics code.

    Regression test for the "fix deployed but has no effect" incident: the disk
    cache was keyed on data_version alone, so restarting the container after a
deploy restored results computed by the PREVIOUS code and served them until
the next scrape.
    """
    import importlib
    import pickle
    import tempfile
    from pathlib import Path

    tmpdir = Path(tempfile.mkdtemp())
    canonical = None
    try:
        canonical = importlib.reload(c)
        canonical.CACHE_DIR = tmpdir

        # Same data_version, but a fingerprint from older code.
        canonical._CODE_VERSION = "oldfingerprint"
        old_path = canonical._get_cache_file_path("79")
        old_path.parent.mkdir(parents=True, exist_ok=True)
        with open(old_path, "wb") as f:
            pickle.dump({"meta_snapshot|xwa|True": {"stale": True}}, f)

        # Deploy new code against the same data_version.
        canonical = importlib.reload(c)
        canonical.CACHE_DIR = tmpdir
        canonical._CODE_VERSION = "newfingerprint"

        assert canonical._get_cache_file_path("79").name != old_path.name
        assert canonical._load_disk_cache("79") is False
        assert not canonical._cache
    finally:
        # Restore module state for other tests.
        importlib.reload(c)


def test_fingerprint_ignores_frontend_changes():
    """Frontend-only deploys must NOT invalidate the warm cache.

    A full rebuild costs ~46 minutes (dominated by ship-detail warming), so the
    cache key must change only when code that computes cached data changes.
    """
    import importlib

    try:
        mod = importlib.reload(c)
        assert mod._CODE_FINGERPRINT, "fingerprint should be computed"
        fp = mod._CODE_FINGERPRINT

        # The fingerprint covers backend analytics code...
        assert any(p in mod._CACHE_CODE_PATHS for p in ("analytics", "api"))

        # ...but must not include frontend or CI paths. A stable fingerprint
        # across a frontend-only commit is what keeps the cache warm.
        for excluded in ("frontend", ".github", "scripts", "scrapers"):
            assert excluded not in mod._CACHE_CODE_PATHS

        # Same source -> same fingerprint (stable across processes).
        assert importlib.reload(c)._CODE_FINGERPRINT == fp
    finally:
        importlib.reload(c)
