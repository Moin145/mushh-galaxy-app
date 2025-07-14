import logging
import re
import time
from urllib.parse import urljoin, urlparse

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
    
    try:
        from playwright.sync_api import sync_playwright, TimeoutError
        
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=[
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-gpu",
                    "--disable-features=VizDisplayCompositor",
                    "--disable-background-timer-throttling",
                    "--disable-renderer-backgrounding",
                    "--disable-backgrounding-occluded-windows"
                ]
            )
            
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                viewport={"width": 1920, "height": 1080},
                ignore_https_errors=True
            )
            
            page = context.new_page()
            m3u8_links = []
            
            # Enhanced network monitoring for M3U8 files
            def handle_response(response):
                url = response.url
                if any(pattern in url.lower() for pattern in ['.m3u8', 'playlist', 'manifest']):
                    logger.info(f"Found M3U8 URL: {url}")
                    m3u8_links.append({
                        'url': url,
                        'status': response.status,
                        'headers': dict(response.headers),
                        'content_type': response.headers.get('content-type', '').lower()
                    })
            
            page.on("response", handle_response)
            
            # Navigate to multiembed page
            multiembed_url = f"https://multiembed.mov/movie/imdb/{imdb_id}"
            logger.info(f"Navigating to: {multiembed_url}")
            
            page.goto(multiembed_url, wait_until="domcontentloaded", timeout=timeout * 1000)
            
            # Wait for initial content to load
            page.wait_for_timeout(3000)
            
            # Look for video iframes and interact with them
            iframe_selectors = [
                "iframe[src*='mixdrop']",
                "iframe[src*='vidsrc']",
                "iframe[src*='doodstream']",
                "iframe[src*='streamwish']",
                "iframe[src*='embed']",
                "iframe[src*='player']",
                "iframe"
            ]
            
            processed_iframes = set()
            
            for selector in iframe_selectors:
                try:
                    iframes = page.query_selector_all(selector)
                    
                    for iframe in iframes:
                        iframe_src = iframe.get_attribute('src')
                        if iframe_src and iframe_src not in processed_iframes:
                            processed_iframes.add(iframe_src)
                            
                            # Make iframe URL absolute
                            if iframe_src.startswith('//'):
                                iframe_src = 'https:' + iframe_src
                            elif iframe_src.startswith('/'):
                                iframe_src = urljoin(multiembed_url, iframe_src)
                            
                            logger.info(f"Processing iframe: {iframe_src}")
                            
                            # Open iframe in new page
                            iframe_page = context.new_page()
                            iframe_page.on("response", handle_response)
                            
                            try:
                                iframe_page.goto(iframe_src, wait_until="domcontentloaded", timeout=20000)
                                
                                # Wait for page to load
                                iframe_page.wait_for_timeout(3000)
                                
                                # Try to find and interact with video elements
                                video_selectors = [
                                    "video",
                                    "video source",
                                    "[data-src*='.m3u8']",
                                    "[src*='.m3u8']"
                                ]
                                
                                for video_selector in video_selectors:
                                    try:
                                        video_elements = iframe_page.query_selector_all(video_selector)
                                        for video in video_elements:
                                            src = video.get_attribute('src') or video.get_attribute('data-src')
                                            if src and '.m3u8' in src:
                                                logger.info(f"Found M3U8 in video element: {src}")
                                                m3u8_links.append({
                                                    'url': src,
                                                    'status': 200,
                                                    'headers': {},
                                                    'content_type': 'application/vnd.apple.mpegurl'
                                                })
                                    except:
                                        continue
                                
                                # Try to find and click play buttons
                                play_selectors = [
                                    "button[class*='play']",
                                    ".play-button",
                                    "button:has-text('Play')",
                                    ".video-play-button",
                                    "[data-testid='play-button']",
                                    ".vjs-big-play-button",
                                    ".plyr__control--overlaid",
                                    ".jwplayer .jw-display-icon-container"
                                ]
                                
                                for play_selector in play_selectors:
                                    try:
                                        play_button = iframe_page.wait_for_selector(play_selector, timeout=3000)
                                        if play_button and play_button.is_visible():
                                            play_button.click()
                                            logger.info(f"Clicked play button: {play_selector}")
                                            break
                                    except TimeoutError:
                                        continue
                                    except Exception as e:
                                        logger.debug(f"Error clicking play button {play_selector}: {str(e)}")
                                        continue
                                
                                # Wait for video to load and network requests
                                iframe_page.wait_for_timeout(5000)
                                
                                # Check for any additional M3U8 URLs in page content
                                content = iframe_page.content()
                                m3u8_matches = re.findall(r'https?://[^"\s<>]+\.m3u8[^"\s<>]*', content)
                                for match in m3u8_matches:
                                    logger.info(f"Found M3U8 in page content: {match}")
                                    m3u8_links.append({
                                        'url': match,
                                        'status': 200,
                                        'headers': {},
                                        'content_type': 'application/vnd.apple.mpegurl'
                                    })
                                
                            except Exception as e:
                                logger.warning(f"Error processing iframe {iframe_src}: {str(e)}")
                            finally:
                                iframe_page.close()
                            
                            # If we found M3U8 links, we can break early
                            if m3u8_links:
                                break
                                
                except Exception as e:
                    logger.debug(f"Error with selector {selector}: {str(e)}")
                    continue
                
                # Break if we found links
                if m3u8_links:
                    break
            
            # Additional wait for any delayed M3U8 requests
            page.wait_for_timeout(2000)
            
            # Filter and return the best M3U8 URL
            if m3u8_links:
                # Sort by preference
                m3u8_links.sort(key=lambda x: (
                    x['status'] != 200,  # Successful responses first
                    'master' not in x['url'].lower(),  # Master playlists first
                    'mpegurl' not in x.get('content_type', ''),  # Proper content type first
                    len(x['url'])  # Shorter URLs first (often more reliable)
                ))
                
                best_link = m3u8_links[0]
                logger.info(f"Selected best M3U8 URL: {best_link['url']}")
                
                return {
                    "success": True,
                    "m3u8": best_link['url'],
                    "stream_type": "hls",
                    "source": "playwright",
                    "quality": "HD",
                    "all_found": [link['url'] for link in m3u8_links]
                }
            else:
                logger.warning("No M3U8 URLs found")
                return {
                    "success": False,
                    "error": "No M3U8 stream URLs found after thorough search"
                }
                
            browser.close()
                
    except ImportError:
        logger.warning("Playwright not available, skipping browser-based extraction")
        return {
            "success": False,
            "error": "Playwright not available - install with 'pip install playwright && playwright install'"
        }
    except Exception as e:
        logger.error(f"Playwright extraction failed: {str(e)}")
        return {
            "success": False,
            "error": f"Playwright extraction failed: {str(e)}"
        }

def validate_m3u8_url(url):
    """Validate if a URL is a working M3U8 stream"""
    try:
        import requests
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'https://multiembed.mov/'
        }
        
        response = requests.head(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            content_type = response.headers.get('content-type', '').lower()
            return any(ct in content_type for ct in ['mpegurl', 'x-mpegurl', 'vnd.apple.mpegurl'])
        
        return False
        
    except Exception as e:
        logger.debug(f"M3U8 validation failed for {url}: {str(e)}")
        return False
