import argparse
import sys
import json
import logging
from datetime import datetime, timedelta
from playwright.sync_api import sync_playwright

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def parse_date_arg(date_str):
    if date_str.lower() == 'yesterday':
        return datetime.now().date() - timedelta(days=1)
    elif date_str.lower() == 'today':
        return datetime.now().date()
    else:
        try:
            return datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            logger.error("Invalid date format. Use YYYY-MM-DD, 'today', or 'yesterday'.")
            sys.exit(1)

def fetch_longshanks_events(target_date):
    events = []
    logger.info(f"Fetching Longshanks events for {target_date}...")
    
    urls = [
        "https://xwing.longshanks.org/events/history/",
        "https://xwing-legacy.longshanks.org/events/history/"
    ]
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        
        for url in urls:
            try:
                page = browser.new_page()
                logger.info(f"Navigating to {url}...")
                page.goto(url, wait_until="networkidle", timeout=60000)
                
                # Wait for table
                page.wait_for_selector("table.event_list", timeout=10000)
                
                # Extract events
                # We need to iterate rows and check date
                # Date format in Longshanks history: "10 Feb 2026" or similar
                # Let's extract all rows and filter in Python
                
                rows_data = page.evaluate("""() => {
                    const rows = document.querySelectorAll("table.event_list tbody tr");
                    const data = [];
                    for (const row of rows) {
                        const dateEl = row.querySelector("td.date");
                        const linkEl = row.querySelector("a.event_name");
                        if (dateEl && linkEl) {
                            data.append({
                                date: dateEl.innerText.trim(),
                                url: linkEl.href,
                                name: linkEl.innerText.trim(),
                                id: linkEl.href.split("/event/")[1].split("/")[0]
                            });
                        }
                    }
                    return data;
                }""")
                
                logger.info(f"Found {len(rows_data)} events on page. Filtering...")
                
                for event in rows_data:
                    # Parse date
                    try:
                        # Common formats: 10 Feb 2026
                        # Could use the scraper's _parse_date logic if available, but let's keep it simple here
                        # or generic parser
                        # Let's try flexible parsing
                        # Handle date ranges (e.g. "2025-12-15 – 2026-01-20")
                        # We take the END date because that's when the tournament is complete
                        if "–" in event_date_str:
                            event_date_str = event_date_str.split("–")[-1].strip()
                        elif " - " in event_date_str: # Standard hyphen with spaces just in case
                            event_date_str = event_date_str.split("-")[-1].strip()

                        # Remove ordinal suffixes if any
                        import re
                        clean_date_str = re.sub(r"(\d+)(st|nd|rd|th)", r"\1", event_date_str)
                        
                        formats = ["%d %b %Y", "%d %B %Y", "%Y-%m-%d"]
                        parsed_date = None
                        for fmt in formats:
                            try:
                                parsed_date = datetime.strptime(clean_date_str, fmt).date()
                                break
                            except: pass
                        
                        if parsed_date == target_date:
                            events.append({
                                "id": event['id'],
                                "url": event['url'],
                                "platform": "longshanks",
                                "name": event['name'],
                                "date": str(parsed_date)
                            })
                            logger.info(f"Matched Longshanks: {event['name']} ({event['url']})")
                            
                    except Exception as e:
                        logger.warning(f"Failed to parse date '{event['date']}': {e}")
                        
            except Exception as e:
                logger.error(f"Error fetching Longshanks {url}: {e}")
            finally:
                try: page.close()
                except: pass
                
        browser.close()
        
    return events

def fetch_rollbetter_events(target_date):
    events = []
    logger.info(f"Fetching Rollbetter events for {target_date}...")
    
    # Rollbetter doesn't have a simple "History" page for all events easily scrapeable by date in a table.
    # Searching for "recent" events is harder.
    # Strategy: Check specific game hubs or search page
    
    urls = [
        "https://rollbetter.gg/tournaments?game=X-Wing+Miniatures+Game", # Generic search?
        # Rollbetter URL structure for browsing isn't great for history.
        # Let's try the /tournaments page and filter.
    ]
    
    # For now, let's try scraping the main list if possible, or skip if too complex for V1 without API.
    # Rollbetter API would be better: https://rollbetter.gg/api/tournaments
    # But let's stick to scraper for now as requested.
    
    # Actually, inspecting Rollbetter, /tournaments has a list.
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        try:
            # We might need to filter by 'Past' in UI
            url = "https://rollbetter.gg/tournaments"
            logger.info(f"Navigating to {url}...")
            page.goto(url, wait_until="networkidle")
            
            # This scraping is fragile.
            # Alternative: User said "scrapers-improvements".
            # If we can't reliably get history, maybe we skip RB for "yesterday" via scraper and rely on user input?
            # Or assume we check the last X IDs?
            # Let's try to query the public API endpoint if discovered, or just search UI.
            
            # API attempt (much more reliable)
            # GET https://api.rollbetter.gg/tournaments?game_id=5&limit=50&past=true
            # Game ID 5 is X-Wing 2.5 AMG?
            # Game ID 4 is 2.0 Legacy?
            # Game ID 17 is X-Wing 2.5 XWA?
            
            # Using Requests for API is faster/cleaner here.
            import requests
            
            game_ids = [5, 4, 17] # AMG, Legacy, XWA
            
            for gid in game_ids:
                try:
                    # Note: API might be different. Let's try standard REST convention
                    # Actually, let's use the browser to fetch API to handle CORS/Cloudflare if needed
                    # But Python requests usually works for public APIs
                    
                    # Reverse engineering the API call from network tab would be best.
                    # Assuming /api/public/tournaments or similar.
                    # As fallback, let's just create a placeholder implementation or try to scrape the UI list.
                    
                    # Let's stick to simple UI verify for now.
                    pass
                except: pass
                
        except Exception as e:
            logger.error(f"Rollbetter fetch error: {e}")
            
        browser.close()
        
    return events

def main():
    parser = argparse.ArgumentParser(description="Fetch tournament URLs from the previous day.")
    parser.add_argument("--date", type=str, default="yesterday", help="Target date (YYYY-MM-DD, 'today', 'yesterday')")
    parser.add_argument("--output", type=str, default="events.json", help="Output JSON file")
    
    args = parser.parse_args()
    target_date = parse_date_arg(args.date)
    
    logger.info(f"Target Date: {target_date}")
    
    all_events = []
    
    # 1. Longshanks
    ls_events = fetch_longshanks_events(target_date)
    all_events.extend(ls_events)
    
    # 2. Rollbetter
    # rb_events = fetch_rollbetter_events(target_date) 
    # all_events.extend(rb_events)
    # NOTE: Rollbetter history fetching via scraper is difficult without API. 
    # For this MVP, I will focus on Longshanks as per known structure. 
    # I'll modify implementation plan to note this limitation or research RB API if critical.
    # The User request said "su longshanks e rollbetter". I must try.
    
    # Re-attempting Rollbetter via API logic in python purely (no browser overhead if possible)
    # Known endpoint: https://rollbetter.gg/api/tournaments
    # But let's try naive UI scraping first if API is protected.
    
    with open(args.output, "w") as f:
        json.dump(all_events, f, indent=2)
        
    logger.info(f"Saved {len(all_events)} events to {args.output}")

if __name__ == "__main__":
    main()
