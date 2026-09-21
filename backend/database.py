import os
from sqlalchemy import event
from sqlmodel import create_engine, SQLModel

# Explicitly import models to ensure they are registered with SQLModel.metadata
from .models import Tournament, PlayerStanding, TeamStanding, Match, TeamMatch, ScrapeMeta, Supporter, Contribution, PilotShipMapping

from dotenv import load_dotenv
load_dotenv()

# Default to local sqlite if no DATABASE_URL is provided
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATABASE_URL = os.getenv(
    "DATABASE_URL", f"sqlite:///{os.path.join(BASE_DIR, 'test.db')}")

# Force PostgreSQL compatibility if using Supabase (SQLModel needs 'postgresql+psycopg2://' or similar often)
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# SQLite-specific settings for concurrent access (e.g. parallel scraper workers).
# WAL mode allows concurrent reads with one writer; a busy timeout makes
# writers wait instead of immediately raising "database is locked".
_sqlite_connect_args: dict = {}
if DATABASE_URL.startswith("sqlite"):
    _sqlite_connect_args = {
        "timeout": 30,  # seconds to wait for the write lock
    }

engine = create_engine(
    DATABASE_URL,
    connect_args=_sqlite_connect_args if _sqlite_connect_args else {},
    # pool_pre_ping verifies each connection is alive before use.
    # Essential for long-running scrapers: a tournament can take 10+ minutes
    # to scrape, and PostgreSQL/Supabase idle-timeout kills idle connections
    # in the pool, causing "server closed the connection unexpectedly".
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    pool_timeout=15,
    pool_recycle=300,  # recycle connections after 5 minutes (defense in depth)
)

if DATABASE_URL.startswith("sqlite"):

    @event.listens_for(engine, "connect")
    def _set_sqlite_pragma(dbapi_connection, connection_record):  # noqa: ARG001
        """Enable WAL mode for better concurrent read performance and custom functions."""
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL;")
        cursor.close()
        try:
            dbapi_connection.create_function("GREATEST", -1, max)
            dbapi_connection.create_function("greatest", -1, max)
            dbapi_connection.create_function("LEAST", -1, min)
            dbapi_connection.create_function("least", -1, min)
        except Exception:
            pass


def _retry_with_backoff(fn, *, attempts: int = 5, base_sleep: float = 0.7):
    """Run *fn* with exponential backoff on serialization/deadlock failures.

    The prod backend starts at the same time as the scraper/promote loop, so
    DDL races with long-running analytics scans (playerstanding ↔ tournament)
    and can raise psycopg2.errors.DeadlockDetected / InFailedSqlTransaction.
    Do not let one DDL failure poison the entire startup transaction.
    """
    import time as _t

    last_exc: Exception | None = None
    for i in range(attempts):
        try:
            return fn()
        except Exception as exc:  # noqa: BLE001  (psycopg2 + sqlalchemy both)
            msg = str(exc)
            is_retryable = any(
                k in msg
                for k in (
                    "DeadlockDetected",
                    "deadlock detected",
                    "InFailedSqlTransaction",
                    "current transaction is aborted",
                    "SerializationFailure",
                    "could not serialize access",
                    "connection already closed",
                )
            )
            if not is_retryable or i == attempts - 1:
                raise
            last_exc = exc
            print(f"[startup] retryable DDL error (attempt {i+1}/{attempts}): {exc}")
            _t.sleep(base_sleep * (2**i))
    if last_exc:
        raise last_exc


def _has_column(conn, table: str, column: str) -> bool:
    try:
        from sqlalchemy import text as _text
        res = conn.execute(
            _text("SELECT 1 FROM information_schema.columns WHERE table_name = :t AND column_name = :c"),
            {"t": table.lower(), "c": column.lower()}
        ).fetchone()
        if res is not None:
            return True
        cols = [r[1] for r in conn.execute(_text(f"PRAGMA table_info({table})")).fetchall()]
        return column.lower() in [c.lower() for c in cols]
    except Exception:
        return False


