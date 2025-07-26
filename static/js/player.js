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
      this.availableSources = ['auto', 'vidsrc', 'mixdrop', 'streamwish', 'doodstream', 'streamtape', 'vidcloud'];
  
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
  
      // Quality selector dropdown
      this.qualitySelect = document.getElementById('quality-select');
      if (this.qualitySelect) {
        this.qualitySelect.addEventListener('change', (e) => {
          this.onQualityChange(e.target.value);
        });
      }
  
      this._iframeLoadTimeoutId = null;
  
      this.initializePlayer();
    }
  
    async initializePlayer() {
      console.log(`Initializing NetMirror Player for IMDb ID: ${this.imdbId}`);
      await this.loadMovieInfo();
      this.setupSourceButtons();
      try {
        await this.loadStream('auto');
      } catch (e) {
        console.error('Error during player initialization:', e);
      }
    }
  
    async loadMovieInfo() {
      // (same as before)
      // ... You can keep your existing implementation here unchanged ...
      try {
        const response = await fetch(`/movie/${this.imdbId}`);
        const data = await response.json();
        if (data.movie) {
          const movie = data.movie;
          if (this.movieTitle) this.movieTitle.textContent = movie.Title || movie.title || 'Unknown Title';
          if (this.movieYear) this.movieYear.textContent = movie.Year || movie.year || 'Unknown';
          if (this.movieRating) this.movieRating.textContent = movie.imdbRating || movie.rating || 'N/A';
          if (this.movieRuntime) this.movieRuntime.textContent = movie.Runtime || movie.runtime || 'N/A';
          if (this.moviePlot) this.moviePlot.textContent = movie.Plot || movie.plot || 'No plot available';
          if (this.movieDirector) this.movieDirector.textContent = movie.Director || movie.director || 'Unknown';
          if (this.movieGenre) this.movieGenre.textContent = movie.Genre || movie.genre || 'Unknown';
          if (this.movieActors) this.movieActors.textContent = movie.Actors || movie.actors || 'Unknown';
          if (this.moviePoster && movie.poster) {
            this.moviePoster.src = movie.poster;
            this.moviePoster.alt = movie.title || movie.Title;
          }
          document.title = `Watch ${movie.Title || movie.title} - NetMirror`;
        } else {
          if (this.movieTitle) this.movieTitle.textContent = 'Movie Information Unavailable';
        }
      } catch (error) {
        if (this.movieTitle) this.movieTitle.textContent = 'Error Loading Movie Info';
      }
    }
  
    setupSourceButtons() {
      // (same as before)
      const sourceButtons = document.querySelectorAll('.source-btn');
      sourceButtons.forEach(button => {
        button.addEventListener('click', e => {
          e.preventDefault();
          const onclickAttr = button.getAttribute('onclick');
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
        console.log('loadStream called with source:', source);
        this.currentSource = source;
        this.retryCount = 0;
        // Update UI
        this.showLoading();
        this.hideError();
        this.hidePlayer();
        this.updateSourceButtons(source);
        this.updateDebugInfo(source, 'Loading...', 'Loading...');
        try {
            console.log('About to fetch stream from API...');
            // Fetch stream from API
            const response = await fetch(`/api/stream/${this.imdbId}?source=${source}`);
            if (!response.ok) {
                throw new Error(`API error: ${response.status}`);
            }
            const data = await response.json();
            console.log('Stream API data:', data);

            if (data.success && data.stream_url) {
                this.currentStreamUrl = data.stream_url;
                this.currentStreamType = this.determineStreamType(this.currentStreamUrl);
                this.updateDebugInfo(source, this.currentStreamUrl, this.currentStreamType);

                if (data.embed === true || this.currentStreamType === 'iframe') {
                    await this.loadIframePlayer(this.currentStreamUrl);
                } else if (this.currentStreamType === 'hls') {
                    await this.loadHLSPlayer();
                } else if (this.currentStreamType === 'mp4') {
                    await this.loadMP4Player();
                } else {
                    await this.loadIframePlayer();
                }
            } else {
                let userMessage = data.error || 'No playable stream found.';
                this.showError(userMessage + ' Trying different source...');
                await this.tryDifferentSource();
            }
        } catch (error) {
            console.error('Stream loading error:', error);
            this.showError('Failed to load stream. ' + (error.message || 'Please try again.'));
        } finally {
            this.hideLoading();
        }
    }
  
    determineStreamType(url) {
      if (!url) return 'unknown';
      const lowerUrl = url.toLowerCase();
      if (lowerUrl.includes('.m3u8')) return 'hls';
      if (lowerUrl.includes('.mp4')) return 'mp4';
      if (lowerUrl.includes('embed') || lowerUrl.includes('player')) return 'iframe';
      return 'iframe';
    }
  
    async loadIframePlayer(embedUrl) {
      if (!this.iframePlayer) return;

      this.showLoading();

      // Use proxy to avoid CORS issues
      const proxiedUrl = `/api/proxy?url=${encodeURIComponent(embedUrl)}`;

      this.iframePlayer.src = proxiedUrl;
      this.iframePlayer.style.display = 'block';

      this.videoPlayer.style.display = 'none'; // hide native video if any
      this.showIframe();

      let iframeLoaded = false;
      const timeout = setTimeout(() => {
        if (!iframeLoaded) {
          this.showError('Embed failed to load, trying next source...');
          this.tryDifferentSource();
        }
      }, 15000); // 15 seconds timeout

      this.iframePlayer.onload = () => {
        iframeLoaded = true;
        clearTimeout(timeout);
        this.hideLoading();
      };

      this.iframePlayer.onerror = () => {
        iframeLoaded = true;
        clearTimeout(timeout);
        this.showError('Embed failed to load, trying next source...');
        this.tryDifferentSource();
      };
    }
  
    async loadHLSPlayer() {
      this.clearVideoPlayerEvents();
      this.destroyHls();
  
      try {
        const video = this.videoPlayer;
        video.autoplay = true;
        video.style.display = 'block';
        this.showPlayer();
  
        if (Hls.isSupported()) {
          this.hls = new Hls();
  
          // Optional headers
          this.hls.config.xhrSetup = (xhr) => {
            xhr.setRequestHeader('Referer', 'https://multiembed.mov/');
            xhr.setRequestHeader('Origin', 'https://multiembed.mov');
          };
  
          this.hls.loadSource(this.currentStreamUrl);
          this.hls.attachMedia(video);
  
          this.hls.on(Hls.Events.MANIFEST_PARSED, () => {
            video.play();
            this.populateQualityLevels();
          });
  
          this.hls.on(Hls.Events.ERROR, (event, data) => {
            if (data.fatal) {
              this.showError('Video playback error. Trying a different source...');
              this.tryDifferentSource();
            }
          });
        } else if (video.canPlayType('application/vnd.apple.mpegurl')) {
          video.src = this.currentStreamUrl;
          video.play();
          this.showPlayer();
        } else {
          this.showError('HLS not supported.');
        }
      } catch (error) {
        this.showError('Failed to load HLS player');
        await this.tryDifferentSource();
      }
    }
  
    async loadMP4Player() {
      this.clearVideoPlayerEvents();
      this.destroyHls();
  
      try {
        const video = this.videoPlayer;
        video.src = this.currentStreamUrl;
        video.style.display = 'block';
        this.showPlayer();
        video.load();
        video.play();
      } catch (error) {
        this.showError('Failed to load MP4 player');
        await this.tryDifferentSource();
      }
    }
  
    // Manage quality selector options for HLS streams
    populateQualityLevels() {
      if (!this.hls || !this.qualitySelect) return;
  
      let levels = this.hls.levels;
      if (!levels || levels.length === 0) {
        this.qualitySelect.innerHTML = '<option value="auto" selected>Auto</option>';
        this.qualitySelect.disabled = true;
        return;
      }
  
      this.qualitySelect.innerHTML = '';
  
      // Add Auto option
      const autoOption = document.createElement('option');
      autoOption.value = 'auto';
      autoOption.textContent = 'Auto';
      autoOption.selected = true;
      this.qualitySelect.appendChild(autoOption);
  
      // Add each quality option sorted by resolution descending
      levels
        .sort((a, b) => b.height - a.height)
        .forEach((level, index) => {
          const label = level.height ? `${level.height}p` : `Level ${index}`;
          const option = document.createElement('option');
          option.value = index;
          option.textContent = label;
          this.qualitySelect.appendChild(option);
        });
  
      this.qualitySelect.disabled = false;
  
      // Listen to hls level change and update dropdown accordingly
      this.hls.on(Hls.Events.LEVEL_SWITCHED, (event, data) => {
        if (data.level >= 0 && data.level < this.qualitySelect.options.length) {
          this.qualitySelect.value = data.level.toString();
        }
      });
    }
  
    onQualityChange(value) {
      if (!this.hls) return;
  
      if (value === 'auto') {
        this.hls.currentLevel = -1;
        console.log('Quality set to Auto');
      } else {
        const levelIndex = parseInt(value, 10);
        if (!isNaN(levelIndex)) {
          this.hls.currentLevel = levelIndex;
          console.log('Quality set to level', levelIndex);
        }
      }
    }
  
    // Utilities for player UI and states
  
    clearVideoPlayerEvents() {
      if (!this.videoPlayer) return;
      this.videoPlayer.pause();
      this.videoPlayer.removeAttribute('src');
      this.videoPlayer.load();
      this.videoPlayer.onerror = null;
    }
  
    destroyHls() {
      if (this.hls) {
        this.hls.destroy();
        this.hls = null;
      }
    }
  
    showLoading() {
      if (this.playerLoading) this.playerLoading.style.display = 'flex';
    }
  
    hideLoading() {
      if (this.playerLoading) this.playerLoading.style.display = 'none';
    }
  
    showError(message) {
      if (this.playerError && this.errorMessage) {
        this.errorMessage.textContent = message;
        this.playerError.classList.remove('d-none');
      }
      this.hidePlayer();
    }
  
    hideError() {
      if (this.playerError) this.playerError.classList.add('d-none');
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
      const buttons = document.querySelectorAll('.source-btn');
      buttons.forEach(button => {
        button.classList.remove('active');
        const fnc = button.getAttribute('onclick');
        if (!fnc) return;
        const match = fnc.match(/'([^']+)'/);
        if (match && match[1] === activeSource) {
          button.classList.add('active');
        }
      });
    }
  
    updateDebugInfo(source, url, playerType) {
      if (this.debugSource) this.debugSource.textContent = source || '-';
      if (this.debugUrl) this.debugUrl.textContent = url ? (url.length > 100 ? url.substr(0, 100) + '...' : url) : '-';
      if (this.debugPlayer) this.debugPlayer.textContent = playerType || '-';
    }
  
    async retryStream() {
      if (this.retryCount < this.maxRetries) {
        this.retryCount++;
        await this.loadStream(this.currentSource);
      } else {
        await this.tryDifferentSource();
      }
    }
  
    async tryDifferentSource() {
      this.sourceIndex = (this.sourceIndex + 1) % this.availableSources.length;
      const nextSource = this.availableSources[this.sourceIndex];
      await this.loadStream(nextSource);
    }
  
    getNextSource() {
      const currentIndex = this.availableSources.indexOf(this.currentSource);
      return this.availableSources[(currentIndex + 1) % this.availableSources.length];
    }
  
    destroy() {
      this.destroyHls();
      if (this.videoPlayer) {
        this.videoPlayer.src = '';
        this.videoPlayer.load();
        this.videoPlayer.style.display = 'none';
        this.videoPlayer.classList.add('d-none');
      }
      if (this.iframePlayer) {
        this.iframePlayer.src = '';
        this.iframePlayer.style.display = 'none';
        this.iframePlayer.classList.add('d-none');
      }
      if (this.playerControls) {
        this.playerControls.classList.add('d-none');
      }
    }
  
    resetQualitySelector() {
        const qualitySelect = document.getElementById('quality-select');
        if (qualitySelect) {
            qualitySelect.value = 'auto';
            // Optionally, remove other options or reset UI here if needed
        }
    }
  }
  
  // Global player instance
  let netMirrorPlayer = null;
  
  // Initialization and global helpers
  function initializePlayer(imdbId) {
    if (netMirrorPlayer) {
      netMirrorPlayer.destroy();
    }
    netMirrorPlayer = new NetMirrorPlayer(imdbId);
  }
  
  function loadStream(source) {
    if (netMirrorPlayer) {
      netMirrorPlayer.loadStream(source);
    }
  }
  
  function retryStream() {
    if (netMirrorPlayer) {
      netMirrorPlayer.retryStream();
    }
  }
  
  function tryDifferentSource() {
    if (netMirrorPlayer) {
      netMirrorPlayer.tryDifferentSource();
    }
  }
  
  window.initializePlayer = initializePlayer;
  window.loadStream = loadStream;
  window.retryStream = retryStream;
  window.tryDifferentSource = tryDifferentSource;
  