import re
import requests
import logging
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

logger = logging.getLogger(__name__)

def extract_from_vidsrc(url):
    """
    Extract M3U8 stream URL from VidSrc
    
    Args:
        url (str): VidSrc URL
    
    Returns:
        str: M3U8 URL or None if extraction fails
    """
    logger.info(f"Extracting M3U8 from VidSrc: {url}")
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://multiembed.mov/",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive"
    }
    
    try:
        # Get VidSrc page
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        logger.info(f"VidSrc page loaded successfully, status: {response.status_code}")
        
        # Parse HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Method 1: Look for direct video sources
        video_tags = soup.find_all('video')
        for video in video_tags:
            src = video.get('src', '')
            if src and '.m3u8' in src:
                logger.info(f"Found M3U8 in video tag: {src}")
                return make_absolute_url(src, url)
        
        # Method 2: Look for source tags within video elements
        source_tags = soup.find_all('source')
        for source in source_tags:
            src = source.get('src', '')
            if src and '.m3u8' in src:
                logger.info(f"Found M3U8 in source tag: {src}")
                return make_absolute_url(src, url)
        
        # Method 3: Look for M3U8 URLs in script tags
        scripts = soup.find_all('script')
        for script in scripts:
            if script.string:
                content = script.string
                
                # Common patterns for VidSrc
                patterns = [
                    r'(?:source|src|file|url)["\':\s]*["\']([^"\']*\.m3u8[^"\']*)["\']',
                    r'["\']([^"\']*\.m3u8[^"\']*)["\']',
                    r'player\s*\.\s*src\s*\(\s*["\']([^"\']*\.m3u8[^"\']*)["\']',
                    r'videojs\s*\([^)]*src["\':\s]*["\']([^"\']*\.m3u8[^"\']*)["\']'
                ]
                
                for pattern in patterns:
                    matches = re.findall(pattern, content, re.IGNORECASE)
                    for match in matches:
                        if match and '.m3u8' in match:
                            m3u8_url = make_absolute_url(match, url)
                            logger.info(f"Found M3U8 URL in script: {m3u8_url}")
                            
                            if validate_m3u8_url(m3u8_url):
                                return m3u8_url
        
        # Method 4: Look for iframe redirects
        iframes = soup.find_all('iframe')
        for iframe in iframes:
            iframe_src = iframe.get('src', '')
            if iframe_src and not iframe_src.startswith('data:'):
                iframe_url = make_absolute_url(iframe_src, url)
                logger.info(f"Found iframe redirect: {iframe_url}")
                
                # Recursively check iframe
                result = extract_from_vidsrc(iframe_url)
                if result:
                    return result
        
        # Method 5: Look for API endpoints
        api_patterns = [
            r'["\']([^"\']*api[^"\']*)["\']',
            r'["\']([^"\']*stream[^"\']*)["\']',
            r'["\']([^"\']*playlist[^"\']*)["\']'
        ]
        
        for pattern in api_patterns:
            matches = re.findall(pattern, response.text, re.IGNORECASE)
            for match in matches:
                if '/api/' in match or '/stream/' in match:
                    api_url = make_absolute_url(match, url)
                    logger.info(f"Trying API endpoint: {api_url}")
                    
                    try:
                        api_response = requests.get(api_url, headers=headers, timeout=10)
                        if api_response.status_code == 200:
                            api_data = api_response.text
                            
                            # Look for M3U8 in API response
                            m3u8_matches = re.findall(r'https?://[^"\s]+\.m3u8[^"\s]*', api_data)
                            if m3u8_matches:
                                logger.info(f"Found M3U8 in API response: {m3u8_matches[0]}")
                                return m3u8_matches[0]
                    except:
                        continue
        
        logger.warning("No M3U8 URL found in VidSrc page")
        return None
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error while fetching VidSrc: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error in VidSrc extraction: {str(e)}")
        return None

def make_absolute_url(url, base_url):
    """
    Convert relative URL to absolute URL
    
    Args:
        url (str): URL to convert
        base_url (str): Base URL
    
    Returns:
        str: Absolute URL
    """
    if url.startswith('//'):
        return 'https:' + url
    elif url.startswith('/'):
        return urljoin(base_url, url)
    elif url.startswith('http'):
        return url
    else:
        return urljoin(base_url, url)

def validate_m3u8_url(url):
    """
    Validate if a URL is a valid M3U8 stream
    
    Args:
        url (str): URL to validate
    
    Returns:
        bool: True if valid M3U8 URL
    """
    try:
        # Basic URL validation
        parsed = urlparse(url)
        if not parsed.scheme or not parsed.netloc:
            return False
        
        # Check if it's actually an M3U8 file
        if not url.lower().endswith('.m3u8'):
            return False
        
        # Try to fetch the M3U8 file to validate it
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        
        response = requests.head(url, headers=headers, timeout=10)
        
        # Check if the response is successful
        if response.status_code == 200:
            content_type = response.headers.get('content-type', '').lower()
            return any(ct in content_type for ct in ['mpegurl', 'x-mpegurl', 'vnd.apple.mpegurl'])
        
        return False
        
    except:
        return False
