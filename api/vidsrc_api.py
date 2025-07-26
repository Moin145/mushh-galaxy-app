# backend/api/vidsrc_api.py

import requests

# Your actual OMDb API key, as provided
OMDB_API_KEY = "cd575855"

def get_omdb_metadata(imdb_id):
    """Fetch basic movie metadata for enriching streams."""
    if not OMDB_API_KEY:
        print("[vidsrc_api] Warning: OMDb API key not set.")
        return {}

    url = "http://www.omdbapi.com/"
    params = {
        "apikey": OMDB_API_KEY,
        "i": imdb_id,
        "plot": "short",
    }
    try:
        resp = requests.get(url, params=params, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            if data.get("Response") == "True":
                return data
    except Exception as e:
        print(f"[vidsrc_api] OMDb metadata fetch error: {e}")
    return {}

def get_stream_for_imdb(imdb_id, title=None, year=None):
    """
    Return the VidSrc embed URL for the given IMDb ID along with enriched metadata.
    """
    try:
        stream_url = f"https://vidsrc.me/embed/{imdb_id}"
        metadata = get_omdb_metadata(imdb_id)
        return {
            "stream_url": stream_url,
            "embed": True,
            "quality": "HD",
            "metadata": metadata
        }
    except Exception as e:
        print(f"[vidsrc_api] get_stream_for_imdb error: {e}")
        return {}
