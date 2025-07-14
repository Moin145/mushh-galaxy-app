# NetMirror - Movie Streaming Web Application

## Overview

NetMirror is a Flask-based movie streaming web application that allows users to search for movies and stream them directly in their browser. The application aggregates streaming links from multiple sources and provides a Netflix-like interface for discovering and watching movies.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Frontend Architecture
- **Template Engine**: Jinja2 with Flask for server-side rendering
- **CSS Framework**: Bootstrap 5 for responsive design with custom dark theme
- **JavaScript**: Vanilla JavaScript with HLS.js for video streaming
- **Video Player**: HTML5 video element with adaptive streaming support for M3U8 files
- **UI Design**: Netflix-inspired dark theme with card-based movie browsing

### Backend Architecture
- **Framework**: Flask web framework with Python 3.x
- **CORS**: Flask-CORS enabled for cross-origin video streaming requests
- **Session Management**: Flask sessions with configurable secret key
- **Logging**: Python logging module configured for debugging
- **Request Handling**: RESTful API endpoints for movie search and streaming

### Browser Automation
- **Playwright**: Headless browser automation for JavaScript-heavy streaming sites
- **Persistent Browser**: Global browser instance for performance optimization
- **Dynamic Content**: Real-time extraction of streaming URLs from embedded players

## Key Components

### Core API Modules
1. **stream_fetcher.py**: Primary streaming logic with Playwright automation
2. **auto_stream_scraper.py**: Intelligent source selection with fallback mechanisms
3. **omdb_fetcher.py**: Movie metadata retrieval from OMDb API with multiple API keys
4. **vidsrc_api.py**: VidSrc streaming source integration
5. **mixdrop_scraper.py**: MixDrop video source extraction
6. **m3u8_scraper.py**: Generic M3U8 stream extraction using browser automation

### Data Models
- **Movie**: Dataclass for movie metadata (title, year, IMDb ID, poster, etc.)
- **StreamResult**: Dataclass for streaming results with success status and URLs
- **StreamSource**: Dataclass for individual streaming sources with quality info
- **PlayerState**: Dataclass for video player state management

### Web Interface
- **Main Routes**: Home page, movie search, streaming endpoints
- **Templates**: HTML templates for homepage and video player
- **Static Assets**: CSS styling and JavaScript for frontend functionality
- **Advanced Player**: Multi-source video player with HLS support

## Data Flow

1. **Movie Search**: User searches → OMDb API → Movie metadata returned
2. **Stream Request**: User selects movie → Multiple streaming sources checked
3. **Source Aggregation**: Auto-scraper tries sources in priority order
4. **Stream Extraction**: Playwright extracts M3U8 URLs from embed pages
5. **Video Playback**: HLS.js handles adaptive streaming in browser

## External Dependencies

### APIs and Services
- **OMDb API**: Movie metadata, posters, ratings (multiple API keys for redundancy)
- **Streaming Sources**: MultiEmbed, VidSrc, MixDrop, StreamWish, DoodStream
- **CDN Services**: Bootstrap 5, Font Awesome, HLS.js from CDN

### Python Packages
- **Flask**: Web framework and template engine
- **Flask-CORS**: Cross-origin resource sharing
- **Playwright**: Browser automation for dynamic content
- **Requests**: HTTP client for API calls
- **BeautifulSoup**: HTML parsing for web scraping
- **Dataclasses**: Type-safe data structures

### Frontend Libraries
- **Bootstrap 5**: Responsive UI framework
- **HLS.js**: HTTP Live Streaming support
- **Font Awesome**: Icon library

## Deployment Strategy

### Development Setup
- **Entry Point**: `main.py` launches Flask development server
- **Host Configuration**: Binds to 0.0.0.0:5000 for container compatibility
- **Debug Mode**: Enabled for development with detailed error logging

### Environment Configuration
- **Session Secret**: Configurable via `SESSION_SECRET` environment variable
- **OMDb API Keys**: Multiple keys via `OMDB_API_KEY` with built-in fallbacks
- **CORS Settings**: Wildcard origins enabled for video streaming

### Performance Optimizations
- **Persistent Browser**: Global Playwright instance reduces startup overhead
- **Source Prioritization**: Intelligent fallback order based on reliability
- **Caching Strategy**: Browser automation results cached for session
- **Error Handling**: Comprehensive error handling with retry mechanisms

### Security Considerations
- **CORS Policy**: Configured for video streaming while maintaining security
- **Input Sanitization**: Movie search queries sanitized
- **Rate Limiting**: Implicit rate limiting through source rotation
- **Session Management**: Secure session handling with configurable keys

The application is designed to be easily deployable on platforms like Replit, with all dependencies managed through standard Python packaging and no database requirements.