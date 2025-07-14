import os
import time
import logging
from urllib.parse import urlparse, urljoin
from playwright.sync_api import sync_playwright, TimeoutError

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Global browser instance for better performance
_PLAYWRIGHT = None
_BROWSER = None

def get_browser():
    """Get or create a persistent browser instance"""
    global _PLAYWRIGHT, _BROWSER
    
    if not _PLAYWRIGHT:
        _PLAYWRIGHT = sync_playwright().start()
        
    if not _BROWSER:
        _BROWSER = _PLAYWRIGHT.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--disable-features=VizDisplayCompositor",
                "--single-process",
                "--disable-blink-features=AutomationControlled"
            ]
        )
    
    return _BROWSER

def get_m3u8_from_multiembed(imdb_id, source='auto'):
    """
    Extract M3U8 stream URL from multiple streaming sources
    
    Args:
        imdb_id (str): IMDb ID (e.g., 'tt1234567')
        source (str): Preferred source ('mixdrop', 'vidsrc', 'streamwish', 'doodstream', 'auto')
    
    Returns:
        dict: {'success': bool, 'm3u8': str, 'error': str}
    """
    logger.info(f"Fetching stream for IMDb ID: {imdb_id} with source: {source}")
    
    # Use API-based streaming sources (no Playwright needed)
    try:
        from .vidsrc_api import get_best_stream_api
        
        # Map source names to API preferences
        source_map = {
            'vidsrc': 'vidsrc',
            'streamwish': 'streamwish', 
            'doodstream': 'doodstream',
            'mixdrop': 'vidsrc',  # Use VidSrc as fallback for mixdrop
            'auto': 'auto'
        }
        
        preferred_source = source_map.get(source, 'auto')
        result = get_best_stream_api(imdb_id, preferred_source)
        
        if result.get('success'):
            return {
                "success": True,
                "m3u8": result.get('url'),
                "source": result.get('source', 'api')
            }
        else:
            return {
                "success": False,
                "error": result.get('error', 'Stream extraction failed')
            }
            
    except Exception as e:
        logger.error(f"API stream extraction failed: {str(e)}")
        return {"success": False, "error": f"API extraction failed: {str(e)}"}
    
    # Fallback to Playwright method if API fails
    try:
        browser = get_browser()
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080},
            java_script_enabled=True,
            ignore_https_errors=True
        )
        
        page = context.new_page()
        
        # Block unnecessary resources to speed up loading
        def route_handler(route):
            resource_type = route.request.resource_type
            url = route.request.url
            
            # Block images, fonts, and other unnecessary resources
            if resource_type in ['image', 'font', 'stylesheet'] or any(ext in url for ext in ['.png', '.jpg', '.jpeg', '.gif', '.woff', '.woff2', '.css']):
                route.abort()
            else:
                route.continue_()
        
        page.route("**/*", route_handler)
        
        # Navigate to multiembed page
        multiembed_url = f"https://multiembed.mov/movie/imdb/{imdb_id}"
        logger.info(f"Navigating to: {multiembed_url}")
        
        page.goto(multiembed_url, wait_until="domcontentloaded", timeout=30000)
        
        # Wait for page to load and find video iframes
        try:
            page.wait_for_timeout(5000)  # Wait 5 seconds for initial load
            
            # Look for video iframes
            iframe_selectors = [
                "iframe[src*='mixdrop']",
                "iframe[src*='vidsrc']",
                "iframe[src*='doodstream']",
                "iframe[src*='streamtape']",
                "iframe"
            ]
            
            iframe_element = None
            iframe_url = None
            
            for selector in iframe_selectors:
                try:
                    iframe_element = page.wait_for_selector(selector, timeout=10000)
                    if iframe_element:
                        iframe_url = iframe_element.get_attribute("src")
                        if iframe_url:
                            logger.info(f"Found iframe: {iframe_url}")
                            break
                except TimeoutError:
                    continue
            
            if not iframe_url:
                return {"error": "No video iframe found on page", "success": False}
            
            # Make iframe URL absolute if needed
            if iframe_url.startswith('//'):
                iframe_url = 'https:' + iframe_url
            elif iframe_url.startswith('/'):
                iframe_url = urljoin(multiembed_url, iframe_url)
            
            # Extract stream based on source
            if 'mixdrop' in iframe_url:
                logger.info("Using MixDrop extractor")
                from .mixdrop_scraper import extract_m3u8_from_mixdrop
                m3u8_url = extract_m3u8_from_mixdrop(iframe_url)
                
            elif 'vidsrc' in iframe_url:
                logger.info("Using VidSrc extractor")
                from .vidsrc_scraper import extract_from_vidsrc
                m3u8_url = extract_from_vidsrc(iframe_url)
                
            else:
                logger.info("Using generic extractor")
                m3u8_url = extract_m3u8_from_generic(page, iframe_url)
            
            if m3u8_url:
                logger.info(f"Successfully extracted M3U8 URL: {m3u8_url[:100]}...")
                return {"m3u8": m3u8_url, "success": True}
            else:
                return {"error": "Failed to extract M3U8 URL", "success": False}
                
        except Exception as e:
            logger.error(f"Error during iframe processing: {str(e)}")
            return {"error": f"Iframe processing failed: {str(e)}", "success": False}
            
    except Exception as e:
        logger.error(f"Stream extraction failed: {str(e)}")
        return {"error": f"Stream extraction failed: {str(e)}", "success": False}
        
    finally:
        if 'context' in locals():
            context.close()

def extract_m3u8_from_generic(page, iframe_url):
    """
    Generic M3U8 extractor that monitors network requests
    """
    try:
        logger.info(f"Extracting M3U8 from generic iframe: {iframe_url}")
        
        m3u8_urls = []
        
        # Monitor network requests for M3U8 files
        def handle_response(response):
            if '.m3u8' in response.url:
                logger.info(f"Found M3U8 URL: {response.url}")
                m3u8_urls.append(response.url)
        
        page.on("response", handle_response)
        
        # Navigate to iframe
        page.goto(iframe_url, wait_until="domcontentloaded", timeout=30000)
        
        # Wait for video to load
        page.wait_for_timeout(10000)
        
        # Try to find and click play button
        play_selectors = [
            "button[class*='play']",
            ".play-button",
            ".video-play-button",
            "button:has-text('Play')",
            "[data-testid='play-button']"
        ]
        
        for selector in play_selectors:
            try:
                play_button = page.query_selector(selector)
                if play_button:
                    play_button.click()
                    logger.info(f"Clicked play button: {selector}")
                    break
            except:
                continue
        
        # Wait for M3U8 requests
        page.wait_for_timeout(5000)
        
        # Return the best M3U8 URL found
        if m3u8_urls:
            # Prefer master playlists
            master_urls = [url for url in m3u8_urls if 'master' in url.lower()]
            if master_urls:
                return master_urls[0]
            return m3u8_urls[0]
        
        return None
        
    except Exception as e:
        logger.error(f"Generic extraction failed: {str(e)}")
        return None

def cleanup_browser():
    """Clean up browser resources"""
    global _BROWSER, _PLAYWRIGHT
    
    if _BROWSER:
        _BROWSER.close()
        _BROWSER = None
    
    if _PLAYWRIGHT:
        _PLAYWRIGHT.stop()
        _PLAYWRIGHT = None

# Clean up on module exit
import atexit
atexit.register(cleanup_browser)
