from playwright.sync_api import sync_playwright

def check(ids, subdomain):
    print(f"Checking {subdomain} IDs: {list(ids)}")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        for i in ids:
            try:
                url = f"https://{subdomain}.longshanks.org/event/{i}/"
                page.goto(url, timeout=5000)
                try: 
                    try:
                        page.wait_for_selector('.player_link', timeout=1500)
                    except:
                        # Maybe empty event
                        continue
                    
                    # Count lists
                    lists = page.evaluate("document.querySelectorAll(\"img[title='Encoded list']\").length")
                    title = page.title()
                    
                    # If lists > 0, Print
                    if lists > 0:
                        print(f"FOUND: {i} | {title} | Lists: {lists}")
                    else:
                        print(f"SKIP: {i} | Lists: 0")
                        
                except Exception as e:
                    pass
            except:
                pass
        browser.close()

if __name__ == "__main__":
    # Legacy: 29336 was good. Check near it.
    check(range(29330, 29340), "xwing-legacy")
    # XWA: 30230 was good. Check near it.
    check(range(30225, 30235), "xwing")
