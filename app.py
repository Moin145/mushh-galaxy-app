import os
import logging
from flask import Flask, render_template, request, jsonify, redirect, url_for
import requests
import json
from flask_cors import CORS

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "netmirror-secret-key-2025")

# Enable CORS for all domains with necessary headers and methods
CORS(app,
     origins=["*"],
     methods=["GET", "POST", "OPTIONS", "HEAD"],
     allow_headers=["Content-Type", "Authorization", "X-Requested-With", "Range", "If-Range"],
     expose_headers=["Content-Length", "Content-Range", "Accept-Ranges"])

# ---------- Corrected Imports from your api folder ------------

from api.omdb_fetcher import search_movies_by_keyword, get_movie_details
from api.stream_fetcher import get_m3u8_from_multiembed as get_stream_sources

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
        logger.error(f"Search error: {e}")
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
        logger.error(f"Movie details error: {e}")
        return jsonify({'error': 'Failed to fetch movie details'}), 500

@app.route('/watch/<imdb_id>')
def watch(imdb_id):
    """Video player page"""
    return render_template('watch.html', imdb_id=imdb_id)

@app.route('/api/stream/<imdb_id>')
def get_stream(imdb_id):
    """
    Get streaming URL for movie with enhanced error handling and CORS headers.
    Uses your improved, concurrent, cached backend.
    """
    try:
        source = request.args.get('source', 'auto')
        logger.info(f"Getting stream for {imdb_id} with source: {source}")

        # Call the main fallback streaming aggregator
        stream_data = get_stream_sources(imdb_id, source)

        logger.debug(f"Stream fetch result: {stream_data}")

        # Check if a valid stream_url or success key is present
        success = stream_data.get('stream_url') or stream_data.get('success', False)
        if success:
            response = jsonify({'success': True, **stream_data})
            response.headers['Access-Control-Allow-Origin'] = '*'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type,Authorization,Range,If-Range'
            response.headers['Access-Control-Allow-Methods'] = 'GET,POST,OPTIONS,HEAD'
            response.headers['Access-Control-Expose-Headers'] = 'Content-Length,Content-Range,Accept-Ranges'
            response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            response.headers['Pragma'] = 'no-cache'
            response.headers['Expires'] = '0'
            return response
        else:
            error_msg = stream_data.get('error', 'Unknown error')
            logger.error(f"Stream fetch failed for {imdb_id}: {error_msg}")
            return jsonify({
                'success': False,
                'error': error_msg,
                'imdb_id': imdb_id,
                'source': source,
                'debug': stream_data
            }), 404

    except Exception as e:
        logger.exception(f"Stream API error for {imdb_id}: {e}")
        return jsonify({
            'success': False,
            'error': f'Stream fetch failed: {str(e)}',
            'imdb_id': imdb_id
        }), 500

# If you have get_m3u8_from_multiembed implemented:
# @app.route('/api/multiembed/<imdb_id>')
# def get_multiembed_stream(imdb_id):
#     try:
#         source = request.args.get('source', 'auto')
#         logger.info(f"Getting multiembed stream for {imdb_id} with source: {source}")
#         result = get_m3u8_from_multiembed(imdb_id, source)
#         if result.get('success'):
#             response = jsonify(result)
#             response.headers['Access-Control-Allow-Origin'] = '*'
#             response.headers['Access-Control-Allow-Headers'] = 'Content-Type,Authorization,Range,If-Range'
#             response.headers['Access-Control-Allow-Methods'] = 'GET,POST,OPTIONS,HEAD'
#             response.headers['Access-Control-Expose-Headers'] = 'Content-Length,Content-Range,Accept-Ranges'
#             return response
#         else:
#             logger.error(f"Multiembed API failed for {imdb_id}")
#             return jsonify(result), 404
#     except Exception as e:
#         logger.error(f"Multiembed API error: {e}")
#         return jsonify({'success': False, 'error': f'Multiembed fetch failed: {str(e)}'}), 500

