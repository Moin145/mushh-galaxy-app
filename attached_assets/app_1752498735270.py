import os
import logging
from flask import Flask, render_template, jsonify, request
from flask_cors import CORS

# Configure logging for debugging
logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__, template_folder='templates', static_folder='static')
app.secret_key = os.environ.get("SESSION_SECRET", "fallback_secret_key_for_dev")

# Enable CORS for video streaming
CORS(app, resources={
    r"/api/*": {
        "origins": "*",
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})

# Required for relative imports
from api.stream_fetcher import get_m3u8_from_multiembed
from api.omdb_fetcher import fetch_movie_by_title, search_movies_by_keyword

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/watch/<imdb_id>')
def watch_movie(imdb_id):
    return render_template('watch.html', imdb_id=imdb_id)

@app.route('/api/stream/<imdb_id>')
def get_stream(imdb_id):
    source = request.args.get('source', 'auto')
    
    try:
        app.logger.info(f"Attempting to get stream for IMDb ID: {imdb_id} with source: {source}")
        result = get_m3u8_from_multiembed(imdb_id, source)
        
        if result.get('success'):
            app.logger.info(f"Successfully found stream: {result.get('m3u8', 'No URL')[:100]}...")
        else:
            app.logger.error(f"Stream fetch failed: {result.get('error', 'Unknown error')}")
            
        return jsonify(result)
    except Exception as e:
        app.logger.error(f"Exception in get_stream: {str(e)}")
        return jsonify({"error": str(e), "success": False})

@app.route('/api/search')
def search_movies():
    title = request.args.get('title', '')
    
    if not title:
        return jsonify({"error": "Title parameter is required", "success": False})
    
    try:
        app.logger.info(f"Searching for movies with title: {title}")
        result = search_movies_by_keyword(title)
        return jsonify(result)
    except Exception as e:
        app.logger.error(f"Search failed: {str(e)}")
        return jsonify({"error": str(e), "success": False})

@app.route('/api/movie/<title>')
def get_movie_details(title):
    try:
        app.logger.info(f"Fetching movie details for: {title}")
        result = fetch_movie_by_title(title)
        return jsonify(result)
    except Exception as e:
        app.logger.error(f"Movie fetch failed: {str(e)}")
        return jsonify({"error": str(e), "success": False})

@app.after_request
def after_request(response):
    # Add CORS headers for video streaming
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

if __name__ == '__main__':
    # Create necessary folders if they don't exist
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static', exist_ok=True)
    os.makedirs('api', exist_ok=True)
    
    app.logger.info("Starting MOinMirror streaming application...")
    app.run(host='0.0.0.0', port=5000, debug=True)
