import os
import pickle
import time

import backend.cache as c


def _isolate(monkeypatch, tmp_path, version, entries=None):
    """Point the cache at a temp dir with a fixed version and no version check."""
    monkeypatch.setattr(c, "CACHE_DIR", tmp_path)
    monkeypatch.setattr(c, "_cached_version", version)
    monkeypatch.setattr(c, "_cache", dict(entries or {}))
    monkeypatch.setattr(c, "_disk_mtime", 0.0)
    monkeypatch.setattr(c, "_last_version_check", time.monotonic())


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


def test_has_cached_reflects_cache_state():
    """The pre-warmer uses has_cached to skip work that is already done."""
    c._cache.clear()
    c._cached_version = "300"
    c._last_version_check = 0
    c._get_db_version = lambda: "300"

    assert c.has_cached("warm|missing") is False

    c.get_cached_or_compute("warm|present", lambda: {"ok": True})
    assert c.has_cached("warm|present") is True

    # A data_version bump clears the cache, so nothing is "cached" any more.
    c._last_version_check = 0
    c._get_db_version = lambda: "301"
    assert c.has_cached("warm|present") is False

    c.invalidate_cache()


def test_disk_save_is_throttled(monkeypatch, tmp_path):
    """A write must not dump the whole pickle every few keys.

    Re-dumping on every 10th key wrote hundreds of MB per minute during
    warm-up on production. Only one save per interval is allowed.
    """
    _isolate(monkeypatch, tmp_path, "900")
    monkeypatch.setattr(c, "_last_save_at", time.monotonic())

    c.get_cached_or_compute("k1", lambda: 1)
    assert list(tmp_path.glob("api_cache_*.pkl")) == []

    # Pretend the interval elapsed: the next write persists everything.
    monkeypatch.setattr(c, "_last_save_at", time.monotonic() - c.SAVE_MIN_INTERVAL - 1)
    c.get_cached_or_compute("k2", lambda: 2)

    files = list(tmp_path.glob("api_cache_*.pkl"))
    assert len(files) == 1
    with open(files[0], "rb") as f:
        data = pickle.load(f)
    assert data["k1"] == 1 and data["k2"] == 2


def test_worker_adopts_snapshot_written_by_another_worker(monkeypatch, tmp_path):
    """Only one worker warms; the others must load its snapshot, not stay cold."""
    _isolate(monkeypatch, tmp_path, "901")

    path = c._get_cache_file_path("901")
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "wb") as f:
        pickle.dump({"warm|key": {"value": 42}}, f)

    assert c._cache == {}
    assert c._reload_disk_cache_if_newer() == 1
    assert c._cache["warm|key"] == {"value": 42}

    # Nothing new: a second poll is a no-op.
    assert c._reload_disk_cache_if_newer() == 0


def test_save_merges_newer_snapshot_instead_of_shrinking_it(monkeypatch, tmp_path):
    """A worker with a partial cache must not overwrite the full snapshot."""
    _isolate(monkeypatch, tmp_path, "902", {"local": 1})

    path = c._get_cache_file_path("902")
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "wb") as f:
        pickle.dump({"local": 99, "from_other_worker": 2}, f)

    c._save_disk_cache("902")

    with open(path, "rb") as f:
        data = pickle.load(f)
    assert data["from_other_worker"] == 2
    assert data["local"] == 99
    assert "abc" not in data


def test_purge_removes_stale_pickles_only(monkeypatch, tmp_path):
    """Files from old fingerprints pile up (hundreds of MB); stale ones go."""
    _isolate(monkeypatch, tmp_path, "903")
    current = c._get_cache_file_path("903")
    current.write_bytes(b"current")
    stale = tmp_path / "api_cache_1_oldfingerprint.pkl"
    stale.write_bytes(b"stale")
    recent = tmp_path / "api_cache_1_otherfingerprint.pkl"
    recent.write_bytes(b"recent")

    old = time.time() - c.STALE_CACHE_MIN_AGE - 60
    os.utime(stale, (old, old))
    os.utime(current, (old, old))

    c._purge_old_disk_caches("903")

    assert not stale.exists()
    assert current.exists()
    assert recent.exists()


def test_version_change_keeps_serving_stale_until_refreshed(monkeypatch, tmp_path):
    """A scrape must not turn every page cold while the warm rebuilds."""
    _isolate(monkeypatch, tmp_path, "910", {"k": "old"})
    monkeypatch.setattr(c, "_last_version_check", 0)
    monkeypatch.setattr(c, "_get_db_version", lambda: "911")
    assert c.cache_is_stale() is False

    # Version bumped: the previous generation is still served.
    assert c.get_cached_or_compute("k", lambda: "new") == "old"
    assert c.cache_is_stale() is True
    # ...but the warm must not think the key is already fresh.
    assert c.has_cached("k") is False

    token = c.set_force_refresh(True)
    try:
        assert c.get_cached_or_compute("k", lambda: "new") == "new"
    finally:
        c.reset_force_refresh(token)
    assert c.has_cached("k") is True


def test_stale_generation_expires(monkeypatch, tmp_path):
    """Old data is served only for a bounded window, then recomputed."""
    _isolate(monkeypatch, tmp_path, "920", {"k": "old"})
    monkeypatch.setattr(c, "_last_version_check", 0)
    monkeypatch.setattr(c, "_get_db_version", lambda: "921")
    assert c.get_cached_or_compute("k", lambda: "new") == "old"

    monkeypatch.setattr(c, "_stale_until", time.monotonic() - 1)
    assert c.get_cached_or_compute("k", lambda: "new") == "new"


def test_force_refresh_does_not_force_nested_helpers(monkeypatch, tmp_path):
    """Only the outermost lookup recomputes; helper caches stay warm."""
    _isolate(monkeypatch, tmp_path, "930", {"inner": "cached"})
    token = c.set_force_refresh(True)
    try:
        result = c.get_cached_or_compute(
            "outer", lambda: ("recomputed", c.get_cached_or_compute("inner", lambda: "computed"))
        )
    finally:
        c.reset_force_refresh(token)
    assert result == ("recomputed", "cached")
