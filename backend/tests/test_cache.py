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


def test_disk_cache_is_keyed_by_code_version():
    """A deploy must never restore pickles written by older code.

    Regression test for the "fix deployed but has no effect" incident: the
    disk cache was keyed on data_version alone, so restarting the container
    after a deploy restored results computed by the PREVIOUS code and served
    them until the next scrape.
    """
    import importlib
    import os
    import pickle
    import tempfile
    from pathlib import Path

    original = os.environ.get("SOURCE_COMMIT")
    try:
        tmpdir = Path(tempfile.mkdtemp())

        os.environ["SOURCE_COMMIT"] = "oldcode111"
        mod = importlib.reload(c)
        mod.CACHE_DIR = tmpdir
        old_path = mod._get_cache_file_path("79")
        old_path.parent.mkdir(parents=True, exist_ok=True)
        with open(old_path, "wb") as f:
            pickle.dump({"meta_snapshot|xwa|True": {"stale": True}}, f)

        # Simulate deploying new code against the same data_version.
        os.environ["SOURCE_COMMIT"] = "newcode222"
        mod = importlib.reload(c)
        mod.CACHE_DIR = tmpdir

        assert mod._get_cache_file_path("79").name != old_path.name
        assert mod._load_disk_cache("79") is False
        assert not mod._cache
    finally:
        if original is None:
            os.environ.pop("SOURCE_COMMIT", None)
        else:
            os.environ["SOURCE_COMMIT"] = original
        # Restore module state for other tests.
        importlib.reload(c)
