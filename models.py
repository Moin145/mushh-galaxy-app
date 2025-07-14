from dataclasses import dataclass
from typing import Optional, List, Dict, Any

@dataclass
class Movie:
    title: str
    year: str
    imdb_id: str
    poster: Optional[str] = None
    plot: Optional[str] = None
    genre: Optional[str] = None
    director: Optional[str] = None
    actors: Optional[str] = None
    rating: Optional[str] = None
    runtime: Optional[str] = None
    country: Optional[str] = None
    language: Optional[str] = None
    awards: Optional[str] = None
    metascore: Optional[str] = None
    box_office: Optional[str] = None

@dataclass
class StreamResult:
    success: bool
    url: Optional[str] = None
    source: Optional[str] = None
    error: Optional[str] = None
    quality: Optional[str] = None
    stream_type: Optional[str] = None  # 'hls', 'mp4', 'iframe'
    backup_urls: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class StreamSource:
    name: str
    url: str
    quality: Optional[str] = None
    stream_type: str = 'iframe'  # 'hls', 'mp4', 'iframe'
    priority: int = 1  # Lower number = higher priority
    working: bool = True
    
@dataclass
class PlayerState:
    current_source: Optional[StreamSource] = None
    available_sources: List[StreamSource] = None
    current_time: float = 0.0
    duration: float = 0.0
    volume: float = 1.0
    muted: bool = False
    fullscreen: bool = False
    quality: str = 'auto'
    error: Optional[str] = None
