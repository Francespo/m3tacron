
import logging
from playwright.sync_api import sync_playwright

def find_ids():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        try:
            print("Accessing Longshanks...")
            page.goto("https://xwing.longshanks.org/events/history/", timeout=90000)
            
            # Dismiss cookies
            try:
                page.click("#cookie_permission .accept", timeout=3000)
            except:
                pass

            page.wait_for_timeout(5000)
            
            # Debug: what are we seeing?
            print(f"Title: {page.title()}")
            
            # Try to find any links with /event/
            ids = page.evaluate("""() => {
                const anchors = Array.from(document.querySelectorAll('a[href*="/event/"]'));
                const distinctIds = new Set();
                
                anchors.forEach(a => {
                    const m = a.getAttribute('href').match(/\/event\/(\d+)/);
                    if (m) distinctIds.add(m[1]);
                });
                
                return Array.from(distinctIds).slice(0, 15);
            }""")
            
            print(f"IDs Found: {ids}")
            return ids
            
        except Exception as e:
            print(f"Error: {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    find_ids()
