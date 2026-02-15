
import sys
import os
import logging
from pathlib import Path

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from m3tacron.scripts.extract_data import run_url
from sqlmodel import Session, select, create_engine, SQLModel
from m3tacron.backend.models import Tournament

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test_all_urls")

# Database setup
DB_NAME = "test/full_test_v4.db"
# Remove old db if exists
if os.path.exists(DB_NAME):
    os.remove(DB_NAME)

engine = create_engine(f"sqlite:///{DB_NAME}")
SQLModel.metadata.create_all(engine)

def run():
    urls_file = Path("URLS.txt")
    if not urls_file.exists():
        logger.error(f"URLS.txt not found at {urls_file.absolute()}")
        sys.exit(1)

    with open(urls_file, "r") as f:
        urls = [line.strip() for line in f if line.strip() and not line.startswith("#")]

    logger.info(f"Found {len(urls)} URLs to test.")
    
    success_count = 0
    fail_count = 0

    for url in urls:
        logger.info(f"Processing: {url}")
        try:
            # We use run_url directly. 
            # Note: run_url internally uses its own DB session/engine if not passed?
            # extract_data.py's run_url usually expects to create its own session or takes one.
            # Looking at extract_data.py, run_url takes (url, engine).
            
            run_url(url, engine)
            success_count += 1
        except Exception as e:
            logger.error(f"Failed to process {url}: {e}")
            fail_count += 1

    logger.info(f"Finished. Success: {success_count}, Fail: {fail_count}")
    
    # Verification
    with Session(engine) as session:
        tournaments = session.exec(select(Tournament)).all()
        logger.info(f"Total Tournaments in DB: {len(tournaments)}")
        for t in tournaments:
            logger.info(f" - {t.id} ({t.platform}): {t.name} [{t.format}]")

if __name__ == "__main__":
    run()
