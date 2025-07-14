import logging
from playwright.sync_api import sync_playwright, TimeoutError

logger = logging.getLogger(__name__)

def extract_m3u8_playwright(imdb_id, source='auto', timeout=30):
    """
    Extract M3U8 stream URL using Playwright for dynamic content
    
    Args:
        imdb_id (str): IMDb ID
        source (str): Preferred source
        timeout (int): Timeout in seconds
    
    Returns:
        dict: Result with success status and M3U8 URL or error
    """
    logger.info(f"Extracting M3U8 using Playwright for IMDb ID: {imdb_id}")
    
    with sync_playwright() as p:
        try:
            browser = p.chromium.launch(
                headless=True,
                args=[
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-gpu"
                ]
            )
            
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            
            page = context.new_page()
            m3u8_links = []
            
            # Monitor network requests for M3U8 files
            def handle_response(response):
                url = response.url
                if '.m3u8' in url:
                    logger.info(f"Found M3U8 URL: {url}")
                    m3u8_links.append({
                        'url': url,
                        'status': response.status,
                        'headers': dict(response.headers)
                    })
            
            page.on("response", handle_response)
            
            # Navigate to multiembed page
            multiembed_url = f"https://multiembed.mov/movie/imdb/{imdb_id}"
            logger.info(f"Navigating to: {multiembed_url}")
            
            page.goto(multiembed_url, wait_until="domcontentloaded", timeout=timeout * 1000)
            
            # Wait for initial content to load
            page.wait_for_timeout(5000)
            
            # Look for video iframes and interact with them
            iframe_selectors = [
                "iframe[src*='mixdrop']",
                "iframe[src*='vidsrc']",
                "iframe[src*='doodstream']",
                "iframe"
            ]
            
            for selector in iframe_selectors:
                try:
                    iframe = page.wait_for_selector(selector, timeout=10000)
                    if iframe:
                        iframe_src = iframe.get_attribute('src')
                        if iframe_src:
                            logger.info(f"Found iframe: {iframe_src}")
                            
                            # Navigate to iframe content
                            iframe_page = context.new_page()
                            iframe_page.on("response", handle_response)
                            
                            try:
                                iframe_page.goto(iframe_src, wait_until="domcontentloaded", timeout=20000)
                                
                                # Try to find and click play button
                                play_selectors = [
                                    "button[class*='play']",
                                    ".play-button",
                                    "button:has-text('Play')",
                                    ".video-play-button"
                                ]
                                
                                for play_selector in play_selectors:
                                    try:
                                        play_button = iframe_page.wait_for_selector(play_selector, timeout=5000)
                                        if play_button:
                                            play_button.click()
                                            logger.info(f"Clicked play button: {play_selector}")
                                            break
                                    except TimeoutError:
                                        continue
                                
                                # Wait for video to load
                                iframe_page.wait_for_timeout(10000)
                                
                            except Exception as e:
                                logger.warning(f"Error processing iframe {iframe_src}: {str(e)}")
                            finally:
                                iframe_page.close()
                            
                            # If we found M3U8 links, break
                            if m3u8_links:
                                break
                                
                except TimeoutError:
                    continue
            
            # Additional wait for any delayed M3U8 requests
            page.wait_for_timeout(5000)
            
            # Filter and return the best M3U8 URL
            if m3u8_links:
                # Sort by preference (master playlists first, then by status code)
                m3u8_links.sort(key=lambda x: (
                    'master' not in x['url'].lower(),  # Master playlists first
                    x['status'] != 200  # Successful responses first
                ))
                
                best_link = m3u8_links[0]
                logger.info(f"Selected best M3U8 URL: {best_link['url']}")
                
                return {
                    "success": True,
                    "m3u8": best_link['url']
                }
            else:
                logger.warning("No M3U8 URLs found")
                return {
                    "success": False,
                    "error": "No M3U8 stream URLs found"
                }
                
        except Exception as e:
            logger.error(f"Playwright extraction failed: {str(e)}")
            return {
                "success": False,
                "error": f"Playwright extraction failed: {str(e)}"
            }
        finally:
            browser.close()
