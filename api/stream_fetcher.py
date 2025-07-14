import os
import time
import logging
import requests
from urllib.parse import urlparse, urljoin
import re

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def get_m3u8_from_multiembed(imdb_id, source='auto'):
    """
    Extract M3U8 stream URL from multiple streaming sources with enhanced reliability
    
    Args:
        imdb_id (str): IMDb ID (e.g., 'tt1234567')
        source (str): Preferred source ('mixdrop', 'vidsrc', 'streamwish', 'doodstream', 'auto')
    
    Returns:
        dict: {'success': bool, 'm3u8': str, 'error': str}
    """
    logger.info(f"Fetching stream for IMDb ID: {imdb_id} with source: {source}")
    
    # Enhanced direct embed URLs with better working sources
    direct_embed_urls = [
        f"https://multiembed.mov/directstream.php?video_id={imdb_id}&imdb=1",
        f"https://2embed.cc/embed/movie?imdb={imdb_id}",
        f"https://www.2embed.to/embed/imdb/movie?id={imdb_id}",
        f"https://embed.su/embed/movie/{imdb_id}",
        f"https://vidsrc.me/embed/movie?imdb={imdb_id}",
        f"https://moviesapi.club/movie/{imdb_id}",
        f"https://vidsrc.to/embed/movie/{imdb_id}",
        f"https://autoembed.cc/movie/imdb/{imdb_id}",
        f"https://streamm4u.ws/embed/movie/{imdb_id}",
        f"https://vidplay.online/embed/movie/{imdb_id}",
        f"https://vidbinge.com/embed/movie/{imdb_id}",
        f"https://www.filmxy.vip/embed/movie/{imdb_id}",
        f"https://vidbinge.dev/embed/movie/{imdb_id}",
        f"https://www.showboxmovies.net/embed/movie/{imdb_id}",
        f"https://vidsrc.xyz/embed/movie/{imdb_id}",
        f"https://embedsito.com/v/movie/{imdb_id}",
        f"https://www.2embed.org/embed/movie/{imdb_id}",
        f"https://movieshd.watch/embed/movie/{imdb_id}"
    ]
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1"
    }
    
    # Try direct embed URLs first
    for embed_url in direct_embed_urls:
        try:
            logger.info(f"Trying direct embed: {embed_url}")
            
            # Quick test to see if the URL is accessible
            response = requests.get(embed_url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                content = response.text.lower()
                
                # Check if it contains video player elements
                video_indicators = ['video', 'player', 'stream', 'embed', 'iframe', 'source', 'jwplayer', 'videojs']
                if any(indicator in content for indicator in video_indicators):
                    logger.info(f"Found working embed URL: {embed_url}")
                    
                    # Try to extract direct M3U8 URLs from the content
                    m3u8_urls = extract_m3u8_from_content(response.text)
                    if m3u8_urls:
                        # Validate the M3U8 URL
                        for m3u8_url in m3u8_urls:
                            if validate_stream_url(m3u8_url):
                                logger.info(f"Found valid direct M3U8 URL: {m3u8_url}")
                                return {
                                    "success": True,
                                    "m3u8": m3u8_url,
                                    "source": "direct_m3u8",
                                    "type": "hls"
                                }
                    
                    # If no direct M3U8, return embed URL for iframe
                    return {
                        "success": True,
                        "m3u8": embed_url,
                        "source": "embed",
                        "type": "iframe"
                    }
        except Exception as e:
            logger.warning(f"Direct embed failed {embed_url}: {str(e)}")
            continue
    
    # If direct embeds don't work, try multiembed with iframe extraction
    try:
        multiembed_url = f"https://multiembed.mov/movie/imdb/{imdb_id}"
        logger.info(f"Trying multiembed: {multiembed_url}")
        
        response = requests.get(multiembed_url, headers=headers, timeout=15)
        
        if response.status_code == 200:
            # Look for iframe URLs in the response
            iframe_urls = extract_iframe_urls(response.text, multiembed_url)
            
            # Prioritize iframes based on source preference
            prioritized_iframes = prioritize_iframes(iframe_urls, source)
            
            for iframe_url in prioritized_iframes:
                logger.info(f"Found streaming iframe: {iframe_url}")
                
                # Try to extract M3U8 from this iframe
                if 'mixdrop' in iframe_url.lower():
                    from .mixdrop_scraper import extract_m3u8_from_mixdrop
                    m3u8_url = extract_m3u8_from_mixdrop(iframe_url)
                    if m3u8_url:
                        return {"success": True, "m3u8": m3u8_url, "source": "mixdrop", "type": "hls"}
                
                elif 'vidsrc' in iframe_url.lower():
                    from .vidsrc_scraper import extract_from_vidsrc
                    m3u8_url = extract_from_vidsrc(iframe_url)
                    if m3u8_url:
                        return {"success": True, "m3u8": m3u8_url, "source": "vidsrc", "type": "hls"}
                
                else:
                    # For other sources, try generic extraction
                    m3u8_url = extract_m3u8_from_generic_iframe(iframe_url)
                    if m3u8_url:
                        return {"success": True, "m3u8": m3u8_url, "source": "generic", "type": "hls"}
                    
                    # If no M3U8 found, return iframe URL directly
                    return {"success": True, "m3u8": iframe_url, "source": "iframe", "type": "iframe"}
        
        # If no specific iframes found, try to extract any streaming URLs
        stream_urls = extract_streaming_urls(response.text)
        
        for stream_url in stream_urls:
            if validate_stream_url(stream_url):
                logger.info(f"Found stream URL: {stream_url}")
                stream_type = determine_stream_type(stream_url)
                return {"success": True, "m3u8": stream_url, "source": "extracted", "type": stream_type}
        
        # If no streams found, return the multiembed URL as fallback
        return {"success": True, "m3u8": multiembed_url, "source": "multiembed", "type": "iframe"}
        
    except Exception as e:
        logger.error(f"Multiembed extraction failed: {str(e)}")
        return {"success": False, "error": f"Multiembed extraction failed: {str(e)}"}

def extract_iframe_urls(html_content, base_url):
    """Extract iframe URLs from HTML content"""
    iframe_pattern = r'<iframe[^>]+src=["\']([^"\']+)["\']'
    iframe_matches = re.findall(iframe_pattern, html_content, re.IGNORECASE)
    
    iframe_urls = []
    for iframe_src in iframe_matches:
        # Make URL absolute if needed
        if iframe_src.startswith('//'):
            iframe_url = 'https:' + iframe_src
        elif iframe_src.startswith('/'):
            iframe_url = urljoin(base_url, iframe_src)
        else:
            iframe_url = iframe_src
        
        iframe_urls.append(iframe_url)
    
    return iframe_urls

def prioritize_iframes(iframe_urls, preferred_source):
    """Prioritize iframe URLs based on source preference"""
    if preferred_source == 'auto':
        # Default priority
        priority_order = ['vidsrc', 'mixdrop', 'streamwish', 'doodstream', 'embed']
    else:
        priority_order = [preferred_source, 'vidsrc', 'mixdrop', 'streamwish', 'doodstream', 'embed']
    
    prioritized = []
    
    # First, add iframes that match priority order
    for source in priority_order:
        for url in iframe_urls:
            if source in url.lower() and url not in prioritized:
                prioritized.append(url)
    
    # Then add any remaining iframes
    for url in iframe_urls:
        if url not in prioritized:
            prioritized.append(url)
    
    return prioritized

def extract_m3u8_from_content(content):
    """Extract M3U8 URLs from HTML content"""
    # Enhanced patterns to find M3U8 URLs
    patterns = [
        r'(?:src|source|url|file|playlist)["\':\s]*["\']([^"\']*\.m3u8[^"\']*)["\']',
        r'["\']([^"\']*\.m3u8[^"\']*)["\']',
        r'https?://[^"\s<>]+\.m3u8[^"\s<>]*',
        r'player\.src\s*\(\s*["\']([^"\']*\.m3u8[^"\']*)["\']',
        r'videojs.*?src["\']?\s*:\s*["\']([^"\']*\.m3u8[^"\']*)["\']',
        r'jwplayer\([^)]*\)\.setup\([^)]*file["\']?\s*:\s*["\']([^"\']*\.m3u8[^"\']*)["\']'
    ]
    
    m3u8_urls = []
    
    for pattern in patterns:
        matches = re.findall(pattern, content, re.IGNORECASE)
        for match in matches:
            if '.m3u8' in match and match.startswith('http'):
                m3u8_urls.append(match)
    
    return list(set(m3u8_urls))  # Remove duplicates

def extract_streaming_urls(content):
    """Extract various streaming URLs from content"""
    patterns = [
        r'https?://[^"\s<>]+\.m3u8[^"\s<>]*',
        r'https?://[^"\s<>]+\.mp4[^"\s<>]*',
        r'https?://[^"\s<>]+/embed/[^"\s<>]*',
        r'https?://[^"\s<>]+/stream/[^"\s<>]*',
        r'https?://[^"\s<>]+/player/[^"\s<>]*'
    ]
    
    urls = []
    for pattern in patterns:
        matches = re.findall(pattern, content, re.IGNORECASE)
        urls.extend(matches)
    
    return list(set(urls))

def extract_m3u8_from_generic_iframe(iframe_url):
    """Extract M3U8 from generic iframe"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'https://multiembed.mov/'
        }
        
        response = requests.get(iframe_url, headers=headers, timeout=15)
        
        if response.status_code == 200:
            m3u8_urls = extract_m3u8_from_content(response.text)
            
            for m3u8_url in m3u8_urls:
                if validate_stream_url(m3u8_url):
                    return m3u8_url
        
        return None
        
    except Exception as e:
        logger.warning(f"Generic iframe extraction failed for {iframe_url}: {str(e)}")
        return None

def determine_stream_type(url):
    """Determine the type of stream from URL"""
    if not url:
        return 'unknown'
    
    url_lower = url.lower()
    
    if '.m3u8' in url_lower:
        return 'hls'
    elif '.mp4' in url_lower:
        return 'mp4'
    elif any(keyword in url_lower for keyword in ['embed', 'player', 'iframe']):
        return 'iframe'
    else:
        return 'unknown'

def validate_stream_url(url):
    """Validate if a URL is a valid streaming URL"""
    try:
        # Basic URL validation
        parsed = urlparse(url)
        if not parsed.scheme or not parsed.netloc:
            return False
        
        # Quick check for streaming indicators
        if any(ext in url.lower() for ext in ['.m3u8', '.mp4', '/embed/', '/stream/', '/player/']):
            return True
        
        return False
        
    except Exception as e:
        logger.debug(f"URL validation failed for {url}: {str(e)}")
        return False

def cleanup_browser():
    """Clean up browser resources"""
    pass  # No persistent browser to clean up in this implementation

# Clean up on module exit
import atexit
atexit.register(cleanup_browser)
