// NetMirror Video Player - Advanced streaming with multiple source support
class NetMirrorPlayer {
    constructor(imdbId) {
        this.imdbId = imdbId;
        this.currentSource = 'auto';
        this.currentStreamUrl = null;
        this.currentStreamType = null;
        this.hls = null;
        this.retryCount = 0;
        this.maxRetries = 3;
        this.sourceIndex = 0;
        this.availableSources = ['auto', 'vidsrc', 'mixdrop', 'streamwish', 'doodstream'];
        
        // DOM elements
        this.playerLoading = document.getElementById('player-loading');
        this.playerError = document.getElementById('player-error');
        this.videoPlayer = document.getElementById('video-player');
        this.iframePlayer = document.getElementById('iframe-player');
        this.playerControls = document.getElementById('player-controls');
        this.errorMessage = document.getElementById('error-message');
        
        // Movie info elements
        this.movieTitle = document.getElementById('movie-title');
        this.movieYear = document.getElementById('movie-year');
        this.movieRating = document.getElementById('movie-rating');
        this.movieRuntime = document.getElementById('movie-runtime');
        this.moviePlot = document.getElementById('movie-plot');
        this.movieDirector = document.getElementById('movie-director');
        this.movieGenre = document.getElementById('movie-genre');
        this.movieActors = document.getElementById('movie-actors');
        this.moviePoster = document.getElementById('movie-poster-img');
        
        // Debug elements
        this.debugSource = document.getElementById('debug-source');
        this.debugUrl = document.getElementById('debug-url');
        this.debugPlayer = document.getElementById('debug-player');
        
        this.initializePlayer();
    }
    
    async initializePlayer() {
        console.log(`Initializing NetMirror Player for IMDb ID: ${this.imdbId}`);
        
        // Load movie information first
        await this.loadMovieInfo();
        
        // Setup source buttons
        this.setupSourceButtons();
        
        // Load stream with auto source
        await this.loadStream('auto');
    }
    
    async loadMovieInfo() {
        try {
            console.log('Loading movie information...');
            
            const response = await fetch(`/movie/${this.imdbId}`);
            const data = await response.json();
            
            if (data.movie) {
                const movie = data.movie;
                
                // Update movie info
                if (this.movieTitle) this.movieTitle.textContent = movie.title || 'Unknown Title';
                if (this.movieYear) this.movieYear.textContent = movie.year || 'Unknown';
                if (this.movieRating) this.movieRating.textContent = movie.rating || 'N/A';
                if (this.movieRuntime) this.movieRuntime.textContent = movie.runtime || 'N/A';
                if (this.moviePlot) this.moviePlot.textContent = movie.plot || 'No plot available';
                if (this.movieDirector) this.movieDirector.textContent = movie.director || 'Unknown';
                if (this.movieGenre) this.movieGenre.textContent = movie.genre || 'Unknown';
                if (this.movieActors) this.movieActors.textContent = movie.actors || 'Unknown';
                
                // Update poster
                if (this.moviePoster && movie.poster && movie.poster !== 'N/A') {
                    this.moviePoster.src = movie.poster;
                    this.moviePoster.alt = movie.title;
                }
                
                // Update page title
                document.title = `Watch ${movie.title} - NetMirror`;
                
                console.log('Movie information loaded successfully');
            } else {
                console.warn('No movie data received');
                if (this.movieTitle) this.movieTitle.textContent = 'Movie Information Unavailable';
            }
        } catch (error) {
            console.error('Error loading movie info:', error);
            if (this.movieTitle) this.movieTitle.textContent = 'Error Loading Movie Info';
        }
    }
    
