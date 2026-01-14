import os
from sqlmodel import create_engine, SQLModel, Session

# Default to SQLite for local development if no env var is set
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./metacron.db")

# Creation of the engine
engine = create_engine(DATABASE_URL, echo=False)

def create_db_and_tables():
    """Create the database and tables."""
    SQLModel.metadata.create_all(engine)

def get_session():
    """Dependency to get a database session."""
    with Session(engine) as session:
        yield session
