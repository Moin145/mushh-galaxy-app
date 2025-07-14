import os
import requests
import logging

logger = logging.getLogger(__name__)

# Get API key from environment or use fallback with backup
OMDB_API_KEYS = [os.getenv("OMDB_API_KEY", "e6bc1ee7"), "e4e540f4"]

def fetch_movie_by_title(title):
    """
    Fetch movie details from OMDb API by title
    
    Args:
        title (str): Movie title
    
    Returns:
        dict: Movie details
    """
    logger.info(f"Fetching movie details for: {title}")
    
    # Try multiple API keys
    for api_key in OMDB_API_KEYS:
        try:
            url = f"http://www.omdbapi.com/?apikey={api_key}&t={title}"
            response = requests.get(url, timeout=10)
            
            if response.status_code != 200:
                continue  # Try next API key
            
            data = response.json()
            
            if data.get("Response") == "False":
                continue  # Try next API key
            
            imdb_id = data.get("imdbID")
            
            result = {
                "title": data.get("Title"),
                "year": data.get("Year"),
                "plot": data.get("Plot"),
                "poster": data.get("Poster"),
                "imdbID": imdb_id,
                "genre": data.get("Genre"),
                "director": data.get("Director"),
                "actors": data.get("Actors"),
                "rating": data.get("imdbRating"),
                "runtime": data.get("Runtime")
            }
            
            logger.info(f"Successfully fetched movie: {result['title']} ({result['year']})")
            return result
            
        except Exception as e:
            logger.error(f"Error with API key {api_key}: {str(e)}")
            continue
    
    # If all API keys failed
    raise Exception("All OMDb API keys failed")

def search_movies_by_keyword(keyword):
    """
    Search for movies using OMDb API
    
    Args:
        keyword (str): Search keyword
    
    Returns:
        list: List of movie results
    """
    logger.info(f"Searching movies with keyword: {keyword}")
    
    # Try multiple API keys
    for api_key in OMDB_API_KEYS:
        try:
            url = f"http://www.omdbapi.com/?apikey={api_key}&s={keyword}&type=movie"
            response = requests.get(url, timeout=10)
            
            if response.status_code != 200:
                continue  # Try next API key
            
            data = response.json()
            
            if data.get("Response") == "False":
                continue  # Try next API key
            
            search_results = data.get("Search", [])
            
            # Filter and clean results
            movies = []
            for movie in search_results:
                if movie.get("Type") == "movie" and movie.get("imdbID"):
                    movies.append({
                        "Title": movie.get("Title"),
                        "Year": movie.get("Year"),
                        "imdbID": movie.get("imdbID"),
                        "Poster": movie.get("Poster") if movie.get("Poster") != "N/A" else None
                    })
            
            logger.info(f"Found {len(movies)} movies for keyword: {keyword}")
            return movies[:10]  # Return max 10 results
            
        except Exception as e:
            logger.error(f"Error with API key {api_key}: {str(e)}")
            continue
    
    # If all API keys failed
    logger.warning(f"No results found for keyword: {keyword}")
    return []

def get_movie_details(imdb_id):
    """
    Get detailed movie information by IMDb ID
    
    Args:
        imdb_id (str): IMDb ID
    
    Returns:
        dict: Detailed movie information
    """
    logger.info(f"Getting movie details for IMDb ID: {imdb_id}")
    
    try:
        url = f"http://www.omdbapi.com/?apikey={OMDB_API_KEY}&i={imdb_id}"
        response = requests.get(url, timeout=10)
        
        if response.status_code != 200:
            raise Exception(f"OMDb API returned status {response.status_code}")
        
        data = response.json()
        
        if data.get("Response") == "False":
            raise Exception(f"Movie not found: {data.get('Error', 'Unknown error')}")
        
        result = {
            "title": data.get("Title"),
            "year": data.get("Year"),
            "plot": data.get("Plot"),
            "poster": data.get("Poster"),
            "imdbID": data.get("imdbID"),
            "genre": data.get("Genre"),
            "director": data.get("Director"),
            "actors": data.get("Actors"),
            "rating": data.get("imdbRating"),
            "runtime": data.get("Runtime"),
            "country": data.get("Country"),
            "language": data.get("Language"),
            "awards": data.get("Awards"),
            "metascore": data.get("Metascore"),
            "boxOffice": data.get("BoxOffice")
        }
        
        logger.info(f"Successfully fetched detailed info for: {result['title']}")
        return result
        
    except Exception as e:
        logger.error(f"Error getting movie details: {str(e)}")
        raise
