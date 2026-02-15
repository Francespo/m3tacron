import random
import subprocess
import sys
import os
import logging
from sqlalchemy import create_engine, text

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

URLS_FILE = "URLS.txt"
TEST_DB = "regression_test.db"
REF_DB = "maybe_working.db"

def get_random_urls(n=5):
    with open(URLS_FILE, 'r') as f:
        lines = [line.strip() for line in f if line.strip()]
    return random.sample(lines, min(n, len(lines)))

def run_extraction(urls):
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)
    
    cmd = [sys.executable, "-m", "m3tacron.scripts.extract_data", "--db", TEST_DB] + urls
    logger.info(f"Running extraction for {len(urls)} URLs...")
    subprocess.check_call(cmd)

def compare_dbs(urls):
    ref_engine = create_engine(f"sqlite:///{REF_DB}")
    test_engine = create_engine(f"sqlite:///{TEST_DB}")

    with ref_engine.connect() as ref_conn, test_engine.connect() as test_conn:
        for url in urls:
            # Extract ID from URL
            tid = url.rstrip('/').split('/')[-1]
            logger.info(f"--- Checking Tournament ID: {tid} ({url}) ---")

            # 1. Compare Tournament Data
            t_query = text("SELECT name, date, player_count, format FROM tournament WHERE id = :tid")
            ref_t = ref_conn.execute(t_query, {"tid": tid}).fetchone()
            test_t = test_conn.execute(t_query, {"tid": tid}).fetchone()

            if not ref_t:
                logger.warning(f"Tournament {tid} not found in reference DB. Skipping comparison.")
                continue
            
            if not test_t:
                logger.error(f"Tournament {tid} failed to scrape (not in test DB).")
                continue

            # Compare fields
            fields = ["name", "date", "player_count", "format"]
            files_match = True
            for i, field in enumerate(fields):
                if str(ref_t[i]) != str(test_t[i]):
                    logger.warning(f"MISMATCH {field}: Ref='{ref_t[i]}' vs Test='{test_t[i]}'")
                    files_match = False
            
            if files_match:
                logger.info(f"Tournament metadata matches.")

            # 2. Compare Player Counts
            p_query = text("SELECT COUNT(*) FROM playerresult WHERE tournament_id = :tid")
            ref_p_count = ref_conn.execute(p_query, {"tid": tid}).scalar()
            test_p_count = test_conn.execute(p_query, {"tid": tid}).scalar()

            if ref_p_count != test_p_count:
                logger.warning(f"PLAYER COUNT MISMATCH: Ref={ref_p_count} vs Test={test_p_count}")
            else:
                logger.info(f"Player count matches ({ref_p_count}).")

            # 3. Compare Match Counts
            m_query = text("SELECT COUNT(*) FROM match WHERE tournament_id = :tid")
            ref_m_count = ref_conn.execute(m_query, {"tid": tid}).scalar()
            test_m_count = test_conn.execute(m_query, {"tid": tid}).scalar()

            if ref_m_count != test_m_count:
                logger.warning(f"MATCH COUNT MISMATCH: Ref={ref_m_count} vs Test={test_m_count}")
            else:
                logger.info(f"Match count matches ({ref_m_count}).")

if __name__ == "__main__":
    urls = get_random_urls(5)
    logger.info(f"Selected URLs: {urls}")
    try:
        run_extraction(urls)
        compare_dbs(urls)
        logger.info("Verification complete.")
    except Exception as e:
        logger.error(f"Test failed: {e}")
        sys.exit(1)
