import requests
import logging
import json
from urllib.parse import urljoin, quote
import time
import random

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
            # Enhanced embed sources with better working URLs
            embed_sources = [
                # Most reliable sources first
                f"https://multiembed.mov/directstream.php?video_id={imdb_id}&imdb=1",
                f"https://vidsrc.me/embed/movie?imdb={imdb_id}",
                f"https://2embed.cc/embed/movie?imdb={imdb_id}",
                f"https://www.2embed.to/embed/imdb/movie?id={imdb_id}",
                f"https://embed.su/embed/movie/{imdb_id}",
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
                f"https://movieshd.watch/embed/movie/{imdb_id}",
                f"https://fsapi.xyz/movie-watch/{imdb_id}",
                f"https://database.gdriveplayer.us/player.php?imdb={imdb_id}",
                f"https://moviee.tv/embed/movie/{imdb_id}",
                f"https://www.moviesm4u.net/embed/movie/{imdb_id}"
            ]
            
            # Shuffle sources to distribute load
            random.shuffle(embed_sources)
            
            for embed_url in embed_sources:
                try:
                    logger.info(f"Trying embed source: {embed_url}")
                    
                    # Quick test with appropriate timeout
                    response = self.session.get(embed_url, timeout=10)
                    
                    if response.status_code == 200:
                        # Check if the response contains video player elements
                        content = response.text.lower()
                        video_indicators = [
                            'video', 'player', 'stream', 'embed', 'iframe', 'source',
                            'jwplayer', 'videojs', 'plyr', 'flowplayer', 'hls.js'
                        ]
                        
                        if any(indicator in content for indicator in video_indicators):
                            logger.info(f"Successfully found working stream: {embed_url}")
                            
                            # Try to extract direct M3U8 URLs
                            m3u8_urls = self._extract_m3u8_from_content(response.text)
                            if m3u8_urls:
                                # Validate the M3U8 URL
                                for m3u8_url in m3u8_urls:
                                    if self._validate_m3u8_url(m3u8_url):
                                        logger.info(f"Found valid direct M3U8: {m3u8_url}")
                                        return {"success": True, "url": m3u8_url, "source": "direct_m3u8"}
                            
                            return {"success": True, "url": embed_url, "source": "embed"}
                    
                except Exception as e:
                    logger.warning(f"Failed to test embed URL {embed_url}: {str(e)}")
                    continue
            
            # If no working URL found, return the first one as fallback
            fallback_url = embed_sources[0]
            logger.info(f"No verified working URL found, using fallback: {fallback_url}")
            return {"success": True, "url": fallback_url, "source": "embed"}
                
        except Exception as e:
            logger.error(f"VidSrc API error: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def _extract_m3u8_from_content(self, content):
        """Extract M3U8 URLs from HTML content"""
        import re
        
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
    
    def _validate_m3u8_url(self, url):
        """Validate if a URL is a working M3U8 stream"""
        try:
            response = self.session.head(url, timeout=8)
            if response.status_code == 200:
                content_type = response.headers.get('content-type', '').lower()
                return any(ct in content_type for ct in ['mpegurl', 'x-mpegurl', 'vnd.apple.mpegurl'])
            return False
        except:
            return False
    
    def _extract_stream_urls(self, content):
        """Extract stream URLs from HTML content"""
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
        self.base_urls = [
            "https://streamwish.to",
            "https://awish.pro",
            "https://streamwish.com",
            "https://playwish.to",
            "https://streamwish.site"
        ]
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': '*/*',
            'Accept-Language': 'en-US,en;q=0.5'
        })
    
    def get_movie_stream(self, imdb_id):
        """Get streaming URL for a movie using IMDb ID"""
        try:
            # Try different StreamWish endpoints
            for base_url in self.base_urls:
                endpoints = [
                    f"{base_url}/embed/movie/{imdb_id}",
                    f"{base_url}/e/{imdb_id}",
                    f"{base_url}/v/{imdb_id}"
                ]
                
                for endpoint in endpoints:
                    try:
                        logger.info(f"Trying StreamWish endpoint: {endpoint}")
                        response = self.session.get(endpoint, timeout=10)
                        
                        if response.status_code == 200:
                            content = response.text.lower()
                            if any(keyword in content for keyword in ['video', 'player', 'stream']):
                                return {"success": True, "url": endpoint, "source": "streamwish"}
                    except:
                        continue
            
            return {"success": False, "error": "No valid StreamWish streams found"}
            
        except Exception as e:
            logger.error(f"StreamWish API error: {str(e)}")
            return {"success": False, "error": str(e)}


class DoodstreamAPI:
    """
    Doodstream API client for fetching streaming URLs
    """
    
    def __init__(self):
        self.base_urls = [
            "https://doodstream.com",
            "https://dood.to",
            "https://dood.la",
            "https://dooood.com",
            "https://dood.ws"
        ]
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': '*/*'
        })
    
    def get_movie_stream(self, imdb_id):
        """Get streaming URL for a movie using IMDb ID"""
        try:
            # Try different Doodstream endpoints
            for base_url in self.base_urls:
                endpoints = [
                    f"{base_url}/embed/movie/{imdb_id}",
                    f"{base_url}/e/{imdb_id}",
                    f"{base_url}/d/{imdb_id}"
                ]
                
                for endpoint in endpoints:
                    try:
                        logger.info(f"Trying Doodstream endpoint: {endpoint}")
                        response = self.session.get(endpoint, timeout=10)
                        
                        if response.status_code == 200:
                            content = response.text.lower()
                            if any(keyword in content for keyword in ['video', 'player', 'stream']):
                                return {"success": True, "url": endpoint, "source": "doodstream"}
                    except:
                        continue
            
            return {"success": False, "error": "No valid Doodstream streams found"}
            
        except Exception as e:
            logger.error(f"Doodstream API error: {str(e)}")
            return {"success": False, "error": str(e)}


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

def test_stream_sources(imdb_id):
    """Test all available streaming sources for a given IMDb ID"""
    results = {}
    
    # Test VidSrc
    try:
        vidsrc = VidSrcAPI()
        results['vidsrc'] = vidsrc.get_movie_stream(imdb_id)
    except Exception as e:
        results['vidsrc'] = {"success": False, "error": str(e)}
    
    # Test StreamWish
    try:
        streamwish = StreamWishAPI()
        results['streamwish'] = streamwish.get_movie_stream(imdb_id)
    except Exception as e:
        results['streamwish'] = {"success": False, "error": str(e)}
    
    # Test Doodstream
    try:
        doodstream = DoodstreamAPI()
        results['doodstream'] = doodstream.get_movie_stream(imdb_id)
    except Exception as e:
        results['doodstream'] = {"success": False, "error": str(e)}
    
    return results
