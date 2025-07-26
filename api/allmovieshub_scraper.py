import concurrent.futures
import time
import json

from .vidsrc_api import get_stream_for_imdb as get_vidsrc
from .multiembed_scraper import get_stream_for_imdb as get_multiembed
from .flixhq_scraper import get_stream_for_imdb as get_flixhq
from .tplayer_scraper import get_stream_for_imdb as get_tplayer

# Redis Setup
import redis

REDIS_URL = "redis://localhost:6379/0"  # Update if you use a different host/port/db
CACHE_TTL_SECONDS = 900  # 15 minutes
_redis = None
try:
    _redis = redis.Redis.from_url(REDIS_URL)
    _redis.ping()
    REDIS_AVAILABLE = True
except Exception as e:
    print(f"[auto_stream_scraper] Redis connection failed: {e}")
    REDIS_AVAILABLE = False

# Fallback in-memory cache
_stream_cache = {}

def get_stream_for_imdb(imdb_id, title=None, year=None):
    # ... your scraper logic ...
    return {"stream_url": "..."}

def _fetch_source(func, imdb_id, title=None, year=None):
    try:
        return func(imdb_id, title, year)
    except Exception as e:
        print(f"[auto_stream_scraper] Exception in {func.__name__}: {e}")
        return None

def get_best_stream(imdb_id, title=None, year=None):
    now = int(time.time())
    cache_key = f"stream:{imdb_id}"

    # --- 1. Try Redis cache first
    if REDIS_AVAILABLE:
        cached = _redis.get(cache_key)
        if cached:
            try:
                result = json.loads(cached)
                return result
            except Exception as e:
                print(f"[auto_stream_scraper] Redis cache decode error: {e}")

    # --- 2. Try in-memory cache as secondary
    cached = _stream_cache.get(imdb_id)
    if cached:
        cached_time, result = cached
        if now - cached_time < CACHE_TTL_SECONDS:
            return result

    # --- 3. Fetch all sources in parallel
    sources = [
        ("VidSrc", get_vidsrc),
        ("MultiEmbed", get_multiembed),
        ("FlixHQ", get_flixhq),
        ("TPlayer", get_tplayer),
        ("AllMoviesHub", get_stream_for_imdb),
    ]

    embed_stream = None
    direct_stream = None

    with concurrent.futures.ThreadPoolExecutor(max_workers=len(sources)) as executor:
        future_to_source = {
            executor.submit(_fetch_source, func, imdb_id, title, year): name
            for name, func in sources
        }
        try:
            for future in concurrent.futures.as_completed(future_to_source, timeout=7):
                source_name = future_to_source[future]
                try:
                    result = future.result(timeout=5)
                    if not result or not result.get("stream_url"):
                        continue

                    result["source"] = source_name
                    url = result["stream_url"]
                    result["m3u8"] = url

                    if url.endswith(".m3u8") or url.endswith(".mp4"):
                        direct_stream = result
                        break
                    else:
                        if embed_stream is None:
                            embed_stream = result
                except Exception as e:
                    print(f"[auto_stream_scraper] Exception in future result ({source_name}): {e}")
        except concurrent.futures.TimeoutError:
            print("[auto_stream_scraper] Source queries timed out")

    # --- 4. Cache and return best available stream
    to_cache = None
    if direct_stream:
        to_cache = direct_stream
    elif embed_stream:
        to_cache = embed_stream
    else:
        to_cache = {"success": False, "error": "No working stream found"}

    # --- Save to Redis if available, else to in-memory cache
    if REDIS_AVAILABLE:
        try:
            _redis.setex(cache_key, CACHE_TTL_SECONDS, json.dumps(to_cache))
        except Exception as e:
            print(f"[auto_stream_scraper] Redis cache set error: {e}")

    _stream_cache[imdb_id] = (now, to_cache)
    return to_cache
