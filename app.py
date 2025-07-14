import os
import logging
from flask import Flask, render_template, request, jsonify, redirect, url_for, Response
from flask_cors import CORS

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "netmirror-secret-key-2025")

# Enable CORS for video streaming with proper headers
CORS(app, origins=["*"], methods=["GET", "POST", "OPTIONS", "HEAD"], 
     allow_headers=["Content-Type", "Authorization", "X-Requested-With", "Range", "If-Range"],
     expose_headers=["Content-Length", "Content-Range", "Accept-Ranges"])

# Import API modules
from api import (
    get_best_stream,
    fetch_movie_by_title,
    search_movies_by_keyword,
    get_m3u8_from_multiembed,
    get_best_stream_api,
    get_movie_details
)

@app.route('/')
def index():
    """Main page with movie search and categories"""
    return render_template('index.html')

@app.route('/search')
def search():
    """Search movies by keyword"""
    query = request.args.get('q', '').strip()
    if not query:
        return jsonify({'movies': []})
    
    try:
        movies = search_movies_by_keyword(query)
        return jsonify({'movies': movies})
    except Exception as e:
        logger.error(f"Search error: {str(e)}")
        return jsonify({'error': 'Search failed', 'movies': []})

@app.route('/movie/<imdb_id>')
def movie_details(imdb_id):
    """Get movie details by IMDb ID"""
    try:
        movie = get_movie_details(imdb_id)
        if movie:
            return jsonify({'movie': movie})
        else:
            return jsonify({'error': 'Movie not found'}), 404
    except Exception as e:
        logger.error(f"Movie details error: {str(e)}")
        return jsonify({'error': 'Failed to fetch movie details'}), 500

@app.route('/watch/<imdb_id>')
def watch(imdb_id):
    """Video player page"""
    return render_template('watch.html', imdb_id=imdb_id)

@app.route('/api/stream/<imdb_id>')
def get_stream(imdb_id):
    """Get streaming URL for movie with enhanced error handling"""
    try:
        source = request.args.get('source', 'auto')
        logger.info(f"Getting stream for {imdb_id} with source: {source}")
        
        # Try to get the best stream
        result = get_best_stream(imdb_id, source)
        
        if result.get('success'):
            # Add comprehensive CORS headers for streaming
            response = jsonify(result)
            response.headers['Access-Control-Allow-Origin'] = '*'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type,Authorization,Range,If-Range'
            response.headers['Access-Control-Allow-Methods'] = 'GET,POST,OPTIONS,HEAD'
            response.headers['Access-Control-Expose-Headers'] = 'Content-Length,Content-Range,Accept-Ranges'
            response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            response.headers['Pragma'] = 'no-cache'
            response.headers['Expires'] = '0'
            return response
        else:
            error_msg = result.get('error', 'Unknown error')
            logger.error(f"Stream fetch failed for {imdb_id}: {error_msg}")
            return jsonify({
                'success': False,
                'error': error_msg,
                'imdb_id': imdb_id,
                'source': source
            }), 404
            
    except Exception as e:
        logger.error(f"Stream API error for {imdb_id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Stream fetch failed: {str(e)}',
            'imdb_id': imdb_id
        }), 500

@app.route('/api/multiembed/<imdb_id>')
def get_multiembed_stream(imdb_id):
    """Get stream from multiembed specifically"""
    try:
        source = request.args.get('source', 'auto')
        logger.info(f"Getting multiembed stream for {imdb_id} with source: {source}")
        
        result = get_m3u8_from_multiembed(imdb_id, source)
        
        if result.get('success'):
            response = jsonify(result)
            response.headers['Access-Control-Allow-Origin'] = '*'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type,Authorization,Range,If-Range'
            response.headers['Access-Control-Allow-Methods'] = 'GET,POST,OPTIONS,HEAD'
            response.headers['Access-Control-Expose-Headers'] = 'Content-Length,Content-Range,Accept-Ranges'
            return response
        else:
            return jsonify(result), 404
            
    except Exception as e:
        logger.error(f"Multiembed API error: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Multiembed fetch failed: {str(e)}'
        }), 500

@app.route('/api/test-stream')
def test_stream():
    """Test streaming with multiple known working movies"""
    test_movies = [
        {"imdb_id": "tt0111161", "title": "The Shawshank Redemption"},
        {"imdb_id": "tt0068646", "title": "The Godfather"},
        {"imdb_id": "tt0468569", "title": "The Dark Knight"},
        {"imdb_id": "tt0108052", "title": "Schindler's List"},
        {"imdb_id": "tt0167260", "title": "The Lord of the Rings: The Return of the King"}
    ]
    
    results = []
    for movie in test_movies:
        try:
            result = get_best_stream(movie["imdb_id"], 'auto')
            results.append({
                "movie": movie["title"],
                "imdb_id": movie["imdb_id"],
                "result": result
            })
        except Exception as e:
            results.append({
                "movie": movie["title"],
                "imdb_id": movie["imdb_id"],
                "result": {"success": False, "error": str(e)}
            })
    
    return jsonify({"test_results": results})

@app.route('/api/proxy')
def proxy_stream():
    """Proxy streaming URLs to handle CORS issues"""
    url = request.args.get('url')
    if not url:
        return jsonify({'error': 'No URL provided'}), 400
    
    try:
        import requests
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'https://multiembed.mov/',
            'Origin': 'https://multiembed.mov'
        }
        
        # Handle range requests for video streaming
        if 'Range' in request.headers:
            headers['Range'] = request.headers['Range']
        
        response = requests.get(url, headers=headers, stream=True, timeout=30)
        
        def generate():
            for chunk in response.iter_content(chunk_size=8192):
                yield chunk
        
        # Create response with proper headers
        resp = Response(generate(), content_type=response.headers.get('content-type', 'application/octet-stream'))
        resp.headers['Access-Control-Allow-Origin'] = '*'
        resp.headers['Access-Control-Allow-Headers'] = 'Range'
        resp.headers['Access-Control-Expose-Headers'] = 'Content-Length,Content-Range,Accept-Ranges'
        
        if 'content-length' in response.headers:
            resp.headers['Content-Length'] = response.headers['content-length']
        if 'content-range' in response.headers:
            resp.headers['Content-Range'] = response.headers['content-range']
        if 'accept-ranges' in response.headers:
            resp.headers['Accept-Ranges'] = response.headers['accept-ranges']
        
        return resp
        
    except Exception as e:
        logger.error(f"Proxy error: {str(e)}")
        return jsonify({'error': f'Proxy failed: {str(e)}'}), 500

@app.errorhandler(404)
def not_found(error):
    if request.path.startswith('/api/'):
        return jsonify({'error': 'API endpoint not found'}), 404
    return render_template('index.html'), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {str(error)}")
    if request.path.startswith('/api/'):
        return jsonify({'error': 'Internal server error'}), 500
    return render_template('index.html'), 500

# Handle CORS preflight requests
@app.before_request
def handle_preflight():
    if request.method == "OPTIONS":
        response = Response()
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET,POST,OPTIONS,HEAD'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type,Authorization,Range,If-Range'
        response.headers['Access-Control-Max-Age'] = '86400'
        return response

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
