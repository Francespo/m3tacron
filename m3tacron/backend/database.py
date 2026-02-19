import reflex as rx
from sqlmodel import create_engine, SQLModel

# Explicitly import models to ensure they are registered with SQLModel.metadata
from .models import Tournament, PlayerResult, Match

DATABASE_URL = f"sqlite:///main.db"

engine = create_engine(DATABASE_URL)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)
