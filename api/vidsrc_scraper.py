import re
import requests
import logging
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

logger = logging.getLogger(__name__)

def extract_from_vidsrc(url):
    """
    Extract M3U8 stream URL from VidSrc with enhanced extraction methods
    
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
        "Connection": "keep-alive",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "cross-site"
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
        
        # Method 3: Look for M3U8 URLs in script tags with enhanced patterns
        scripts = soup.find_all('script')
        for script in scripts:
            if script.string:
                content = script.string
                
                # Enhanced patterns for VidSrc
                patterns = [
                    r'(?:source|src|file|url|playlist)["\':\s]*["\']([^"\']*\.m3u8[^"\']*)["\']',
                    r'["\']([^"\']*\.m3u8[^"\']*)["\']',
                    r'player\s*\.\s*src\s*\(\s*["\']([^"\']*\.m3u8[^"\']*)["\']',
                    r'videojs\s*\([^)]*src["\':\s]*["\']([^"\']*\.m3u8[^"\']*)["\']',
                    r'jwplayer\([^)]*\)\.setup\([^)]*file["\']?\s*:\s*["\']([^"\']*\.m3u8[^"\']*)["\']',
                    r'Hls\.loadSource\s*\(\s*["\']([^"\']*\.m3u8[^"\']*)["\']',
                    r'new\s+Hls\([^)]*\)\.loadSource\s*\(\s*["\']([^"\']*\.m3u8[^"\']*)["\']',
                    r'\.m3u8["\']?\s*:\s*["\']([^"\']*\.m3u8[^"\']*)["\']'
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
                
                # For VidSrc iframes, try to extract from them recursively
                if 'vidsrc' in iframe_url.lower():
                    result = extract_from_vidsrc(iframe_url)
                    if result:
                        return result
                
                # For other iframes, return the URL directly
                return iframe_url
        
        # Method 5: Look for API endpoints
        api_patterns = [
            r'["\']([^"\']*api[^"\']*)["\']',
            r'["\']([^"\']*stream[^"\']*)["\']',
            r'["\']([^"\']*playlist[^"\']*)["\']',
            r'["\']([^"\']*source[^"\']*)["\']'
        ]
        
        for pattern in api_patterns:
            matches = re.findall(pattern, response.text, re.IGNORECASE)
            for match in matches:
                if any(keyword in match for keyword in ['/api/', '/stream/', '/playlist/', '/source/']):
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
        
        # Method 6: Look for any M3U8 URLs in entire page content
        m3u8_pattern = r'https?://[^"\s<>]+\.m3u8[^"\s<>]*'
        m3u8_matches = re.findall(m3u8_pattern, response.text, re.IGNORECASE)
        
        for m3u8_url in m3u8_matches:
            logger.info(f"Found potential M3U8 URL: {m3u8_url}")
            if validate_m3u8_url(m3u8_url):
                return m3u8_url
        
        # Method 7: Look for encrypted or obfuscated sources
        encrypted_patterns = [
            r'atob\s*\(\s*["\']([^"\']+)["\']\s*\)',  # Base64 encoded
            r'decodeURIComponent\s*\(\s*["\']([^"\']+)["\']\s*\)',  # URI encoded
            r'JSON\.parse\s*\(\s*["\']([^"\']+)["\']\s*\)'  # JSON encoded
        ]
        
        for pattern in encrypted_patterns:
            matches = re.findall(pattern, response.text, re.IGNORECASE)
            for encoded_data in matches:
                try:
                    # Try to decode base64
                    if 'atob' in pattern:
                        import base64
                        decoded = base64.b64decode(encoded_data).decode('utf-8')
                        if '.m3u8' in decoded:
                            logger.info(f"Found M3U8 in base64: {decoded}")
                            return decoded
                    
                    # Try to decode URI
                    elif 'decodeURIComponent' in pattern:
                        import urllib.parse
                        decoded = urllib.parse.unquote(encoded_data)
                        if '.m3u8' in decoded:
                            logger.info(f"Found M3U8 in URI: {decoded}")
                            return decoded
                    
                except:
                    continue
        
        # Method 8: Return the original URL if it looks like a working embed
        if any(keyword in url.lower() for keyword in ['embed', 'player', 'stream']):
            logger.info(f"Returning original URL as potential embed: {url}")
            return url
        
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

def extract_vidsrc_sources(url):
    """Extract all possible sources from VidSrc page"""
    sources = []
    
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Referer": "https://multiembed.mov/"
        }
        
        response = requests.get(url, headers=headers, timeout=15)
        
        if response.status_code == 200:
            # Extract all potential streaming URLs
            patterns = [
                r'https?://[^"\s<>]+\.m3u8[^"\s<>]*',
                r'https?://[^"\s<>]+\.mp4[^"\s<>]*',
                r'https?://[^"\s<>]+/embed/[^"\s<>]*'
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, response.text, re.IGNORECASE)
                for match in matches:
                    if match not in sources:
                        sources.append(match)
        
        return sources
        
    except Exception as e:
        logger.error(f"Error extracting VidSrc sources: {str(e)}")
        return []