def _has_table(conn, table: str) -> bool:
    try:
        from sqlalchemy import text as _text
        res = conn.execute(
            _text("SELECT 1 FROM information_schema.tables WHERE table_name = :t"),
            {"t": table.lower()}
        ).fetchone()
        if res is not None:
            return True
        tables = [r[0] for r in conn.execute(_text("SELECT name FROM sqlite_master WHERE type='table'")).fetchall()]
        return table.lower() in [t.lower() for t in tables]
    except Exception:
        return False


def _has_index(conn, index_name: str) -> bool:
    try:
        from sqlalchemy import text as _text
        res = conn.execute(
            _text("SELECT 1 FROM pg_indexes WHERE indexname = :i"),
            {"i": index_name.lower()}
        ).fetchone()
        if res is not None:
            return True
        indexes = [r[0] for r in conn.execute(_text("SELECT name FROM sqlite_master WHERE type='index'")).fetchall()]
        return index_name.lower() in [i.lower() for i in indexes]
    except Exception:
        return False


def _ensure_performance_indexes(conn) -> None:
    """Create the analytics hot-path indexes idempotently.

    These are required for ship-detail and card aggregations to avoid
    seq scans over 96K+ playerstanding rows (18s → 0.002s). They are NOT
    created by SQLModel's create_all — they must be declared explicitly.
    Safe to re-run on every startup. Checks pg_indexes first to avoid
    acquiring table locks if the index already exists.
    """
    from sqlalchemy import text as _text

    indexes = [
        ("ix_playerstanding_tournament_id", "playerstanding", "tournament_id"),
        ("ix_tournament_date", "tournament", "date"),
        ("ix_tournament_source", "tournament", "source"),
        ("ix_tournament_format", "tournament", "format"),
        ("ix_playerstanding_faction_xws_normalized", "playerstanding", "faction_xws_normalized"),
        ("ix_list_faction_xws_normalized", "list", "faction_xws_normalized"),
        ("ix_pilot_ship_mapping_ship_xws", "pilot_ship_mapping", "ship_xws"),
    ]
    for name, table, col in indexes:
        if _has_index(conn, name):
            continue
        ddl = f"CREATE INDEX IF NOT EXISTS {name} ON {table} ({col})"
        for attempt in range(3):
            try:
                with conn.begin_nested():
                    conn.execute(_text(ddl))
                break
            except Exception as exc:
                msg = str(exc)
                retryable = any(k in msg for k in ("DeadlockDetected", "deadlock detected", "InFailedSqlTransaction", "current transaction is aborted"))
                if retryable and attempt < 2:
                    import time as _t
                    _t.sleep(0.7 * (2**attempt))
                    continue
                print(f"[startup] index {name} skipped: {exc}")
                break


