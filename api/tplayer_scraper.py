# backend/api/tplayer_scraper.py

def get_stream_for_imdb(imdb_id, title=None, year=None):
    """
    Returns TPlayer embed URL for given IMDb ID.
    TPlayer is frequently used in Indian streaming apps.
    """
    try:
        stream_url = f"https://tplayer.info/embed/{imdb_id}"
        return {
            "stream_url": stream_url,
            "embed": True,
            "quality": "HD"
        }
    except Exception as e:
        print(f"[tplayer_scraper] error: {e}")
        return {}
