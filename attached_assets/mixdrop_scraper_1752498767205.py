import re
import requests
import logging
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

logger = logging.getLogger(__name__)

def extract_m3u8_from_mixdrop(url):
    """
    Extract M3U8 stream URL from MixDrop
    
    Args:
        url (str): MixDrop URL
    
    Returns:
        str: M3U8 URL or None if extraction fails
    """
    logger.info(f"Extracting M3U8 from MixDrop: {url}")
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://multiembed.mov/",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1"
    }
    
    try:
        # Get MixDrop page
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        logger.info(f"MixDrop page loaded successfully, status: {response.status_code}")
        
        # Parse HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Method 1: Look for direct video source in HTML
        video_tags = soup.find_all('video')
        for video in video_tags:
            src = video.get('src', '')
            if src and '.m3u8' in src:
                logger.info(f"Found M3U8 in video tag: {src}")
                return src
        
        # Method 2: Look for M3U8 URLs in script tags
        scripts = soup.find_all('script')
        for script in scripts:
            if script.string:
                content = script.string
                
                # Look for various M3U8 patterns
                patterns = [
                    r'(?:src|source|url)["\':\s]*["\']([^"\']*\.m3u8[^"\']*)["\']',
                    r'MDCore\.\w+\s*=\s*["\']([^"\']*\.m3u8[^"\']*)["\']',
                    r'["\']([^"\']*\.m3u8[^"\']*)["\']',
                    r'file["\':\s]*["\']([^"\']*\.m3u8[^"\']*)["\']'
                ]
                
                for pattern in patterns:
                    matches = re.findall(pattern, content, re.IGNORECASE)
                    for match in matches:
                        if match and '.m3u8' in match:
                            # Make URL absolute if needed
                            if match.startswith('//'):
                                m3u8_url = 'https:' + match
                            elif match.startswith('/'):
                                m3u8_url = urljoin(url, match)
                            elif match.startswith('http'):
                                m3u8_url = match
                            else:
                                continue
                            
                            logger.info(f"Found M3U8 URL in script: {m3u8_url}")
                            
                            # Validate the URL
                            if validate_m3u8_url(m3u8_url):
                                return m3u8_url
        
        # Method 3: Look for encoded/obfuscated URLs
        full_text = response.text
        
        # Look for base64 encoded URLs
        base64_pattern = r'atob\(["\']([^"\']+)["\']\)'
        base64_matches = re.findall(base64_pattern, full_text)
        
        for encoded in base64_matches:
            try:
                import base64
                decoded = base64.b64decode(encoded).decode('utf-8')
                if '.m3u8' in decoded:
                    logger.info(f"Found M3U8 in base64: {decoded}")
                    if validate_m3u8_url(decoded):
                        return decoded
            except:
                continue
        
        # Method 4: Look for any M3U8 URLs in the entire page
        m3u8_pattern = r'https?://[^"\s<>]+\.m3u8[^"\s<>]*'
        m3u8_matches = re.findall(m3u8_pattern, full_text, re.IGNORECASE)
        
        for m3u8_url in m3u8_matches:
            logger.info(f"Found potential M3U8 URL: {m3u8_url}")
            if validate_m3u8_url(m3u8_url):
                return m3u8_url
        
        logger.warning("No M3U8 URL found in MixDrop page")
        return None
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error while fetching MixDrop: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error in MixDrop extraction: {str(e)}")
        return None

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
