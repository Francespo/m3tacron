from playwright.sync_api import sync_playwright
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("DebugListStructure")

def run():
    url = "https://rollbetter.gg/tournaments/2538/lists"
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url, wait_until="domcontentloaded")
        page.wait_for_timeout(3000)
        
        # Find first Copy XWS button
        btn = page.locator("button:has-text('Copy XWS')").first
        if btn.count() == 0:
            logger.error("No Copy XWS button found!")
            return

        logger.info(f"Button found: {btn.inner_text()}")
        
        parents = btn.evaluate("""(el) => {
            let current = el;
            let info = [];
            for (let i=0; i<6; i++) {
                current = current.parentElement;
                if (!current) break;
                
                // Get header or previous sibling if it looks like a name
                let siblingText = "";
                if (current.previousElementSibling) {
                     siblingText = current.previousElementSibling.innerText.substring(0, 50);
                }
                
                info.push({
                    tag: current.tagName,
                    classes: current.className,
                    text: current.innerText.substring(0, 100).replace(/\\n/g, ' | '),
                    html: current.outerHTML.substring(0, 150),
                    sibling: siblingText
                });
            }
            return info;
        }""")
        
        for i, p in enumerate(parents):
            if i+1 in [2, 3, 4, 5]:
                 logger.info(f"Parent {i+1} ({p['tag']}.{p['classes']}):")
                 logger.info(f"  Text Start: {p['text'][:50]}")
                 logger.info(f"  Prev Sibling: {p['sibling']}")

        browser.close()

if __name__ == "__main__":
    run()
