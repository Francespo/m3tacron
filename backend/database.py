import os
from sqlalchemy import event
from sqlmodel import create_engine, SQLModel

# Explicitly import models to ensure they are registered with SQLModel.metadata
from .models import Tournament, PlayerStanding, TeamStanding, Match, TeamMatch, ScrapeMeta, Supporter, Contribution

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


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)
