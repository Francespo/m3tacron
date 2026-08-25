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
        """Enable WAL mode for better concurrent read performance."""
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL;")
        cursor.close()


def _ensure_performance_indexes(conn) -> None:
    """Create the 6 analytics hot-path indexes idempotently.

    These are required for ship-detail and card aggregations to avoid
    seq scans over 96K+ playerstanding rows (18s → 0.002s). They are NOT
    created by SQLModel's create_all — they must be declared explicitly.
    Safe to re-run on every startup (IF NOT EXISTS).
    """
    from sqlalchemy import text as _text

    indexes = [
        ("ix_playerstanding_tournament_id", "playerstanding", "tournament_id"),
        ("ix_tournament_date", "tournament", "date"),
        ("ix_tournament_source", "tournament", "source"),
        ("ix_tournament_format", "tournament", "format"),
        ("ix_playerstanding_faction_xws_normalized", "playerstanding", "faction_xws_normalized"),
        ("ix_list_faction_xws_normalized", "list", "faction_xws_normalized"),
    ]
    for name, table, col in indexes:
        try:
            conn.execute(_text(f"CREATE INDEX IF NOT EXISTS {name} ON {table} ({col})"))
        except Exception as exc:
            print(f"[startup] index {name} skipped: {exc}")


def _ensure_team_event_columns(conn) -> None:
    """Add team-event columns idempotently for stale dumps.

    The dev dump is restored on every local dev launch and may predate
    the team-event schema. Without these columns every analytics query
    that filters on is_team_event 500s and the prewarm fails.
    """
    from sqlalchemy import text as _text

    for ddl in [
        "ALTER TABLE tournament ADD COLUMN IF NOT EXISTS is_team_event boolean NOT NULL DEFAULT false",
        "ALTER TABLE playerstanding ADD COLUMN IF NOT EXISTS is_team_member boolean NOT NULL DEFAULT false",
        "CREATE TABLE IF NOT EXISTS team_member (id SERIAL PRIMARY KEY, teamstanding_id integer NOT NULL REFERENCES teamstanding(id) ON DELETE CASCADE, playerstanding_id integer NOT NULL REFERENCES playerstanding(id) ON DELETE CASCADE, list_id integer REFERENCES list(id), list_json jsonb, CONSTRAINT uq_team_member_team_player UNIQUE (teamstanding_id, playerstanding_id))",
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_team_member_player ON team_member(playerstanding_id)",
        "CREATE INDEX IF NOT EXISTS ix_team_member_teamstanding ON team_member(teamstanding_id)",
    ]:
        try:
            conn.execute(_text(ddl))
        except Exception as exc:
            print(f"[startup] team schema {ddl[:60]}... skipped: {exc}")


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)
    # Ensure team-event schema + performance indexes on every startup (idempotent).
    try:
        from sqlalchemy import text as _text

        with engine.begin() as conn:
            _ensure_team_event_columns(conn)
            _ensure_performance_indexes(conn)
    except Exception as exc:
        print(f"[startup] team/performance ensures skipped: {exc}")
    # Self-heal pilot_ship_mapping for fresh or legacy databases:
    #  - Table is declared in models.PilotShipMapping so create_all above
    #    creates it on fresh DBs.
    #  - Existing DBs (restored from dumps taken before the faction column
    #    existed) will have the 3-column table without `faction`; create_all
    #    does NOT add missing columns, so we patch the column and backfill.
    try:
        from sqlalchemy import text as _text
        from sqlmodel import Session as _Session

        with engine.begin() as conn:
            # Back-compat: add new Contribution columns for older DBs/migrations
            for ddl in [
                "ALTER TABLE contribution ADD COLUMN IF NOT EXISTS type TEXT",
                "ALTER TABLE contribution ADD COLUMN IF NOT EXISTS is_subscription_payment BOOLEAN",
                "ALTER TABLE contribution ADD COLUMN IF NOT EXISTS is_first_subscription_payment BOOLEAN",
                "ALTER TABLE contribution ADD COLUMN IF NOT EXISTS tier_name TEXT",
            ]:
                try:
                    conn.execute(_text(ddl))
                except Exception:
                    pass
            try:
                conn.execute(_text("ALTER TABLE pilot_ship_mapping ADD COLUMN IF NOT EXISTS faction TEXT"))
            except Exception:
                # SQLite < 3.?? has no IF NOT EXISTS for ADD COLUMN – check PRAGMA then add.
                try:
                    cols = [r[1] for r in conn.execute(_text("PRAGMA table_info(pilot_ship_mapping)")).fetchall()]
                    if "faction" not in cols:
                        conn.execute(_text("ALTER TABLE pilot_ship_mapping ADD COLUMN faction TEXT"))
                except Exception:
                    pass

        # Backfill missing factions from the vendored xwing manifests (idempotent).
        try:
            with _Session(engine) as session:
                try:
                    total = session.execute(_text("SELECT COUNT(*) FROM pilot_ship_mapping")).scalar() or 0
                    nulls = session.execute(_text("SELECT COUNT(*) FROM pilot_ship_mapping WHERE faction IS NULL OR faction = ''")).scalar() or 0
                except Exception:
                    total = 0
                    nulls = 0
                if total == 0 or nulls > 0:
                    # Import lazily to avoid circular import at module load.
                    try:
                        from .scripts.populate_pilot_ship_mapping import populate as _populate_psm

                        _populate_psm()
                    except Exception as exc:
                        print(f"[startup] pilot_ship_mapping backfill failed: {exc}")
                # Normalize any legacy faction values that still contain spaces/caps
                try:
                    session.execute(_text("UPDATE pilot_ship_mapping SET faction = lower(replace(replace(faction, ' ', ''), '-', '')) WHERE faction IS NOT NULL AND faction != lower(replace(replace(faction, ' ', ''), '-', ''))"))
                    session.commit()
                except Exception:
                    pass
        except Exception as exc:
            print(f"[startup] pilot_ship_mapping ensure skipped: {exc}")
    except Exception as exc:
        print(f"[startup] create_db_and_tables self-heal skipped: {exc}")
