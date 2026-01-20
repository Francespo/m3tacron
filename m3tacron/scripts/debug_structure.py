from playwright.sync_api import sync_playwright
import logging
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("debug_structure")

def debug_longshanks():
    url = "https://xwing-legacy.longshanks.org/event/29336/"
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        logger.info(f"Navigating to {url}")
        page.goto(url)
        page.add_style_tag(content="#cookie_permission { display: none !important; }")
        page.wait_for_timeout(3000)

        # 1. Inspect Player Structure (Points)
        logger.info("Inspecting Player Structure...")
        player_debug = page.evaluate("""() => {
            const p = document.querySelector('.player:not(.accordion)');
            if(!p) return "No player found";
            
            const dataEl = p.querySelector('.data');
            if(!dataEl) return "No .data found";
            
            const children = Array.from(dataEl.children).map(c => ({
                tag: c.tagName,
                cls: c.className,
                text: c.innerText.trim(),
                html: c.outerHTML.substring(0, 100)
            }));
            
            return children;
        }""")
        print("\n--- PLAYER ROW STRUCTURE (First Player) ---")
        if isinstance(player_debug, str):
            print(player_debug)
        else:
            for i, child in enumerate(player_debug):
                print(f"Index {i}: [{child['cls']}] '{child['text']}'")

        # 2. XWS Check
        logger.info("Checking XWS icons...")
        xws_debug = page.evaluate("""() => {
            const icon = document.querySelector("img[title='Encoded list']");
            if(!icon) return "No XWS icon found";
            return {
                found: true,
                onclick: icon.getAttribute('onclick'),
                parent: icon.parentElement.outerHTML.substring(0,100)
            };
        }""")
        print(f"\n--- XWS CHECK ---\n{xws_debug}")

        # 3. Games Tab & Matches
        logger.info("Clicking Games tab...")
        try:
             page.click("#tab_games, a[title='Games']", timeout=5000)
        except Exception as e:
             logger.error(f"Click failed: {e}")
             return

        page.wait_for_timeout(3000)
        
        logger.info("Inspecting Matches...")
        match_debug = page.evaluate("""() => {
            const logs = [];
            
            // Find ALL headers to see if we missed some
            const details = document.querySelectorAll('.details');
            logs.push(`Found ${details.length} .details headers`);
            
            // Inspect the first header and its siblings DEEPLY
            if(details.length > 0) {
                const h = details[0];
                const block = { header: h.innerText, children: [] };
                
                let next = h.nextElementSibling;
                while(next && !next.classList.contains('details') && !next.classList.contains('footer')) {
                     block.children.push({
                         tag: next.tagName,
                         cls: next.className,
                         text: next.innerText.substring(0, 50).replace(/\\n/g, ' '),
                         html: next.outerHTML.substring(0, 500) // Get more HTML
                     });
                     next = next.nextElementSibling;
                }
                logs.push(block);
            }
            return logs;
        }""")
        
        print("\n--- MATCH STRUCTURE ---")
        for item in match_debug:
            if isinstance(item, str):
                print(item)
            else:
                print(f"HEADER: {item['header']}")
                for child in item['children']:
                    print(f"  > [{child['cls']}] Text: '{child['text']}'")
                    print(f"    HTML: {child['html']}")

if __name__ == "__main__":
    debug_longshanks()
