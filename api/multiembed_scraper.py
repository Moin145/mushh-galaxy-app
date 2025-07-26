# backend/api/multiembed_scraper.py

def get_stream_for_imdb(imdb_id, title=None, year=None):
    """
    Returns MultiEmbed iframe URL for given IMDb ID for embedding video player.
    MultiEmbed provides multiple source embeds.
    """
    try:
        stream_url = f"https://multiembed.to/embed/{imdb_id}"
        return {
            "stream_url": stream_url,
            "embed": True,
            "quality": "HD"
        }
    except Exception as e:
        print(f"[multiembed_scraper] error: {e}")
        return {}
