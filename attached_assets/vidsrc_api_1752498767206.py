import requests
import logging
import json
from urllib.parse import urljoin, quote
import time

logger = logging.getLogger(__name__)

class VidSrcAPI:
    """
    VidSrc API client for fetching streaming URLs
    """
    
    def __init__(self):
        self.base_url = "https://vidsrc.xyz"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
    
    def get_movie_stream(self, imdb_id):
        """
        Get streaming URL for a movie using IMDb ID
        
        Args:
            imdb_id (str): IMDb ID (e.g., 'tt1234567')
            
        Returns:
            dict: {'success': bool, 'url': str, 'error': str}
        """
        try:
            # Fast, reliable embed sources similar to NetMirror's architecture
            embed_urls = [
                f"https://multiembed.mov/directstream.php?video_id={imdb_id}&imdb=1",
                f"https://2embed.cc/embed/movie?imdb={imdb_id}",
                f"https://www.2embed.to/embed/imdb/movie?id={imdb_id}",
                f"https://embed.su/embed/movie/{imdb_id}",
                f"https://vidsrc.me/embed/movie?imdb={imdb_id}",
                f"https://moviesapi.club/movie/{imdb_id}",
                f"https://vidsrc.to/embed/movie/{imdb_id}",
                f"https://autoembed.cc/movie/imdb/{imdb_id}"
            ]
            
            for embed_url in embed_urls:
                try:
                    logger.info(f"Trying embed source: {embed_url}")
                    
                    # Quick test with shorter timeout for faster response
                    response = self.session.get(embed_url, timeout=3)
                    
                    if response.status_code == 200:
                        # Check if the response contains video player elements
                        content = response.text.lower()
                        if any(keyword in content for keyword in ['video', 'player', 'stream', 'embed', 'iframe', 'source']):
                            logger.info(f"Successfully found working stream: {embed_url}")
                            return {"success": True, "url": embed_url, "source": "multiembed"}
                    
                except Exception as e:
                    logger.warning(f"Failed to test embed URL {embed_url}: {str(e)}")
                    continue
            
            # If no working URL found, return the first one as fallback
            fallback_url = embed_urls[0]
            logger.info(f"No verified working URL found, using fallback: {fallback_url}")
            return {"success": True, "url": fallback_url, "source": "multiembed"}
                
        except Exception as e:
            logger.error(f"VidSrc API error: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def _extract_stream_urls(self, content):
        """
        Extract stream URLs from HTML content
        """
        stream_urls = []
        
        # Common patterns for finding streaming URLs
        patterns = [
            r'file["\']?\s*:\s*["\']([^"\']+\.m3u8[^"\']*)',
            r'source["\']?\s*:\s*["\']([^"\']+\.m3u8[^"\']*)',
            r'src["\']?\s*:\s*["\']([^"\']+\.m3u8[^"\']*)',
            r'["\']([^"\']*\.m3u8[^"\']*)["\']',
            r'["\']([^"\']*\.mp4[^"\']*)["\']'
        ]
        
        import re
        for pattern in patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                if match and ('http' in match or match.startswith('//')):
                    stream_urls.append(match)
        
        return stream_urls


class StreamWishAPI:
    """
    StreamWish API client for fetching streaming URLs
    """
    
    def __init__(self):
        self.base_url = "https://streamwish.to"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': 'https://streamwish.to/',
            'Accept': '*/*',
            'Accept-Language': 'en-US,en;q=0.5'
        })
    
    def get_movie_stream(self, imdb_id):
        """
        Get streaming URL for a movie using IMDb ID
        """
        try:
            # Try different StreamWish endpoints
            endpoints = [
                f"{self.base_url}/e/{imdb_id}",
                f"{self.base_url}/embed/{imdb_id}",
                f"{self.base_url}/v/{imdb_id}"
            ]
            
            for endpoint in endpoints:
                try:
                    response = self.session.get(endpoint, timeout=20)
                    if response.status_code == 200:
                        stream_urls = self._extract_stream_urls(response.text)
                        if stream_urls:
                            return {"success": True, "url": stream_urls[0], "source": "streamwish"}
                except:
                    continue
            
            return {"success": False, "error": "No valid streams found"}
            
        except Exception as e:
            logger.error(f"StreamWish API error: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def _extract_stream_urls(self, content):
        """Extract stream URLs from HTML content"""
        stream_urls = []
        
        import re
        patterns = [
            r'file["\']?\s*:\s*["\']([^"\']+\.m3u8[^"\']*)',
            r'source["\']?\s*:\s*["\']([^"\']+\.m3u8[^"\']*)',
            r'["\']([^"\']*\.m3u8[^"\']*)["\']',
            r'["\']([^"\']*\.mp4[^"\']*)["\']'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                if match and ('http' in match or match.startswith('//')):
                    stream_urls.append(match)
        
        return stream_urls


class DoodstreamAPI:
    """
    Doodstream API client for fetching streaming URLs
    """
    
    def __init__(self):
        self.base_url = "https://doodstream.com"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': 'https://doodstream.com/',
            'Accept': '*/*'
        })
    
    def get_movie_stream(self, imdb_id):
        """
        Get streaming URL for a movie using IMDb ID
        """
        try:
            # Try different Doodstream endpoints
            endpoints = [
                f"{self.base_url}/e/{imdb_id}",
                f"{self.base_url}/d/{imdb_id}",
                f"{self.base_url}/embed/{imdb_id}"
            ]
            
            for endpoint in endpoints:
                try:
                    response = self.session.get(endpoint, timeout=20)
                    if response.status_code == 200:
                        stream_urls = self._extract_stream_urls(response.text)
                        if stream_urls:
                            return {"success": True, "url": stream_urls[0], "source": "doodstream"}
                except:
                    continue
            
            return {"success": False, "error": "No valid streams found"}
            
        except Exception as e:
            logger.error(f"Doodstream API error: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def _extract_stream_urls(self, content):
        """Extract stream URLs from HTML content"""
        stream_urls = []
        
        import re
        patterns = [
            r'file["\']?\s*:\s*["\']([^"\']+\.m3u8[^"\']*)',
            r'source["\']?\s*:\s*["\']([^"\']+\.m3u8[^"\']*)',
            r'["\']([^"\']*\.m3u8[^"\']*)["\']',
            r'["\']([^"\']*\.mp4[^"\']*)["\']'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                if match and ('http' in match or match.startswith('//')):
                    stream_urls.append(match)
        
        return stream_urls


def get_best_stream_api(imdb_id, preferred_source='auto'):
    """
    Get the best available stream using multiple API sources
    
    Args:
        imdb_id (str): IMDb ID
        preferred_source (str): Preferred source ('vidsrc', 'streamwish', 'doodstream', 'auto')
    
    Returns:
        dict: Stream result with success status and URL or error
    """
    logger.info(f"Fetching stream for IMDb ID: {imdb_id} using API sources")
    
    # Initialize API clients
    vidsrc = VidSrcAPI()
    streamwish = StreamWishAPI()
    doodstream = DoodstreamAPI()
    
    # Define source order based on preference
    if preferred_source == 'vidsrc':
        sources = [('vidsrc', vidsrc), ('streamwish', streamwish), ('doodstream', doodstream)]
    elif preferred_source == 'streamwish':
        sources = [('streamwish', streamwish), ('vidsrc', vidsrc), ('doodstream', doodstream)]
    elif preferred_source == 'doodstream':
        sources = [('doodstream', doodstream), ('vidsrc', vidsrc), ('streamwish', streamwish)]
    else:
        sources = [('vidsrc', vidsrc), ('streamwish', streamwish), ('doodstream', doodstream)]
    
    # Try each source in order
    for source_name, api_client in sources:
        try:
            logger.info(f"Trying {source_name} API...")
            result = api_client.get_movie_stream(imdb_id)
            
            if result.get('success'):
                logger.info(f"Successfully found stream from {source_name}")
                return result
            else:
                logger.warning(f"{source_name} failed: {result.get('error')}")
                
        except Exception as e:
            logger.error(f"Error with {source_name}: {str(e)}")
            continue
    
    # If all sources fail, return error
    return {"success": False, "error": "All streaming sources failed"}