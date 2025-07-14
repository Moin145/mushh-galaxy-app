import logging
from .mixdrop_scraper import extract_m3u8_from_mixdrop
from .vidsrc_scraper import extract_from_vidsrc
from .stream_fetcher import get_m3u8_from_multiembed

logger = logging.getLogger(__name__)

def get_best_stream(imdb_id, preferred_source='auto'):
    """
    Get the best available stream for a given IMDb ID
    
    Args:
        imdb_id (str): IMDb ID
        preferred_source (str): Preferred source ('mixdrop', 'vidsrc', 'auto')
    
    Returns:
        dict: Stream result with success status and URL or error
    """
    logger.info(f"Getting best stream for IMDb ID: {imdb_id}, preferred source: {preferred_source}")
    
    # Define source priority based on preference including new NetMirror sources
    if preferred_source == 'mixdrop':
        sources = ['mixdrop', 'vidsrc', 'streamwish', 'doodstream', 'auto']
    elif preferred_source == 'vidsrc':
        sources = ['vidsrc', 'streamwish', 'doodstream', 'mixdrop', 'auto']
    elif preferred_source == 'streamwish':
        sources = ['streamwish', 'vidsrc', 'doodstream', 'mixdrop', 'auto']
    elif preferred_source == 'doodstream':
        sources = ['doodstream', 'streamwish', 'vidsrc', 'mixdrop', 'auto']
    else:
        sources = ['auto', 'vidsrc', 'streamwish', 'doodstream', 'mixdrop']
    
    last_error = None
    
    for source in sources:
        try:
            logger.info(f"Trying source: {source}")
            
            result = get_m3u8_from_multiembed(imdb_id, source)
            
            if result.get('success') and result.get('m3u8'):
                logger.info(f"Successfully got stream from {source}")
                return result
            else:
                last_error = result.get('error', f'{source} failed')
                logger.warning(f"Source {source} failed: {last_error}")
                
        except Exception as e:
            last_error = str(e)
            logger.error(f"Exception with source {source}: {last_error}")
            continue
    
    # If all sources failed, return error
    return {
        "success": False,
        "error": f"All sources failed. Last error: {last_error or 'Unknown error'}"
    }

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
        
        # This would typically involve finding the MixDrop URL from multiembed
        # For now, we'll use the general stream fetcher with MixDrop preference
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
        
        # This would typically involve finding the VidSrc URL from multiembed
        # For now, we'll use the general stream fetcher with VidSrc preference
        return get_m3u8_from_multiembed(imdb_id, 'vidsrc')
        
    except Exception as e:
        logger.error(f"VidSrc stream fetch failed: {str(e)}")
        return {"success": False, "error": str(e)}
