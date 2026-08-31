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
