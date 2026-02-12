"""Verification script: Scrape 5 tournaments and verify match counts."""
import sys
import os
import random
import logging
from sqlalchemy import create_engine, text

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from m3tacron.scripts.extract_data import run_url

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("verify_fix")

DB_path = "test/match_fix_verification.db"
DB_URL = f"sqlite:///{DB_path}"

# Known URLs to test specific fixes + randoms
FIX_TARGETS = [
    "https://xwing.longshanks.org/event/31565/",  # Longshanks (was 0 matches)
    "https://rollbetter.gg/tournaments/2444",     # Rollbetter (was 2 rounds)
]

def get_random_urls(count=3):
    urls = []
    try:
        with open("URLS.txt", "r") as f:
            lines = [l.strip() for l in f if l.strip() and not l.startswith("#")]
            # Filter out the fix targets to avoid duplicates
            pool = [l for l in lines if l not in FIX_TARGETS]
            if len(pool) >= count:
                urls = random.sample(pool, count)
            else:
                urls = pool
    except FileNotFoundError:
        logger.warning("URLS.txt not found, using only fix targets.")
    return urls

def verify_matches(engine):
    logger.info("\n--- Verification Report ---")
    with engine.connect() as conn:
        tournaments = conn.execute(text("SELECT id, name, player_count, platform FROM tournament")).fetchall()
        
        all_passed = True
        for t in tournaments:
            tid, name, p_count, platform = t
            
            # Count matches
            m_count = conn.execute(text("SELECT COUNT(*) FROM match WHERE tournament_id = :tid"), {"tid": tid}).scalar()
            
            # Count rounds
            r_count = conn.execute(text("SELECT COUNT(DISTINCT round_number) FROM match WHERE tournament_id = :tid"), {"tid": tid}).scalar()
            
            logger.info(f"[{platform}] {name} (ID: {tid})")
            logger.info(f"  Players: {p_count}")
            logger.info(f"  Matches: {m_count}")
            logger.info(f"  Rounds:  {r_count}")
            
            if m_count == 0 and p_count > 1:
                logger.error("  FAIL: 0 matches found!")
                all_passed = False
            elif m_count > 0:
                logger.info("  OK: Matches found.")
            else:
                logger.warning("  WARN: 0 matches (might be empty/upcoming).")
                
            logger.info("-" * 30)
            
        return all_passed

def main():
    # 1. Clean up old DB
    if os.path.exists(DB_path):
        os.remove(DB_path)
        
    # 2. Select URLs
    target_urls = FIX_TARGETS + get_random_urls(3)
    logger.info(f"Selected {len(target_urls)} URLs for verification.")
    
    # 3. Scrape
    engine = create_engine(DB_URL)
    for url in target_urls:
        run_url(url, engine)
        
    # 4. Verify
    if verify_matches(engine):
        logger.info("\nSUCCESS: All data verification checks passed.")
        sys.exit(0)
    else:
        logger.error("\nFAILURE: Some checks failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()