@app.route('/api/test-stream')
def test_stream():
    """Test streaming on well-known movies"""
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
            result = get_stream_sources(movie["imdb_id"], 'auto') # Assuming 'auto' for testing
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
    """
    Robust proxy to stream video files/segments to the browser.
    - Handles Range requests (seeking, partial loads)
    - Adds all relevant CORS headers
    - Can also restrict allowed upstream domains if needed
    """
    url = request.args.get('url')
    if not url:
        return jsonify({'error': 'No URL provided'}), 400

    # (Optional) Restrict allowed proxied hosts
    ALLOWED_HOSTS = [
        "vidsrc.me", "multiembed.to", "multiembed.mov", "flixhq.to", "tplayer.info",
        "allmovieshub.se", "dood", "streamwish", "mixdrop", "vidcloud", "streamtape"
    ]
    try:
        parsed = requests.utils.urlparse(url)
        if not any(host in parsed.netloc for host in ALLOWED_HOSTS):
            return jsonify({'error': 'Domain not allowed'}), 403

        # Prepare headers
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                          '(KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36',
            # Use a referer/origin commonly accepted for embeds
            'Referer': 'https://multiembed.mov/',
            'Origin': 'https://multiembed.mov'
        }
        if 'Range' in request.headers:
            headers['Range'] = request.headers['Range']

        upstream = requests.get(
            url,
            headers=headers,
            stream=True,
            timeout=15,  # Conservative timeout
            allow_redirects=True
        )
        def generate():
            for chunk in upstream.iter_content(chunk_size=8192):
                yield chunk

        # Build the response with relevant headers
        resp = Response(
            generate(),
            status=upstream.status_code,
            content_type=upstream.headers.get('Content-Type', 'application/octet-stream')
        )
        # Pass downstream headers required for streaming
        for h in ["Content-Length", "Content-Range", "Accept-Ranges", "Content-Disposition"]:
            if h in upstream.headers:
                resp.headers[h] = upstream.headers[h]

        # CORS for every stream chunk
        resp.headers['Access-Control-Allow-Origin'] = '*'
        resp.headers['Access-Control-Allow-Headers'] = 'Content-Type,Range,Origin,Authorization,If-Range'
        resp.headers['Access-Control-Expose-Headers'] = 'Content-Length,Content-Range,Accept-Ranges'
        resp.headers['Access-Control-Allow-Methods'] = 'GET,POST,OPTIONS,HEAD'
        # Browser caching controls
        resp.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        resp.headers['Pragma'] = 'no-cache'
        resp.headers['Expires'] = '0'

        return resp

    except requests.exceptions.RequestException as e:
        logger.error(f"[Proxy] Upstream error: {e!r}")
        return jsonify({'error': 'Upstream error', 'details': str(e)}), 502
    except Exception as e:
        logger.error(f"[Proxy] Fatal proxy error: {e!r}")
        return jsonify({'error': f'Proxy failed: {str(e)}'}), 500

@app.route('/api/report-broken-source', methods=['POST'])
def report_broken_source():
    """
    Accepts POST JSON:
    { "imdb_id": "...", "source": "...", "client_ip": "...", "user_agent": "...", "note": "..." }
    Appends info to a log file for later analysis/deprioritization.
    """
    import json
    from datetime import datetime

    data = request.get_json(force=True)
    imdb_id = data.get('imdb_id')
    source = data.get('source')
    note = data.get('note', '')
    client_ip = request.remote_addr
    user_agent = request.headers.get('User-Agent', '')

    report_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "imdb_id": imdb_id,
        "source": source,
        "client_ip": client_ip,
        "user_agent": user_agent,
        "note": note
    }

    # Append to a simple log for now
    try:
        with open('broken_sources.log', 'a', encoding='utf-8') as logf:
            logf.write(json.dumps(report_entry) + "\n")
        return jsonify({"success": True, "message": "Report received. Thank you!"})
    except Exception as e:
        logger.error(f"Failed to log broken source report: {str(e)}")
        return jsonify({"success": False, "error": "Failed to record report."}), 500

@app.route('/health')
def health_check():
    """Basic health check"""
    return jsonify({'status': 'ok'})

# Custom error handlers

@app.errorhandler(404)
def not_found(error):
    if request.path.startswith('/api/'):
        return jsonify({'error': 'API endpoint not found'}), 404
    return render_template('index.html'), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {error}")
    if request.path.startswith('/api/'):
        return jsonify({'error': 'Internal server error'}), 500
    return render_template('index.html'), 500

# Handle CORS preflight requests globally
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
    # Use environment variables for production
    import os
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    
    app.run(host='0.0.0.0', port=port, debug=debug)
