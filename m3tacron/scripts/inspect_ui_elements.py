from playwright.sync_api import sync_playwright

def inspect():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        # 1. Inspect First Player (Standard Event)
        print("--- Inspecting First Player Indicators (Event 30230) ---")
        page.goto("https://xwing-legacy.longshanks.org/event/30230/")
        
        # Remove cookie banner
        page.add_style_tag(content="#cookie_permission { display: none !important; }")
        
        page.click("#tab_games")
        page.wait_for_selector(".game")
        
        # Dump detailed structure around scores
        games = page.locator(".game").all()[:3]
        for i, game in enumerate(games):
            print(f"\nGame {i} Inner Text: {game.inner_text()!r}")
            # Check for images specifically
            imgs = game.locator("img").all()
            for img in imgs:
                src = img.get_attribute("src")
                title = img.get_attribute("title")
                print(f"  Img: src={src}, title={title}")
        
        # 2. Inspect Squad Players Tab (Event 26633)
        print("\n--- Inspecting Squad Players Tab (Event 26633) ---")
        page.goto("https://xwing-legacy.longshanks.org/event/26633/")
        page.wait_for_load_state("networkidle")
        
        # Remove cookie banner
        page.add_style_tag(content="#cookie_permission { display: none !important; }")

        # Dump "tabs" area
        # Usually internal links at the top
        print("Dumping all links with class 'tab':")
        # Try generic selector if a.tab fails
        tabs_area = page.msg_selector = page.locator(".tabwrapper, #tabs, .tabs, .menu").first
        if tabs_area.count() > 0:
             print(f"Tabs Area HTML: {tabs_area.evaluate('el => el.innerHTML')}")
        else:
             # Just dump all links
             links = page.locator("a").all()
             print(f"Found {len(links)} links on page. Listing potential tabs:")
             for link in links:
                 cls = link.get_attribute("class")
                 if cls and "tab" in cls:
                     print(f"  Tab Link: {link.evaluate('el => el.outerHTML')}")
        
        # User said "icona dell'omino" (little man)
        # Search for icon classes
        icons = page.locator("i.fa, span.icon").all()
        for icon in icons:
             cls = icon.get_attribute("class")
             parent = icon.locator("..").evaluate("el => el.outerHTML")
             print(f"  Icon: {cls} inside {parent}")
             
        browser.close()

if __name__ == "__main__":
    inspect()
