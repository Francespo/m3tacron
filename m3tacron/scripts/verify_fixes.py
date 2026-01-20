from m3tacron.backend.scrapers.longshanks import LongshanksScraper
from m3tacron.backend.models import Tournament

def verify():
    scraper = LongshanksScraper()
    
    events = [
        {"id": 30230, "name": "PSO Lomza (Round Counts)"},
        {"id": 26633, "name": "Grandpa's Cup (Squads)"},
        {"id": 31565, "name": "MTC (General)"}
    ]
    
    for event in events:
        print(f"\n--- Verifying {event['name']} ({event['id']}) ---")
        t = Tournament(id=event['id'], name=event['name'], url=f"https://xwing-legacy.longshanks.org/event/{event['id']}/")
        
        try:
            matches = scraper.get_matches(str(t.id))
            print(f"Total Matches: {len(matches)}")
            
            # Round analysis
            rounds = {}
            for m in matches:
                r = m.round_number
                rounds[r] = rounds.get(r, 0) + 1
                
            print(f"Matches per Round: {dict(sorted(rounds.items()))}")
            
            # ID check
            with_ids = sum(1 for m in matches if m.player1_id is not None and m.player2_id is not None)
            print(f"Matches with fully resolved IDs: {with_ids}/{len(matches)}")
            
        except Exception as e:
            print(f"FAILED: {e}")

if __name__ == "__main__":
    verify()
