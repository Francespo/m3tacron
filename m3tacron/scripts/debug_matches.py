from playwright.sync_api import sync_playwright
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("debug_matches")

def debug_matches():
    url = "https://xwing-legacy.longshanks.org/event/29336/"
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url)
        
        # Cookie
        try:
             page.click("#cookie_permission button", timeout=2000)
        except: pass

        # Games tab
        page.click("a[href='#tab_games']")
        page.wait_for_timeout(2000)

        # DEBUG: Dump the structure of the first few headers and their siblings
        result = page.evaluate("""() => {
            const logs = [];
            const details = document.querySelectorAll('.details');
            
            // Look at first 3 headers
            for(let i=0; i<3; i++) {
                if(i >= details.length) break;
                const h = details[i];
                const block = { header: h.innerText, siblings: [] };
                
                let next = h.nextElementSibling;
                while(next && !next.classList.contains('details') && !next.classList.contains('footer')) {
                     block.siblings.push({
                         tag: next.tagName,
                         cls: next.className,
                         html: next.outerHTML.substring(0, 150)
                     });
                     next = next.nextElementSibling;
                }
                logs.push(block);
            }
            return logs;
        }""")
        
        for block in result:
            print(f"\nHEADER: {block['header']}")
            for sib in block['siblings']:
                print(f"  - [{sib['tag']}.{sib['cls']}] {sib['html']}...")

if __name__ == "__main__":
    debug_matches()