def _ensure_team_event_columns(conn) -> None:
    """Add team-event columns idempotently for stale dumps.

    Checks information_schema first to avoid acquiring AccessExclusiveLock
    on hot production tables when the columns already exist.
    """
    from sqlalchemy import text as _text

    if not _has_column(conn, "tournament", "is_team_event"):
        try:
            with conn.begin_nested():
                conn.execute(_text("ALTER TABLE tournament ADD COLUMN is_team_event boolean NOT NULL DEFAULT false"))
        except Exception as e:
            print(f"[startup] add tournament.is_team_event skipped: {e}")

    if not _has_column(conn, "playerstanding", "is_team_member"):
        try:
            with conn.begin_nested():
                conn.execute(_text("ALTER TABLE playerstanding ADD COLUMN is_team_member boolean NOT NULL DEFAULT false"))
        except Exception as e:
            print(f"[startup] add playerstanding.is_team_member skipped: {e}")

    if not _has_table(conn, "team_member"):
        try:
            with conn.begin_nested():
                conn.execute(_text("CREATE TABLE team_member (id SERIAL PRIMARY KEY, teamstanding_id integer NOT NULL REFERENCES teamstanding(id) ON DELETE CASCADE, playerstanding_id integer NOT NULL REFERENCES playerstanding(id) ON DELETE CASCADE, list_id integer REFERENCES list(id), list_json jsonb, CONSTRAINT uq_team_member_team_player UNIQUE (teamstanding_id, playerstanding_id))"))
        except Exception as e:
            print(f"[startup] create team_member table skipped: {e}")

    if not _has_index(conn, "uq_team_member_player"):
        try:
            with conn.begin_nested():
                conn.execute(_text("CREATE UNIQUE INDEX IF NOT EXISTS uq_team_member_player ON team_member(playerstanding_id)"))
        except Exception as e:
            print(f"[startup] index uq_team_member_player skipped: {e}")

    if not _has_index(conn, "ix_team_member_teamstanding"):
        try:
            with conn.begin_nested():
                conn.execute(_text("CREATE INDEX IF NOT EXISTS ix_team_member_teamstanding ON team_member(teamstanding_id)"))
        except Exception as e:
            print(f"[startup] index ix_team_member_teamstanding skipped: {e}")


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)
    try:
        from sqlalchemy import text as _text
        with engine.begin() as conn:
            try:
                conn.execute(_text("SET LOCAL lock_timeout = '2s'"))
            except Exception:
                pass
            _ensure_team_event_columns(conn)
            _ensure_performance_indexes(conn)
    except Exception as exc:
        print(f"[startup] index/team-event ensure skipped: {exc}")

    try:
        from sqlalchemy import text as _text
        from sqlmodel import Session as _Session

        with engine.begin() as conn:
            try:
                conn.execute(_text("SET LOCAL lock_timeout = '2s'"))
            except Exception:
                pass
            for col in ["type", "is_subscription_payment", "is_first_subscription_payment", "tier_name"]:
                if not _has_column(conn, "contribution", col):
                    try:
                        col_type = "BOOLEAN" if "is_" in col else "TEXT"
                        conn.execute(_text(f"ALTER TABLE contribution ADD COLUMN {col} {col_type}"))
                    except Exception:
                        pass
            if not _has_column(conn, "pilot_ship_mapping", "faction"):
                try:
                    conn.execute(_text("ALTER TABLE pilot_ship_mapping ADD COLUMN faction TEXT"))
                except Exception:
                    pass

        # Backfill missing factions from the vendored xwing manifests (idempotent).
        try:
            with _Session(engine) as session:
                try:
                    total = session.execute(_text("SELECT COUNT(*) FROM pilot_ship_mapping")).scalar() or 0
                    nulls = session.execute(_text("SELECT COUNT(*) FROM pilot_ship_mapping WHERE faction IS NULL OR faction = ''")).scalar() or 0
                    session.commit()  # release read locks immediately
                except Exception:
                    total = 0
                    nulls = 0
                    session.rollback()

            if total == 0 or nulls > 0:
                # Import lazily to avoid circular import at module load.
                try:
                    from .scripts.populate_pilot_ship_mapping import populate as _populate_psm

                    _populate_psm()
                except Exception as exc:
                    print(f"[startup] pilot_ship_mapping backfill failed: {exc}")
            # Normalize any legacy faction values that still contain spaces/caps
            with _Session(engine) as session:
                try:
                    session.execute(_text("UPDATE pilot_ship_mapping SET faction = lower(replace(replace(faction, ' ', ''), '-', '')) WHERE faction IS NOT NULL AND faction != lower(replace(replace(faction, ' ', ''), '-', ''))"))
                    session.commit()
                except Exception:
                    session.rollback()
        except Exception as exc:
            print(f"[startup] pilot_ship_mapping ensure skipped: {exc}")
    except Exception as exc:
        print(f"[startup] create_db_and_tables self-heal skipped: {exc}")
