import os
import requests
import logging

logger = logging.getLogger(__name__)

# Multiple API keys for redundancy
OMDB_API_KEYS = [
    os.getenv("OMDB_API_KEY", "e6bc1ee7"), 
    "e4e540f4", 
    "3d1c1e95", 
    "b6003d8a",
    "2dde6ad0",
    "4c9f1b2a"
]

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
            url = f"http://www.omdbapi.com/?apikey={api_key}&t={title}&plot=full"
            response = requests.get(url, timeout=10)
            
            if response.status_code != 200:
                continue  # Try next API key
            
            data = response.json()
            
            if data.get("Response") == "False":
                continue  # Try next API key
            
            result = format_movie_data(data)
            
            logger.info(f"Successfully fetched movie: {result['title']} ({result['year']})")
            return result
            
        except Exception as e:
            logger.error(f"Error with API key {api_key}: {str(e)}")
            continue
    
    # If all API keys failed
    raise Exception(f"All OMDb API keys failed for title: {title}")

def search_movies_by_keyword(keyword):
    """
    Search for movies using OMDb API
    
    Args:
        keyword (str): Search keyword
    
    Returns:
        list: List of movie results
    """
    logger.info(f"Searching movies with keyword: {keyword}")
    
    all_movies = []
    
    # Try multiple API keys
    for api_key in OMDB_API_KEYS:
        try:
            # Search with the original keyword
            url = f"http://www.omdbapi.com/?apikey={api_key}&s={keyword}&type=movie"
            response = requests.get(url, timeout=10)
            
            if response.status_code != 200:
                continue  # Try next API key
            
            data = response.json()
            
            if data.get("Response") == "False":
                continue  # Try next API key
            
            search_results = data.get("Search", [])
            
            # Filter and clean results
            for movie in search_results:
                if movie.get("Type") == "movie" and movie.get("imdbID"):
                    movie_data = {
                        "Title": movie.get("Title"),
                        "Year": movie.get("Year"),
                        "imdbID": movie.get("imdbID"),
                        "Poster": movie.get("Poster") if movie.get("Poster") != "N/A" else None
                    }
                    # Avoid duplicates
                    if not any(m["imdbID"] == movie_data["imdbID"] for m in all_movies):
                        all_movies.append(movie_data)
            
            # Also try searching for common variations for series
            if keyword.lower() in ['bahubali', 'avengers', 'batman', 'spider-man', 'harry potter', 'lord of the rings']:
                variations = [
                    f"{keyword} part",
                    f"{keyword} chapter", 
                    f"{keyword} volume",
                    f"{keyword} episode",
                    f"{keyword} 1",
                    f"{keyword} 2",
                    f"{keyword} 3",
                    f"{keyword} the beginning",
                    f"{keyword} the conclusion",
                    f"{keyword} the final chapter"
                ]
                
                # Special handling for Bahubali
                if keyword.lower() == 'bahubali':
                    variations.extend([
                        "Baahubali",
                        "Baahubali: The Beginning",
                        "Baahubali 2: The Conclusion",
                        "Baahubali: The Beginning",
                        "Baahubali: The Conclusion"
                    ])
                
                for variation in variations:
                    try:
                        var_url = f"http://www.omdbapi.com/?apikey={api_key}&s={variation}&type=movie"
                        var_response = requests.get(var_url, timeout=10)
                        
                        if var_response.status_code == 200:
                            var_data = var_response.json()
                            if var_data.get("Response") == "True":
                                var_results = var_data.get("Search", [])
                                for movie in var_results:
                                    if movie.get("Type") == "movie" and movie.get("imdbID"):
                                        movie_data = {
                                            "Title": movie.get("Title"),
                                            "Year": movie.get("Year"),
                                            "imdbID": movie.get("imdbID"),
                                            "Poster": movie.get("Poster") if movie.get("Poster") != "N/A" else None
                                        }
                                        # Avoid duplicates
                                        if not any(m["imdbID"] == movie_data["imdbID"] for m in all_movies):
                                            all_movies.append(movie_data)
                    except Exception as e:
                        logger.error(f"Error searching variation {variation}: {str(e)}")
                        continue
            
            logger.info(f"Found {len(all_movies)} total movies for keyword: {keyword}")
            return all_movies[:50]  # Return up to 50 results for better series coverage
            
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
    
    # Try multiple API keys
    for api_key in OMDB_API_KEYS:
        try:
            url = f"http://www.omdbapi.com/?apikey={api_key}&i={imdb_id}&plot=full"
            response = requests.get(url, timeout=10)
            
            if response.status_code != 200:
                continue  # Try next API key
            
            data = response.json()
            
            if data.get("Response") == "False":
                continue  # Try next API key
            
            result = format_movie_data(data)
            
            logger.info(f"Successfully fetched detailed info for: {result['title']}")
            return result
            
        except Exception as e:
            logger.error(f"Error with API key {api_key}: {str(e)}")
            continue
    
    # If all API keys failed
    raise Exception(f"Failed to fetch movie details for IMDb ID: {imdb_id}")

def format_movie_data(data):
    """Format movie data from OMDb API response"""
    return {
        "title": data.get("Title"),
        "year": data.get("Year"),
        "plot": data.get("Plot"),
        "poster": data.get("Poster") if data.get("Poster") != "N/A" else None,
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
        "boxOffice": data.get("BoxOffice"),
        "released": data.get("Released"),
        "writer": data.get("Writer"),
        "production": data.get("Production"),
        "website": data.get("Website")
    }

def get_popular_movies():
    """Get a list of popular movies"""
    popular_titles = [
        "The Shawshank Redemption",
        "The Godfather",
        "The Dark Knight",
        "Pulp Fiction",
        "The Lord of the Rings: The Return of the King",
        "Forrest Gump",
        "Inception",
        "The Matrix",
        "Goodfellas",
        "The Silence of the Lambs",
        "Seven",
        "Fight Club",
        "The Lord of the Rings: The Fellowship of the Ring",
        "Star Wars: Episode IV - A New Hope",
        "The Lord of the Rings: The Two Towers",
        "Interstellar",
        "The Departed",
        "The Prestige",
        "Gladiator",
        "Saving Private Ryan"
    ]
    
    movies = []
    for title in popular_titles:
        try:
            movie = fetch_movie_by_title(title)
            if movie:
                movies.append(movie)
        except:
            continue
    
    return movies

def validate_imdb_id(imdb_id):
    """Validate IMDb ID format"""
    import re
    pattern = r'^tt\d{7,8}$'
    return re.match(pattern, imdb_id) is not None
