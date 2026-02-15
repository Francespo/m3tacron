import sys
import logging
from m3tacron.backend.scrapers.listfortress_scraper import ListFortressScraper
from m3tacron.backend.models import Tournament

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test_listfortress")

def test_fetch_tournament():
    scraper = ListFortressScraper()
    # Test with tournament ID 360 (known from research)
    tid = "360" 
    logger.info(f"Fetching tournament {tid}...")
    
    # 1. Get Participants
    players = scraper.get_participants(tid)
    logger.info(f"Found {len(players)} players.")
    if len(players) > 0:
        logger.info(f"Sample player: {players[0].player_name} (Rank: {players[0].swiss_rank})")
        if players[0].list_json:
            logger.info("XWS data found.")
    else:
        logger.error("No players found!")
        sys.exit(1)

    # 2. Get Metadata
    t_data = scraper.get_tournament_data(tid)
    logger.info(f"Tournament: {t_data.name} | Date: {t_data.date} | Format: {t_data.format}")
    if t_data.name == "Element Games X-wing 19/02/19":
        logger.info("Metadata matches expected.")
    else:
        logger.warning(f"Metadata name mismatch: {t_data.name}")

    # 3. Get Matches (Expected empty for 360)
    matches = scraper.get_matches(tid)
    logger.info(f"Found {len(matches)} matches.")
    # ID 360 had empty rounds in research, so 0 is expected.
    
    # 4. Test ID 261 (Has matches)
    tid2 = "261"
    logger.info(f"Fetching tournament {tid2} (expecting matches)...")
    matches2 = scraper.get_matches(tid2)
    logger.info(f"Found {len(matches2)} matches for {tid2}.")
    if len(matches2) > 0:
        logger.info(f"Sample match: R{matches2[0]['round_number']} {matches2[0]['p1_name_temp']} vs {matches2[0]['p2_name_temp']}")
    else:
        logger.warning(f"No matches found for {tid2}, expected some.")

if __name__ == "__main__":
    test_fetch_tournament()
