
import logging
import json
from playwright.sync_api import sync_playwright, Page

logger = logging.getLogger(__name__)

def fetch_xws_from_builder(url: str) -> dict | None:
    """
    Visits a builder URL (YASB, etc.) and attempts to extract the XWS JSON 
    by interacting with the page's export features.
    
    Args:
        url: The full URL to the squadron builder list.
        
    Returns:
        dict: The parsed XWS JSON, or None if extraction failed.
    """
    if not url:
        return None
        
    # Check supported builders
    if "yasb.app" not in url:
        # TODO: Add LBN support if needing interaction (LBN usually has different export flow)
        return None

    logger.info(f"Fetching XWS from builder: {url}")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        # Use a consistent user agent and viewport to ensure desktop UI
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            viewport={"width": 1920, "height": 1080}
        )
        page = context.new_page()
        
        try:
            page.goto(url, wait_until="networkidle", timeout=30000)
            
            if "yasb.app" in url:
                return _extract_yasb_xws(page)
                
        except Exception as e:
            logger.error(f"Error fetching XWS from builder: {e}")
            return None
        finally:
            browser.close()
            
    return None

def _extract_yasb_xws(page: Page) -> dict | None:
    """
    Internal helper to drive YASB UI for XWS export.
    """
    try:
        # 1. Click Print/Export button
        # Use native JS click to bypass ALL Playwright visibility checks
        try:
           export_locator = page.locator("button.view-as-text")
           export_locator.first.wait_for(state="attached", timeout=30000)
           
           # Direct JS click
           page.evaluate("document.querySelector('button.view-as-text').click()")
           
        except Exception as e:
           logger.warning(f"Failed to click export button: {e}")
           return None
        
        # 2. Click "XWS" view option
        # Selector: button.select-xws-view
        xws_locator = page.locator("button.select-xws-view")
        xws_locator.first.wait_for(state="attached", timeout=10000)
        page.evaluate("document.querySelector('button.select-xws-view').click()")
        
        # 3. Read Textarea
        textarea = page.locator("textarea").first
        
        # Poll for content (up to 5 seconds)
        for _ in range(10):
            content = textarea.input_value()
            if content and len(content) > 10:
                break
            page.wait_for_timeout(500)
            
        content = textarea.input_value()
        if not content:
            logger.warning("YASB Export textarea empty.")
            return None
            
        # 4. Parse JSON
        xws = json.loads(content)
        return xws
        
    except Exception as e:
        logger.error(f"YASB Extraction Logic Failed: {e}")
        return None
