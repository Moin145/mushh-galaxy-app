import re
import requests
import logging
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

logger = logging.getLogger(__name__)

def extract_m3u8_from_mixdrop(url):
    """
    Extract M3U8 stream URL from MixDrop with enhanced extraction methods
    
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
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "cross-site"
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
                return make_absolute_url(src, url)
        
        # Method 2: Look for source tags
        source_tags = soup.find_all('source')
        for source in source_tags:
            src = source.get('src', '')
            if src and '.m3u8' in src:
                logger.info(f"Found M3U8 in source tag: {src}")
                return make_absolute_url(src, url)
        
        # Method 3: Look for M3U8 URLs in script tags with enhanced patterns
        scripts = soup.find_all('script')
        for script in scripts:
            if script.string:
                content = script.string
                
                # Enhanced patterns for MixDrop
                patterns = [
                    r'(?:src|source|url|file|playlist)["\':\s]*["\']([^"\']*\.m3u8[^"\']*)["\']',
                    r'MDCore\.\w+\s*=\s*["\']([^"\']*\.m3u8[^"\']*)["\']',
                    r'["\']([^"\']*\.m3u8[^"\']*)["\']',
                    r'file["\':\s]*["\']([^"\']*\.m3u8[^"\']*)["\']',
                    r'videojs.*?src["\']?\s*:\s*["\']([^"\']*\.m3u8[^"\']*)["\']',
                    r'jwplayer\([^)]*\)\.setup\([^)]*file["\']?\s*:\s*["\']([^"\']*\.m3u8[^"\']*)["\']',
                    r'player\.src\s*\(\s*["\']([^"\']*\.m3u8[^"\']*)["\']',
                    r'\.m3u8["\']?\s*:\s*["\']([^"\']*\.m3u8[^"\']*)["\']'
                ]
                
                for pattern in patterns:
                    matches = re.findall(pattern, content, re.IGNORECASE)
                    for match in matches:
                        if match and '.m3u8' in match:
                            m3u8_url = make_absolute_url(match, url)
                            logger.info(f"Found M3U8 URL in script: {m3u8_url}")
                            
                            # Validate the URL
                            if validate_m3u8_url(m3u8_url):
                                return m3u8_url
        
        # Method 4: Look for encoded/obfuscated URLs
        full_text = response.text
        
        # Look for base64 encoded URLs
        base64_pattern = r'atob\s*\(\s*["\']([^"\']+)["\']\s*\)'
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
        
        # Method 5: Look for any M3U8 URLs in the entire page
        m3u8_pattern = r'https?://[^"\s<>]+\.m3u8[^"\s<>]*'
        m3u8_matches = re.findall(m3u8_pattern, full_text, re.IGNORECASE)
        
        for m3u8_url in m3u8_matches:
            logger.info(f"Found potential M3U8 URL: {m3u8_url}")
            if validate_m3u8_url(m3u8_url):
                return m3u8_url
        
        # Method 6: Look for video.js or other player configurations
        player_patterns = [
            r'videojs\s*\([^)]*\)\.src\s*\(\s*["\']([^"\']*\.m3u8[^"\']*)["\']',
            r'jwplayer\([^)]*\)\.setup\([^)]*["\']([^"\']*\.m3u8[^"\']*)["\']',
            r'new\s+Plyr\([^)]*src["\']?\s*:\s*["\']([^"\']*\.m3u8[^"\']*)["\']',
            r'hls\.js.*?loadSource\s*\(\s*["\']([^"\']*\.m3u8[^"\']*)["\']'
        ]
        
        for pattern in player_patterns:
            matches = re.findall(pattern, full_text, re.IGNORECASE)
            for m3u8_url in matches:
                logger.info(f"Found M3U8 in player config: {m3u8_url}")
                if validate_m3u8_url(m3u8_url):
                    return m3u8_url
        
        # Method 7: Look for API endpoints that might return M3U8
        api_patterns = [
            r'["\']([^"\']*api[^"\']*playlist[^"\']*)["\']',
            r'["\']([^"\']*api[^"\']*stream[^"\']*)["\']',
            r'["\']([^"\']*api[^"\']*m3u8[^"\']*)["\']'
        ]
        
        for pattern in api_patterns:
            matches = re.findall(pattern, full_text, re.IGNORECASE)
            for api_url in matches:
                if '/api/' in api_url:
                    full_api_url = make_absolute_url(api_url, url)
                    logger.info(f"Trying API endpoint: {full_api_url}")
                    
                    try:
                        api_response = requests.get(full_api_url, headers=headers, timeout=10)
                        if api_response.status_code == 200:
                            api_content = api_response.text
                            
                            # Look for M3U8 in API response
                            api_m3u8_matches = re.findall(r'https?://[^"\s]+\.m3u8[^"\s]*', api_content)
                            if api_m3u8_matches:
                                logger.info(f"Found M3U8 in API response: {api_m3u8_matches[0]}")
                                return api_m3u8_matches[0]
                    except:
                        continue
        
        logger.warning("No M3U8 URL found in MixDrop page")
        return None
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error while fetching MixDrop: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error in MixDrop extraction: {str(e)}")
        return None

def make_absolute_url(url, base_url):
    """Convert relative URL to absolute URL"""
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
    Validate if a URL is a valid M3U8 stream with enhanced validation
    
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
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Referer": "https://multiembed.mov/"
        }
        
        try:
            # Try HEAD request first
            response = requests.head(url, headers=headers, timeout=8)
            
            if response.status_code == 200:
                content_type = response.headers.get('content-type', '').lower()
                return any(ct in content_type for ct in ['mpegurl', 'x-mpegurl', 'vnd.apple.mpegurl'])
        except:
            pass
            
        try:
            # If HEAD fails, try GET request with limited content
            response = requests.get(url, headers=headers, timeout=8, stream=True)
            if response.status_code == 200:
                # Read only first 1KB to check if it's M3U8
                content_sample = b''
                for chunk in response.iter_content(1024):
                    content_sample += chunk
                    break
                
                content_text = content_sample.decode('utf-8', errors='ignore')
                
                # Check for M3U8 markers
                m3u8_markers = ['#EXTM3U', '#EXT-X-VERSION', '#EXT-X-TARGETDURATION', '#EXT-X-MEDIA-SEQUENCE']
                return any(marker in content_text for marker in m3u8_markers)
        except:
            pass
        
        return False
        
    except Exception as e:
        logger.debug(f"M3U8 validation failed for {url}: {str(e)}")
        return False
