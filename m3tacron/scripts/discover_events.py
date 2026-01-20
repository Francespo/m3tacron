import sys
import os
import time
from playwright.sync_api import sync_playwright

def discover(subdomain, count=2):
    url = f"https://{subdomain}.longshanks.org/events/history/"
    candidates = []
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            page.goto(url)
            page.wait_for_selector('table.ranking', timeout=10000)
            
            # Scrape rows
            rows = page.evaluate("""() => {
                return Array.from(document.querySelectorAll('table.ranking tbody tr')).map(row => {
                    const cells = row.cells;
                    if (!cells || cells.length < 5) return null;
                    const link = cells[1].querySelector('a');
                    if (!link) return null;
                    const id = link.href.split('/').filter(x => x).pop();
                    const name = link.textContent.trim();
                    const players = parseInt(cells[3].textContent) || 0;
                    const status = cells[4].textContent.trim();
                    return { id, name, players, status };
                }).filter(x => x);
            }""")
            
            # Filter initial
            potential = []
            for r in rows:
                if r['players'] > 12 and "Mercoledignocchi" not in r['name'] and "Finished" in r['status']:
                    potential.append(r)
            
            print(f"[{subdomain}] Found {len(potential)} potential candidates > 12 players.")
            
            found = []
            for cand in potential:
                if len(found) >= count: break
                
                # Check Lists
                e_url = f"https://{subdomain}.longshanks.org/event/{cand['id']}/"
                print(f"Checking {cand['name']} ({cand['id']})...")
                try:
                    page.goto(e_url)
                    # Wait for players
                    try:
                        page.wait_for_selector('.player_link', timeout=5000)
                    except:
                        pass
                    
                    # Scroll to bottom to ensure lazy load?
                    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    time.sleep(1)
                    
                    list_count = page.evaluate("document.querySelectorAll(\"img[title='Encoded list']\").length")
                    print(f" -> Lists: {list_count}")
                    
                    if list_count > 4: # Accept if at least 5 lists
                        found.append(cand)
                        print("ACCEPTED.")
                except Exception as e:
                    print(f"Error checking {cand['id']}: {e}")
        except Exception as e:
            print(f"Main error: {e}")
            
        browser.close()
        return found

if __name__ == "__main__":
    print("Discovering Legacy...")
    legacy = discover("xwing-legacy", 2)
    print("Discovering XWA...")
    xwa = discover("xwing", 2)
    
    print("\nRESULTS:")
    import json
    print(json.dumps({"legacy": legacy, "xwa": xwa}, indent=2))
