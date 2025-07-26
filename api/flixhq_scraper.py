# backend/api/flixhq_scraper.py

def get_stream_for_imdb(imdb_id, title=None, year=None):
    """
    Returns the FlixHQ embed iframe URL for the movie/show corresponding to IMDb ID.
    FlixHQ often uses direct embed URLs by IMDb.
    """
    try:
        stream_url = f"https://flixhq.to/embed/{imdb_id}"
        return {
            "stream_url": stream_url,
            "embed": True,
            "quality": "HD"
        }
    except Exception as e:
        print(f"[flixhq_scraper] error: {e}")
        return {}
