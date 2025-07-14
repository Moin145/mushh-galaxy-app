import logging
from .mixdrop_scraper import extract_m3u8_from_mixdrop
from .vidsrc_scraper import extract_from_vidsrc
from .stream_fetcher import get_m3u8_from_multiembed
from .vidsrc_api import get_best_stream_api

logger = logging.getLogger(__name__)

def get_best_stream(imdb_id, preferred_source='auto'):
    """
    Get the best available stream for a given IMDb ID with intelligent fallback
    
    Args:
        imdb_id (str): IMDb ID
        preferred_source (str): Preferred source ('mixdrop', 'vidsrc', 'auto')
    
    Returns:
        dict: Stream result with success status and URL or error
    """
    logger.info(f"Getting best stream for IMDb ID: {imdb_id}, preferred source: {preferred_source}")
    
    # First try the API-based approach (faster and more reliable)
    try:
        logger.info("Trying API-based stream extraction...")
        api_result = get_best_stream_api(imdb_id, preferred_source)
        
        if api_result.get('success') and api_result.get('url'):
            logger.info(f"API-based stream successful: {api_result.get('source', 'unknown')}")
            
            # Determine stream type based on URL
            stream_url = api_result.get('url')
            stream_type = determine_stream_type(stream_url)
            
            return {
                "success": True,
                "m3u8": stream_url,
                "url": stream_url,
                "source": api_result.get('source', 'api'),
                "quality": "HD",
                "stream_type": stream_type,
                "backup_sources": get_backup_sources(imdb_id)
            }
    except Exception as e:
        logger.warning(f"API-based stream failed: {str(e)}")
    
    # Fallback to scraping-based approach with enhanced source priority
    source_priority = get_source_priority(preferred_source)
    
    last_error = None
    attempted_sources = []
    
    for source in source_priority:
        try:
            logger.info(f"Trying scraping source: {source}")
            attempted_sources.append(source)
            
            result = get_m3u8_from_multiembed(imdb_id, source)
            
            if result.get('success') and result.get('m3u8'):
                logger.info(f"Successfully got stream from {source}")
                
                # Determine stream type
                stream_url = result.get('m3u8')
                stream_type = determine_stream_type(stream_url)
                
                return {
                    "success": True,
                    "m3u8": stream_url,
                    "url": stream_url,
                    "source": source,
                    "quality": "HD",
                    "stream_type": stream_type,
                    "backup_sources": get_backup_sources(imdb_id, exclude=attempted_sources)
                }
            else:
                last_error = result.get('error', f'{source} failed')
                logger.warning(f"Source {source} failed: {last_error}")
                
        except Exception as e:
            last_error = str(e)
            logger.error(f"Exception with source {source}: {last_error}")
            continue
    
    # If all sources failed, return comprehensive error
    return {
        "success": False,
        "error": f"All sources failed. Attempted: {', '.join(attempted_sources)}. Last error: {last_error or 'Unknown error'}",
        "attempted_sources": attempted_sources,
        "backup_sources": get_backup_sources(imdb_id)
    }

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

def get_source_priority(preferred_source):
    """Get source priority list based on preference"""
    # Updated source priority based on NetMirror's architecture
    all_sources = ['auto', 'vidsrc', 'multiembed', 'streamwish', 'doodstream', 'mixdrop']
    
    if preferred_source == 'mixdrop':
        return ['mixdrop', 'vidsrc', 'multiembed', 'streamwish', 'doodstream', 'auto']
    elif preferred_source == 'vidsrc':
        return ['vidsrc', 'multiembed', 'streamwish', 'doodstream', 'mixdrop', 'auto']
    elif preferred_source == 'streamwish':
        return ['streamwish', 'vidsrc', 'multiembed', 'doodstream', 'mixdrop', 'auto']
    elif preferred_source == 'doodstream':
        return ['doodstream', 'streamwish', 'vidsrc', 'multiembed', 'mixdrop', 'auto']
    elif preferred_source == 'multiembed':
        return ['multiembed', 'vidsrc', 'streamwish', 'doodstream', 'mixdrop', 'auto']
    else:
        return ['auto', 'vidsrc', 'multiembed', 'streamwish', 'doodstream', 'mixdrop']

def get_backup_sources(imdb_id, exclude=None):
    """Get backup streaming sources for fallback"""
    if exclude is None:
        exclude = []
    
    backup_sources = []
    
    # Direct embed URLs that often work
    embed_sources = [
        {
            "name": "MultiEmbed",
            "url": f"https://multiembed.mov/movie/imdb/{imdb_id}",
            "type": "iframe"
        },
        {
            "name": "2embed",
            "url": f"https://2embed.cc/embed/movie?imdb={imdb_id}",
            "type": "iframe"
        },
        {
            "name": "VidSrc",
            "url": f"https://vidsrc.me/embed/movie?imdb={imdb_id}",
            "type": "iframe"
        },
        {
            "name": "EmbedSu",
            "url": f"https://embed.su/embed/movie/{imdb_id}",
            "type": "iframe"
        },
        {
            "name": "AutoEmbed",
            "url": f"https://autoembed.cc/movie/imdb/{imdb_id}",
            "type": "iframe"
        }
    ]
    
    # Filter out excluded sources
    for source in embed_sources:
        if source["name"].lower() not in [s.lower() for s in exclude]:
            backup_sources.append(source)
    
    return backup_sources

def get_mixdrop_stream(imdb_id):
    """
    Get stream specifically from MixDrop
    
    Args:
        imdb_id (str): IMDb ID
    
    Returns:
        dict: Stream result
    """
    try:
        logger.info(f"Getting MixDrop stream for IMDb ID: {imdb_id}")
        
        return get_m3u8_from_multiembed(imdb_id, 'mixdrop')
        
    except Exception as e:
        logger.error(f"MixDrop stream fetch failed: {str(e)}")
        return {"success": False, "error": str(e)}

def get_vidsrc_stream(imdb_id):
    """
    Get stream specifically from VidSrc
    
    Args:
        imdb_id (str): IMDb ID
    
    Returns:
        dict: Stream result
    """
    try:
        logger.info(f"Getting VidSrc stream for IMDb ID: {imdb_id}")
        
        return get_m3u8_from_multiembed(imdb_id, 'vidsrc')
        
    except Exception as e:
        logger.error(f"VidSrc stream fetch failed: {str(e)}")
        return {"success": False, "error": str(e)}

def validate_stream_url(url):
    """Validate if a stream URL is accessible"""
    try:
        import requests
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'https://multiembed.mov/'
        }
        
        response = requests.head(url, headers=headers, timeout=10)
        return response.status_code == 200
        
    except Exception as e:
        logger.warning(f"URL validation failed for {url}: {str(e)}")
        return False
