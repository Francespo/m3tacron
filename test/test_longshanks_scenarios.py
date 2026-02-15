
import sys
import os
import logging
from pathlib import Path

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from m3tacron.backend.scrapers.longshanks_scraper import LongshanksScraper
from m3tacron.backend.data_structures.scenarios import Scenario

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test_longshanks_scenarios")

def run():
    # Test with event known to have scenario issues
    event_id = "31565" 
    
    scraper = LongshanksScraper()
    logger.info(f"Testing get_matches for event {event_id}...")
    
    try:
        matches = scraper.get_matches(event_id)
        logger.info(f"Scraped {len(matches)} matches.")
        
        found_scenarios = set()
        for m in matches:
            s = m.get("scenario")
            if s and s != "unknown" and s != Scenario.OTHER_UNKNOWN:
                found_scenarios.add(s)
        
        if found_scenarios:
            logger.info(f"SUCCESS: Found scenarios: {found_scenarios}")
        else:
            logger.warning("FAILURE: No scenarios found in matches.")
            # Print sample to see what we got
            if matches:
                logger.info(f"Sample match: {matches[0]}")

    except Exception as e:
        logger.error(f"Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run()
