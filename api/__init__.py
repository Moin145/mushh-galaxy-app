# API module initialization
from .stream_fetcher import get_m3u8_from_multiembed
from .mixdrop_scraper import extract_m3u8_from_mixdrop
from .auto_stream_scraper import get_best_stream
from .m3u8_scraper import extract_m3u8_playwright
from .omdb_fetcher import fetch_movie_by_title, search_movies_by_keyword, get_movie_details
from .vidsrc_api import get_stream_for_imdb
from .vidsrc_scraper import extract_from_vidsrc

__all__ = [
    'get_m3u8_from_multiembed',
    'extract_m3u8_from_mixdrop',
    'get_best_stream',
    'extract_m3u8_playwright',
    'fetch_movie_by_title',
    'search_movies_by_keyword',
    'get_movie_details',
    'get_best_stream_api',
    'extract_from_vidsrc'
]
