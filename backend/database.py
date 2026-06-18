import os
from sqlmodel import create_engine, SQLModel

from .models import Tournament, PlayerResult, Match, Supporter, Contribution

from dotenv import load_dotenv
load_dotenv()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _build_database_url():
    explicit = os.getenv("DATABASE_URL")
    if explicit:
        return explicit
    host = os.getenv("LOCAL_DB_HOST")
    if host:
        port = os.getenv("LOCAL_DB_PORT", "5432")
        name = os.getenv("LOCAL_DB_NAME", "m3tacron_perf")
        user = os.getenv("LOCAL_DB_USER", "perf_user")
        password = os.getenv("LOCAL_DB_PASSWORD", "perf_password")
        return f"postgresql://{user}:{password}@{host}:{port}/{name}"
    return f"sqlite:///{os.path.join(BASE_DIR, 'test.db')}"


DATABASE_URL = _build_database_url()

if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)
