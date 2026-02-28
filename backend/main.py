from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

from .database import create_db_and_tables

app = FastAPI(title="M3taCron Backend", version="1.0.0")

# Configure CORS for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    create_db_and_tables()

@app.get("/")
def read_root():
    return {"status": "Backend is running"}

# TODO: Add your routers here
# app.include_router(tournaments.router)
