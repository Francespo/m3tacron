import os
import reflex as rx
from sqlmodel import create_engine, SQLModel

# Explicitly import models to ensure they are registered with SQLModel.metadata
from .models import Tournament, PlayerResult, Match

from dotenv import load_dotenv
load_dotenv()

# Default to local sqlite if no DATABASE_URL is provided (e.g. via GitHub Secrets)
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///main.db")

# Force PostgreSQL compatibility if using Supabase (SQLModel needs 'postgresql+psycopg2://' or similar often)
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)