    setupSourceButtons() {
        const sourceButtons = document.querySelectorAll('.source-btn');
        sourceButtons.forEach(button => {
            button.addEventListener('click', (e) => {
                e.preventDefault();
                const onclickAttr = e.target.getAttribute('onclick');
                if (onclickAttr) {
                    const match = onclickAttr.match(/'([^']+)'/);
                    if (match && match[1]) {
                        this.loadStream(match[1]);
                    }
                }
            });
        });
    }
    
    async loadStream(source = 'auto') {
        console.log(`Loading stream with source: ${source}`);
        
        this.currentSource = source;
        this.retryCount = 0;
        
        // Update UI
        this.showLoading();
        this.hideError();
        this.hidePlayer();
        this.updateSourceButtons(source);
        this.updateDebugInfo(source, 'Loading...', 'Loading...');
        
        try {
            // Fetch stream from API
            const response = await fetch(`/api/stream/${this.imdbId}?source=${source}`);
            const data = await response.json();
            
            if (data.success && data.m3u8) {
                console.log('Stream data received:', data);
                
                this.currentStreamUrl = data.m3u8;
                this.currentStreamType = data.stream_type || this.determineStreamType(data.m3u8);
                
                this.updateDebugInfo(source, this.currentStreamUrl, this.currentStreamType);
                
                // Load the appropriate player
                if (this.currentStreamType === 'hls') {
                    await this.loadHLSPlayer();
                } else if (this.currentStreamType === 'mp4') {
                    await this.loadMP4Player();
                } else {
                    await this.loadIframePlayer();
                }
                
            } else {
                console.error('Stream loading failed:', data.error);
                this.showError(data.error || 'Stream not available');
            }
            
        } catch (error) {
            console.error('Stream loading error:', error);
            this.showError('Failed to load stream. Please try again.');
        } finally {
            this.hideLoading();
        }
    }
    
    determineStreamType(url) {
        if (!url) return 'unknown';
        
        const urlLower = url.toLowerCase();
        
        if (urlLower.includes('.m3u8')) {
            return 'hls';
        } else if (urlLower.includes('.mp4')) {
            return 'mp4';
        } else if (urlLower.includes('embed') || urlLower.includes('player')) {
            return 'iframe';
        } else {
            return 'iframe'; // Default to iframe for unknown types
        }
    }
    
    async loadHLSPlayer() {
        console.log('Loading HLS player...');
        
        try {
            // Cleanup existing HLS instance
            if (this.hls) {
                this.hls.destroy();
                this.hls = null;
            }
            
            const video = this.videoPlayer;
            
            if (Hls.isSupported()) {
                // Use HLS.js for browsers that support it
                this.hls = new Hls({
                    enableWorker: true,
                    lowLatencyMode: false,
                    backBufferLength: 90,
                    maxBufferLength: 30,
                    maxMaxBufferLength: 60,
                    startLevel: -1, // Auto quality
                    capLevelToPlayerSize: true,
                    debug: false,
                    xhrSetup: (xhr, url) => {
                        xhr.setRequestHeader('Referer', 'https://multiembed.mov/');
                        xhr.setRequestHeader('Origin', 'https://multiembed.mov');
                    }
                });
                
                this.hls.loadSource(this.currentStreamUrl);
                this.hls.attachMedia(video);
                
                this.hls.on(Hls.Events.MANIFEST_PARSED, () => {
                    console.log('HLS manifest parsed successfully');
                    this.showPlayer();
                    this.setupVideoEvents();
                });
                
                this.hls.on(Hls.Events.ERROR, (event, data) => {
                    console.error('HLS error:', data);
                    
                    if (data.fatal) {
                        switch (data.type) {
                            case Hls.ErrorTypes.NETWORK_ERROR:
                                console.log('Network error, trying to recover...');
                                this.hls.startLoad();
                                break;
                            case Hls.ErrorTypes.MEDIA_ERROR:
                                console.log('Media error, trying to recover...');
                                this.hls.recoverMediaError();
                                break;
                            default:
                                console.error('Fatal error, cannot recover');
                                this.showError('Video playback failed. Please try a different source.');
                                break;
                        }
                    }
                });
                
            } else if (video.canPlayType('application/vnd.apple.mpegurl')) {
                // Native HLS support (Safari)
                console.log('Using native HLS support');
                video.src = this.currentStreamUrl;
                this.showPlayer();
                this.setupVideoEvents();
                
            } else {
                console.error('HLS not supported');
                this.showError('HLS playback not supported in this browser');
            }
            
        } catch (error) {
            console.error('HLS player error:', error);
            this.showError('Failed to load HLS player');
        }
    }
    
    async loadMP4Player() {
        console.log('Loading MP4 player...');
        
        try {
            const video = this.videoPlayer;
            video.src = this.currentStreamUrl;
            
            this.showPlayer();
            this.setupVideoEvents();
            
        } catch (error) {
            console.error('MP4 player error:', error);
            this.showError('Failed to load MP4 player');
        }
    }
    
    async loadIframePlayer() {
        console.log('Loading iframe player...');
        
        try {
            const iframe = this.iframePlayer;
            
            // Set iframe source
            iframe.src = this.currentStreamUrl;
            iframe.style.display = 'block';
            
            this.showIframe();
            
            // Setup iframe load event
            iframe.onload = () => {
                console.log('Iframe loaded successfully');
            };
            
            iframe.onerror = () => {
                console.error('Iframe failed to load');
                this.showError('Failed to load video player');
            };
            
        } catch (error) {
            console.error('Iframe player error:', error);
            this.showError('Failed to load iframe player');
        }
    }
    
    setupVideoEvents() {
        const video = this.videoPlayer;
        
        // Basic video events
        video.addEventListener('loadstart', () => {
            console.log('Video loading started');
        });
        
        video.addEventListener('canplay', () => {
            console.log('Video can start playing');
        });
        
        video.addEventListener('error', (e) => {
            console.error('Video error:', e);
            this.showError('Video playback error. Please try a different source.');
        });
        
        video.addEventListener('ended', () => {
            console.log('Video playback ended');
        });
        
        // Setup custom controls if needed
        this.setupCustomControls();
    }
    
    setupCustomControls() {
        const video = this.videoPlayer;
        const playPauseBtn = document.getElementById('play-pause-btn');
        const volumeBtn = document.getElementById('volume-btn');
        const volumeSlider = document.getElementById('volume-slider');
        const fullscreenBtn = document.getElementById('fullscreen-btn');
        const currentTimeEl = document.getElementById('current-time');
        const durationEl = document.getElementById('duration');
        
        // Play/Pause button
        if (playPauseBtn) {
            playPauseBtn.addEventListener('click', () => {
                if (video.paused) {
                    video.play();
                    playPauseBtn.innerHTML = '<i class="fas fa-pause"></i>';
                } else {
                    video.pause();
                    playPauseBtn.innerHTML = '<i class="fas fa-play"></i>';
                }
            });
        }
        
        // Volume controls
        if (volumeBtn && volumeSlider) {
            volumeBtn.addEventListener('click', () => {
                video.muted = !video.muted;
                volumeBtn.innerHTML = video.muted 
                    ? '<i class="fas fa-volume-mute"></i>'
                    : '<i class="fas fa-volume-up"></i>';
            });
            
            volumeSlider.addEventListener('input', (e) => {
                video.volume = e.target.value;
                video.muted = e.target.value == 0;
            });
        }
        
        // Fullscreen button
        if (fullscreenBtn) {
            fullscreenBtn.addEventListener('click', () => {
                if (video.requestFullscreen) {
                    video.requestFullscreen();
                } else if (video.webkitRequestFullscreen) {
                    video.webkitRequestFullscreen();
                } else if (video.msRequestFullscreen) {
                    video.msRequestFullscreen();
                }
            });
        }
        
        // Time updates
        video.addEventListener('timeupdate', () => {
            if (currentTimeEl) {
                currentTimeEl.textContent = this.formatTime(video.currentTime);
            }
        });
        
        video.addEventListener('loadedmetadata', () => {
            if (durationEl) {
                durationEl.textContent = this.formatTime(video.duration);
            }
        });
    }
    
    formatTime(seconds) {
        const hrs = Math.floor(seconds / 3600);
        const mins = Math.floor((seconds % 3600) / 60);
        const secs = Math.floor(seconds % 60);
        
        if (hrs > 0) {
            return `${hrs}:${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
        } else {
            return `${mins}:${secs.toString().padStart(2, '0')}`;
        }
    }
    
    showLoading() {
        if (this.playerLoading) {
            this.playerLoading.style.display = 'flex';
        }
    }
    
    hideLoading() {
        if (this.playerLoading) {
            this.playerLoading.style.display = 'none';
        }
    }
    
    showError(message) {
        if (this.playerError && this.errorMessage) {
            this.errorMessage.textContent = message;
            this.playerError.classList.remove('d-none');
        }
    }
    
    hideError() {
        if (this.playerError) {
            this.playerError.classList.add('d-none');
        }
    }
    
    showPlayer() {
        if (this.videoPlayer) {
            this.videoPlayer.classList.remove('d-none');
            this.videoPlayer.style.display = 'block';
        }
        if (this.iframePlayer) {
            this.iframePlayer.style.display = 'none';
        }
        if (this.playerControls) {
            this.playerControls.classList.remove('d-none');
        }
    }
    
    showIframe() {
        if (this.iframePlayer) {
            this.iframePlayer.classList.remove('d-none');
            this.iframePlayer.style.display = 'block';
        }
        if (this.videoPlayer) {
            this.videoPlayer.style.display = 'none';
        }
        if (this.playerControls) {
            this.playerControls.classList.add('d-none');
        }
    }
    
    hidePlayer() {
        if (this.videoPlayer) {
            this.videoPlayer.classList.add('d-none');
            this.videoPlayer.style.display = 'none';
        }
        if (this.iframePlayer) {
            this.iframePlayer.classList.add('d-none');
            this.iframePlayer.style.display = 'none';
        }
        if (this.playerControls) {
            this.playerControls.classList.add('d-none');
        }
    }
    
    updateSourceButtons(activeSource) {
        const sourceButtons = document.querySelectorAll('.source-btn');
        sourceButtons.forEach(button => {
            button.classList.remove('active');
            const buttonSource = button.getAttribute('onclick').match(/'([^']+)'/)[1];
            if (buttonSource === activeSource) {
                button.classList.add('active');
            }
        });
    }
    
    updateDebugInfo(source, url, playerType) {
        if (this.debugSource) this.debugSource.textContent = source;
        if (this.debugUrl) this.debugUrl.textContent = url.length > 100 ? url.substring(0, 100) + '...' : url;
        if (this.debugPlayer) this.debugPlayer.textContent = playerType;
    }
    
    async retryStream() {
        console.log('Retrying stream...');
        
        if (this.retryCount < this.maxRetries) {
            this.retryCount++;
            await this.loadStream(this.currentSource);
        } else {
            console.log('Max retries reached, trying different source');
            this.tryDifferentSource();
        }
    }
    
    async tryDifferentSource() {
        console.log('Trying different source...');
        
        // Get next source in the list
        this.sourceIndex = (this.sourceIndex + 1) % this.availableSources.length;
        const nextSource = this.availableSources[this.sourceIndex];
        
        console.log(`Switching to source: ${nextSource}`);
        await this.loadStream(nextSource);
    }
    
    getNextSource() {
        const currentIndex = this.availableSources.indexOf(this.currentSource);
        const nextIndex = (currentIndex + 1) % this.availableSources.length;
        return this.availableSources[nextIndex];
    }
    
    destroy() {
        console.log('Destroying NetMirror Player');
        
        // Cleanup HLS instance
        if (this.hls) {
            this.hls.destroy();
            this.hls = null;
        }
        
        // Reset video player
        if (this.videoPlayer) {
            this.videoPlayer.src = '';
            this.videoPlayer.load();
        }
        
        // Reset iframe player
        if (this.iframePlayer) {
            this.iframePlayer.src = '';
        }
    }
}

// Global player instance
let netMirrorPlayer = null;

// Initialize player function
function initializePlayer(imdbId) {
    console.log('Initializing NetMirror Player with IMDb ID:', imdbId);
    
    // Destroy existing player if any
    if (netMirrorPlayer) {
        netMirrorPlayer.destroy();
    }
    
    // Create new player instance
    netMirrorPlayer = new NetMirrorPlayer(imdbId);
}

// Global function to load stream with specific source
function loadStream(source) {
    if (netMirrorPlayer) {
        netMirrorPlayer.loadStream(source);
    }
}

// Global function to retry stream
function retryStream() {
    if (netMirrorPlayer) {
        netMirrorPlayer.retryStream();
    }
}

// Global function to try different source
function tryDifferentSource() {
    if (netMirrorPlayer) {
        netMirrorPlayer.tryDifferentSource();
    }
}

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
    if (netMirrorPlayer) {
        netMirrorPlayer.destroy();
    }
});

// Export for global use
window.initializePlayer = initializePlayer;
window.loadStream = loadStream;
window.retryStream = retryStream;
window.tryDifferentSource = tryDifferentSource;
