// NetMirror Main JavaScript

// Global variables
let currentQuery = '';
let isSearching = false;

// DOM Elements
const searchForm = document.getElementById('search-form');
const searchInput = document.getElementById('search-input');
const loadingIndicator = document.getElementById('loading');
const searchResults = document.getElementById('search-results');
const moviesGrid = document.getElementById('movies-grid');
const popularMovies = document.getElementById('popular-movies');

// Initialize app
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
    loadPopularMovies();
    loadContinueWatching();
});

// Initialize application
function initializeApp() {
    // Setup search form
    if (searchForm) {
        searchForm.addEventListener('submit', handleSearch);
    }
    
    // Setup search input
    if (searchInput) {
        searchInput.addEventListener('input', debounce(handleSearchInput, 300));
    }
    
    // Setup smooth scrolling
    setupSmoothScrolling();
    
    // Initialize hero rotation
    initializeHeroRotation();
    
    console.log('NetMirror app initialized');
}

// Handle search form submission
function handleSearch(e) {
    e.preventDefault();
    const query = searchInput.value.trim();
    if (query && !isSearching) {
        searchMovies(query);
    }
}

// Clear search results
function clearSearch() {
    console.log('🧹 Clearing search results');
    if (searchInput) {
        searchInput.value = '';
    }
    hideSearchResults();
    currentQuery = '';
    console.log('✅ Search cleared');
}

// Handle search input changes
function handleSearchInput(e) {
    const query = e.target.value.trim();
    console.log(`🔤 Search input changed: "${query}"`);
    
    if (query.length > 2 && query !== currentQuery) {
        console.log(`🔍 Triggering search for: "${query}"`);
        searchMovies(query);
    } else if (query.length === 0) {
        console.log('🧹 Search input cleared, hiding results');
        hideSearchResults();
    }
}

// Search movies function
async function searchMovies(query) {
    if (isSearching) return;
    
    isSearching = true;
    currentQuery = query;
    
    console.log(`🔍 Starting search for: "${query}"`);
    showLoading();
    hideSearchResults();
    
    try {
        const response = await fetch(`/search?q=${encodeURIComponent(query)}`);
        console.log(`📡 Search response status: ${response.status}`);
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();
        console.log(`📊 Search results:`, data);
        
        if (data.movies && data.movies.length > 0) {
            console.log(`✅ Found ${data.movies.length} movies`);
            // Group related movies (like Bahubali parts)
            const groupedMovies = groupRelatedMovies(data.movies, query);
            displaySearchResults(groupedMovies);
        } else {
            console.log(`❌ No movies found for: "${query}"`);
            displayNoResults(query);
        }
        
    } catch (error) {
        console.error('❌ Search error:', error);
        displayError(`Search failed: ${error.message}`);
    } finally {
        hideLoading();
        isSearching = false;
    }
}

// Group related movies (like series, franchises, parts)
function groupRelatedMovies(movies, query) {
    const queryLower = query.toLowerCase();
    const grouped = [];
    const processed = new Set();
    
    // First, look for exact matches and series
    movies.forEach(movie => {
        const title = movie.Title.toLowerCase();
        const imdbId = movie.imdbID;
        
        if (processed.has(imdbId)) return;
        
        // Check if this movie is part of a series
        if (title.includes(queryLower) || 
            title.includes('part') || 
            title.includes('chapter') ||
            title.includes('volume') ||
            title.includes('episode')) {
            
            // Find related movies
            const related = movies.filter(m => {
                const mTitle = m.Title.toLowerCase();
                return (mTitle.includes(queryLower) || 
                       mTitle.includes('part') || 
                       mTitle.includes('chapter') ||
                       mTitle.includes('volume') ||
                       mTitle.includes('episode')) &&
                       !processed.has(m.imdbID);
            });
            
            if (related.length > 1) {
                // Group related movies
                grouped.push({
                    type: 'series',
                    title: `${query.charAt(0).toUpperCase() + query.slice(1)} Series`,
                    movies: related,
                    year: related[0].Year
                });
                related.forEach(m => processed.add(m.imdbID));
            } else {
                // Single movie
                grouped.push({
                    type: 'single',
                    movie: movie
                });
                processed.add(imdbId);
            }
        } else {
            // Regular movie
            grouped.push({
                type: 'single',
                movie: movie
            });
            processed.add(imdbId);
        }
    });
    
    return grouped;
}

// Display search results
function displaySearchResults(groupedMovies) {
    console.log(`🎬 Displaying ${groupedMovies.length} grouped results`);
    
    if (!moviesGrid) {
        console.error('❌ moviesGrid element not found!');
        return;
    }
    
    moviesGrid.innerHTML = '';
    
    groupedMovies.forEach((item, index) => {
        if (item.type === 'series') {
            console.log(`🎭 Creating individual cards for series: ${item.title} with ${item.movies.length} movies`);
            // Show each movie in the series individually
            item.movies.forEach(movie => {
                const movieCard = createMovieCard(movie);
                moviesGrid.appendChild(movieCard);
            });
        } else {
            console.log(`🎭 Creating single movie card for: ${item.movie.Title} (${item.movie.Year})`);
            const movieCard = createMovieCard(item.movie);
            moviesGrid.appendChild(movieCard);
        }
    });
    
    console.log('📱 Showing search results section');
    showSearchResults();
    scrollToSection('search-results');
}

// Display no results message
function displayNoResults(query) {
    if (!moviesGrid) return;
    
    moviesGrid.innerHTML = `
        <div class="no-results">
            <div class="text-center">
                <i class="fas fa-search fa-3x text-secondary mb-3"></i>
                <h3>No Results Found</h3>
                <p class="text-secondary">No movies found for "${query}". Try different keywords.</p>
            </div>
        </div>
    `;
    
    showSearchResults();
    scrollToSection('search-results');
}

// Display error message
function displayError(message) {
    if (!moviesGrid) return;
    
    moviesGrid.innerHTML = `
        <div class="error-message">
            <div class="text-center">
                <i class="fas fa-exclamation-triangle fa-3x text-danger mb-3"></i>
                <h3>Error</h3>
                <p class="text-secondary">${message}</p>
                <button class="btn btn-primary" onclick="location.reload()">
                    <i class="fas fa-redo me-2"></i>Retry
                </button>
            </div>
        </div>
    `;
    
    showSearchResults();
}

// Create movie card element
function createMovieCard(movie) {
    const card = document.createElement('div');
    card.className = 'movie-card fade-in';
    card.onclick = () => watchMovie(movie.imdbID);
    
    // Better poster handling
    let posterHtml = '';
    if (movie.Poster && movie.Poster !== 'N/A' && movie.Poster.trim() !== '') {
        posterHtml = `<img src="${movie.Poster}" alt="${movie.Title}" loading="lazy" onerror="this.style.display='none'; this.nextElementSibling.style.display='flex';">`;
    }
    
    // Fallback icon if no poster or if poster fails to load
    const fallbackIcon = '<i class="fas fa-film" style="display: none;"></i>';
    
    card.innerHTML = `
        <div class="movie-poster">
            ${posterHtml}
            ${fallbackIcon}
        </div>
        <div class="movie-info">
            <h3 class="movie-title">${movie.Title}</h3>
            <p class="movie-year">${movie.Year}</p>
        </div>
    `;
    
    return card;
}

// Create series card element
function createSeriesCard(series) {
    const card = document.createElement('div');
    card.className = 'movie-card fade-in';
    card.onclick = () => watchMovie(series.movies[0].imdbID); // Click on the first movie in the series
    
    const posterUrl = series.movies[0].Poster && series.movies[0].Poster !== 'N/A' 
        ? series.movies[0].Poster 
        : null;
    
    card.innerHTML = `
        <div class="movie-poster">
            ${posterUrl 
                ? `<img src="${posterUrl}" alt="${series.title}" loading="lazy">` 
                : '<i class="fas fa-film"></i>'
            }
        </div>
        <div class="movie-info">
            <h3 class="movie-title">${series.title}</h3>
            <p class="movie-year">${series.year}</p>
        </div>
    `;
    
    return card;
}

// Navigate to watch page
function watchMovie(imdbId) {
    if (imdbId) {
        window.location.href = `/watch/${imdbId}`;
    }
}

// Load popular movies
async function loadPopularMovies() {
    if (!popularMovies) return;
    
    const popularTitles = [
        'The Shawshank Redemption',
        'The Godfather',
        'The Dark Knight',
        'Pulp Fiction',
        'The Lord of the Rings',
        'Forrest Gump',
        'Inception',
        'The Matrix',
        'Goodfellas',
        'The Silence of the Lambs',
        'Seven',
        'Fight Club',
        'The Lord of the Rings: The Return of the King',
        'Star Wars',
        'The Lord of the Rings: The Fellowship of the Ring'
    ];
    
    popularMovies.innerHTML = '<div class="loading-placeholder">Loading popular movies...</div>';
    
    try {
        const moviePromises = popularTitles.slice(0, 8).map(async title => {
            try {
                const response = await fetch(`/search?q=${encodeURIComponent(title)}`);
                const data = await response.json();
                return data.movies && data.movies.length > 0 ? data.movies[0] : null;
            } catch {
                return null;
            }
        });
        
        const movies = await Promise.all(moviePromises);
        const validMovies = movies.filter(movie => movie !== null);
        
        popularMovies.innerHTML = '';
        
        if (validMovies.length > 0) {
            validMovies.forEach(movie => {
                const movieCard = createMovieCard(movie);
                popularMovies.appendChild(movieCard);
            });
        } else {
            popularMovies.innerHTML = `
                <div class="no-movies">
                    <div class="text-center">
                        <i class="fas fa-film fa-3x text-secondary mb-3"></i>
                        <h3>No Movies Available</h3>
                        <p class="text-secondary">Unable to load popular movies at this time.</p>
                    </div>
                </div>
            `;
        }
        
    } catch (error) {
        console.error('Error loading popular movies:', error);
        popularMovies.innerHTML = `
            <div class="error-message">
                <div class="text-center">
                    <i class="fas fa-exclamation-triangle fa-3x text-danger mb-3"></i>
                    <h3>Loading Error</h3>
                    <p class="text-secondary">Failed to load popular movies.</p>
                </div>
            </div>
        `;
    }
}

// Show/hide loading indicator
function showLoading() {
    if (loadingIndicator) {
        loadingIndicator.classList.remove('d-none');
    }
}

function hideLoading() {
    if (loadingIndicator) {
        loadingIndicator.classList.add('d-none');
    }
}

// Show search results section
function showSearchResults() {
    console.log('👁️ Showing search results section');
    if (searchResults) {
        searchResults.classList.remove('d-none');
        searchResults.style.display = 'block';
        console.log('✅ Search results section is now visible');
    } else {
        console.error('❌ searchResults element not found!');
    }
}

// Hide search results section
function hideSearchResults() {
    console.log('🙈 Hiding search results section');
    if (searchResults) {
        searchResults.classList.add('d-none');
        searchResults.style.display = 'none';
        console.log('✅ Search results section is now hidden');
    } else {
        console.error('❌ searchResults element not found!');
    }
}

// Smooth scrolling
function setupSmoothScrolling() {
    const links = document.querySelectorAll('a[href^="#"]');
    links.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
}

// Scroll to section
function scrollToSection(sectionId) {
    const section = document.getElementById(sectionId);
    if (section) {
        section.scrollIntoView({
            behavior: 'smooth',
            block: 'start'
        });
    }
}

// Debounce function
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Utility functions
function formatTime(seconds) {
    const hrs = Math.floor(seconds / 3600);
    const mins = Math.floor((seconds % 3600) / 60);
    const secs = Math.floor(seconds % 60);
    
    if (hrs > 0) {
        return `${hrs}:${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    } else {
        return `${mins}:${secs.toString().padStart(2, '0')}`;
    }
}

function showNotification(message, type = 'info') {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
    notification.style.cssText = 'top: 20px; right: 20px; z-index: 9999; max-width: 400px;';
    notification.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(notification);
    
    // Auto dismiss after 5 seconds
    setTimeout(() => {
        if (notification.parentNode) {
            notification.parentNode.removeChild(notification);
        }
    }, 5000);
}

// Hero rotation functionality
let heroMovies = [];
let currentHeroIndex = 0;
let heroInterval = null;

function initializeHeroRotation() {
    loadHeroMovies();
}

async function loadHeroMovies() {
    try {
        const trendingMovies = [
            'Squid Game',
            'The Dark Knight',
            'Inception',
            'Avengers: Endgame',
            'Stranger Things',
            'Wednesday',
            'The Witcher',
            'Breaking Bad',
            'Game of Thrones',
            'The Matrix'
        ];
        
        heroMovies = [];
        
        for (let i = 0; i < Math.min(5, trendingMovies.length); i++) {
            try {
                const response = await fetch(`/search?q=${encodeURIComponent(trendingMovies[i])}`);
                const data = await response.json();
                if (data.movies && data.movies.length > 0) {
                    heroMovies.push(data.movies[0]);
                }
            } catch (error) {
                console.error(`Error loading hero movie ${trendingMovies[i]}:`, error);
            }
        }
        
        if (heroMovies.length > 0) {
            setupHeroRotation();
        }
    } catch (error) {
        console.error('Error loading hero movies:', error);
    }
}

function setupHeroRotation() {
    if (heroMovies.length === 0) return;
    
    // Create navigation dots
    const heroDotsContainer = document.getElementById('hero-dots');
    if (heroDotsContainer) {
        heroDotsContainer.innerHTML = '';
        heroMovies.forEach((_, index) => {
            const dot = document.createElement('span');
            dot.className = `hero-dot ${index === 0 ? 'active' : ''}`;
            dot.onclick = () => showHeroMovie(index);
            heroDotsContainer.appendChild(dot);
        });
    }
    
    // Show first movie
    showHeroMovie(0);
    
    // Start auto rotation
    startHeroRotation();
}

// Cache for Squid Game poster
let squidGamePosterUrl = null;
let squidGamePosterFetched = false;

async function showHeroMovie(index) {
    if (index >= heroMovies.length) return;
    
    const movie = heroMovies[index];
    currentHeroIndex = index;
    
    // Update hero content
    const heroTitle = document.getElementById('hero-title');
    const heroSubtitle = document.getElementById('hero-subtitle');
    const heroYear = document.getElementById('hero-year');
    const heroRating = document.getElementById('hero-rating');
    const heroGenre = document.getElementById('hero-genre');
    const heroWatchBtn = document.getElementById('hero-watch-btn');
    const heroBackground = document.getElementById('hero-background');

    // Use Poster (OMDb) or poster (custom) or fallback
    let posterUrl = (movie.Poster && movie.Poster !== 'N/A') ? movie.Poster : (movie.poster && movie.poster !== 'N/A' ? movie.poster : 'https://via.placeholder.com/1920x1080/333/666?text=Loading...');
    
    if (heroTitle) {
        heroTitle.textContent = movie.title || movie.Title;
    }
    
    if (heroSubtitle) {
        heroSubtitle.textContent = movie.plot || movie.Plot || 'Experience this amazing movie with high-quality streaming. No registration required.';
    }
    
    if (heroYear) {
        heroYear.textContent = movie.year || movie.Year || '';
        heroYear.style.display = (movie.year || movie.Year) ? 'inline-block' : 'none';
    }
    
    if (heroRating) {
        heroRating.textContent = movie.rating || movie.imdbRating || '';
        heroRating.style.display = (movie.rating || movie.imdbRating) ? 'inline-block' : 'none';
    }
    
    if (heroGenre) {
        heroGenre.textContent = movie.genre || movie.Genre || '';
        heroGenre.style.display = (movie.genre || movie.Genre) ? 'inline-block' : 'none';
    }
    
    if (heroWatchBtn) {
        heroWatchBtn.onclick = () => watchMovie(movie.imdbID || movie.imdbId || movie.imdb_id);
    }
    
    // Set the background as the main hero poster
    if (heroBackground) {
        console.log('🎬 Setting hero background poster:', posterUrl);
        heroBackground.style.backgroundImage = `url(${posterUrl})`;
        heroBackground.style.backgroundSize = 'cover';
        heroBackground.style.backgroundPosition = 'center';
        heroBackground.style.filter = 'none';
        heroBackground.style.opacity = '1';
        console.log('✅ Hero background poster set successfully');
    }
    
    // Update navigation dots
    const dots = document.querySelectorAll('.hero-dot');
    dots.forEach((dot, i) => {
        dot.classList.toggle('active', i === index);
    });
}

function startHeroRotation() {
    if (heroMovies.length <= 1) return;
    
    // Clear existing interval
    if (heroInterval) {
        clearInterval(heroInterval);
    }
    
    // Start new interval
    heroInterval = setInterval(() => {
        const nextIndex = (currentHeroIndex + 1) % heroMovies.length;
        showHeroMovie(nextIndex);
    }, 5000); // Change every 5 seconds
}

function stopHeroRotation() {
    if (heroInterval) {
        clearInterval(heroInterval);
        heroInterval = null;
    }
}

// Export functions for global use
window.searchMovies = searchMovies;
window.scrollToSection = scrollToSection;
window.watchMovie = watchMovie;
window.showNotification = showNotification;

// New Releases Carousel Logic
const newReleases = [
  {
    Title: 'Dune: Part Two',
    Year: '2024',
    imdbID: 'tt15239678',
    Poster: 'https://m.media-amazon.com/images/M/MV5BZTg2YjQwYjUtYjQwZi00YjQwLTk1YWUtN2FlNDM1MDExMDlhXkEyXkFqcGdeQXVyMTMxODk2OTU@._V1_SX300.jpg'
  },
  {
    Title: 'Godzilla x Kong: The New Empire',
    Year: '2024',
    imdbID: 'tt14539740',
    Poster: 'https://m.media-amazon.com/images/M/MV5BMjA2YjQwYjUtYjQwZi00YjQwLTk1YWUtN2FlNDM1MDExMDlhXkEyXkFqcGdeQXVyMTMxODk2OTU@._V1_SX300.jpg'
  },
  {
    Title: 'Civil War',
    Year: '2024',
    imdbID: 'tt17279496',
    Poster: 'https://m.media-amazon.com/images/M/MV5BMjA2YjQwYjUtYjQwZi00YjQwLTk1YWUtN2FlNDM1MDExMDlhXkEyXkFqcGdeQXVyMTMxODk2OTU@._V1_SX300.jpg'
  },
  {
    Title: 'Ghostbusters: Frozen Empire',
    Year: '2024',
    imdbID: 'tt21235248',
    Poster: 'https://m.media-amazon.com/images/M/MV5BMjA2YjQwYjUtYjQwZi00YjQwLTk1YWUtN2FlNDM1MDExMDlhXkEyXkFqcGdeQXVyMTMxODk2OTU@._V1_SX300.jpg'
  },
  {
    Title: 'Kung Fu Panda 4',
    Year: '2024',
    imdbID: 'tt21692408',
    Poster: 'https://m.media-amazon.com/images/M/MV5BMjA2YjQwYjUtYjQwZi00YjQwLTk1YWUtN2FlNDM1MDExMDlhXkEyXkFqcGdeQXVyMTMxODk2OTU@._V1_SX300.jpg'
  }
];

function populateNewReleasesCarousel() {
  const carouselInner = document.getElementById('new-releases-carousel-inner');
  if (!carouselInner) return;
  carouselInner.innerHTML = '';
  newReleases.forEach((movie, idx) => {
    const isActive = idx === 0 ? 'active' : '';
    const slide = document.createElement('div');
    slide.className = `carousel-item ${isActive}`;
    slide.innerHTML = `
      <div class="row align-items-center justify-content-center" style="min-height: 380px;">
        <div class="col-md-4 text-center">
          <img src="${movie.Poster}" alt="${movie.Title}" class="img-fluid rounded shadow-lg mb-3 bg-dark" style="max-height: 400px; background: #222;" onerror="this.onerror=null;this.src='https://via.placeholder.com/300x450?text=No+Image';">
        </div>
        <div class="col-md-6 d-flex flex-column justify-content-center align-items-start">
          <h3 class="mb-2">${movie.Title}</h3>
          <p class="mb-2 text-muted">${movie.Year}</p>
          <a href="/movie/${movie.imdbID}" class="btn btn-primary btn-lg">Watch Now</a>
        </div>
      </div>
    `;
    carouselInner.appendChild(slide);
  });
}

document.addEventListener('DOMContentLoaded', populateNewReleasesCarousel);

function loadContinueWatching() {
    const row = document.getElementById('continue-watching-row');
    const grid = document.getElementById('continue-watching-movies');
    if (!row || !grid) return;
    // Find all continueWatching items in localStorage
    const items = [];
    for (let i = 0; i < localStorage.length; i++) {
        const key = localStorage.key(i);
        if (key && key.startsWith('continueWatching_')) {
            try {
                const data = JSON.parse(localStorage.getItem(key));
                if (data && data.imdbId && data.title && data.poster && data.time && data.duration && data.time < data.duration - 10) {
                    items.push(data);
                }
            } catch (e) { /* ignore */ }
        }
    }
    // Sort by most recently watched (last in localStorage is most recent)
    items.reverse();
    grid.innerHTML = '';
    if (items.length === 0) {
        row.style.display = 'none';
        return;
    }
    row.style.display = '';
    items.forEach(data => {
        const card = document.createElement('div');
        card.className = 'movie-card fade-in';
        card.onclick = () => watchMovie(data.imdbId);
        card.innerHTML = `
            <div class="movie-poster">
                <img src="${data.poster}" alt="${data.title}" loading="lazy">
                <div class="progress-bar" style="position:absolute;bottom:0;left:0;width:100%;height:6px;background:#222;">
                    <div style="width:${Math.round(100 * data.time / data.duration)}%;height:100%;background:#e50914;"></div>
                </div>
            </div>
            <div class="movie-info">
                <h3 class="movie-title">${data.title}</h3>
                <p class="movie-year">${data.time ? 'Resume at ' + formatTime(data.time) : ''}</p>
            </div>
        `;
        grid.appendChild(card);
    });
}

// Featured movies for carousel
const featuredMovies = [
    { imdbId: 'tt0468569', title: 'The Dark Knight', year: '2008', poster: 'https://m.media-amazon.com/images/M/MV5BMTMxNTMwODM0NF5BMl5BanBnXkFtZTcwODAyMTk2Mw@@._V1_SX300.jpg' },
    { imdbId: 'tt0111161', title: 'The Shawshank Redemption', year: '1994', poster: 'https://m.media-amazon.com/images/M/MV5BNDE3ODcxYzMtY2YzZC00NmNlLWJiNDMtZDViZWM2MzIxZDYwXkEyXkFqcGdeQXVyNjAwNDUxODI@._V1_SX300.jpg' },
    { imdbId: 'tt0133093', title: 'The Matrix', year: '1999', poster: 'https://m.media-amazon.com/images/M/MV5BNzQzOTk3OTAtNDQ0Zi00ZTVkLWI0MTEtMDllZjNkYzNjNTc4L2ltYWdlXkEyXkFqcGdeQXVyNjU0OTQ0OTY@._V1_SX300.jpg' },
    { imdbId: 'tt0110912', title: 'Pulp Fiction', year: '1994', poster: 'https://m.media-amazon.com/images/M/MV5BNGNhMDIzZTUtNTBlZi00MTRlLWFjM2ItYzViMjE3YzI5MjljXkEyXkFqcGdeQXVyNzkwMjQ5NzM@._V1_SX300.jpg' },
    { imdbId: 'tt0133093', title: 'Inception', year: '2010', poster: 'https://m.media-amazon.com/images/M/MV5BMjAxMzY3NjcxNF5BMl5BanBnXkFtZTcwNTI5OTM0Mw@@._V1_SX300.jpg' },
    { imdbId: 'tt0114369', title: 'Se7en', year: '1995', poster: 'https://m.media-amazon.com/images/M/MV5BOTUwODM5MTctZjczMi00OTk4LTg3NWUtNmVhMTAzNTNjYjcyXkEyXkFqcGdeQXVyNjU0OTQ0OTY@._V1_SX300.jpg' }
];

let currentCarouselIndex = 0;

// Initialize carousel
function initializeCarousel() {
    const carouselContainer = document.getElementById('featured-carousel');
    const indicatorsContainer = document.getElementById('carousel-indicators');
    
    if (!carouselContainer || !indicatorsContainer) return;
    
    // Clear existing content
    carouselContainer.innerHTML = '';
    indicatorsContainer.innerHTML = '';
    
    // Add movies to carousel
    featuredMovies.forEach((movie, index) => {
        const movieElement = document.createElement('div');
        movieElement.className = `carousel-movie ${index === 0 ? 'active' : ''}`;
        movieElement.onclick = () => selectCarouselMovie(index);
        
        movieElement.innerHTML = `
            <img src="${movie.poster}" alt="${movie.title}" onerror="this.src='https://via.placeholder.com/200x120/333/666?text=Movie'">
        `;
        
        carouselContainer.appendChild(movieElement);
        
        // Add indicator
        const indicator = document.createElement('div');
        indicator.className = `carousel-indicator ${index === 0 ? 'active' : ''}`;
        indicator.onclick = () => selectCarouselMovie(index);
        indicatorsContainer.appendChild(indicator);
    });
    
    // Auto-rotate carousel
    setInterval(() => {
        currentCarouselIndex = (currentCarouselIndex + 1) % featuredMovies.length;
        selectCarouselMovie(currentCarouselIndex);
    }, 5000);
}

// Select carousel movie
function selectCarouselMovie(index) {
    currentCarouselIndex = index;
    const movie = featuredMovies[index];
    
    // Update active states
    document.querySelectorAll('.carousel-movie').forEach((el, i) => {
        el.classList.toggle('active', i === index);
    });
    
    document.querySelectorAll('.carousel-indicator').forEach((el, i) => {
        el.classList.toggle('active', i === index);
    });
    
    // Update hero background
    const heroBackground = document.querySelector('.hero-background');
    if (heroBackground && movie.poster) {
        heroBackground.style.backgroundImage = `url(${movie.poster})`;
    }
    
    // Update hero content
    const heroTitle = document.getElementById('hero-title');
    const heroSubtitle = document.getElementById('hero-subtitle');
    const heroYear = document.getElementById('hero-year');
    
    if (heroTitle) heroTitle.textContent = movie.title;
    if (heroSubtitle) heroSubtitle.textContent = `Experience this amazing movie with high-quality streaming. No registration required.`;
    if (heroYear) heroYear.textContent = movie.year;
    
    // Update watch button
    const watchBtn = document.getElementById('hero-watch-btn');
    if (watchBtn) {
        watchBtn.onclick = () => window.location.href = `/watch/${movie.imdbId}`;
    }
}

// Navigation functionality
function initializeNavigation() {
    const navLinks = document.querySelectorAll('.navbar-nav .nav-link');
    
    navLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            // Remove active class from all links
            navLinks.forEach(l => l.classList.remove('active'));
            
            // Add active class to clicked link
            this.classList.add('active');
            
            // Handle smooth scrolling for anchor links
            const href = this.getAttribute('href');
            if (href.startsWith('#')) {
                e.preventDefault();
                const targetSection = document.querySelector(href);
                if (targetSection) {
                    targetSection.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start'
                    });
                }
            }
        });
    });
    
    // Update active state based on scroll position
    window.addEventListener('scroll', function() {
        const sections = ['home', 'movies', 'tv-shows', 'categories'];
        const scrollPos = window.scrollY + 100;
        
        sections.forEach(section => {
            const element = document.querySelector(`#${section}`);
            if (element) {
                const offsetTop = element.offsetTop;
                const offsetHeight = element.offsetHeight;
                
                if (scrollPos >= offsetTop && scrollPos < offsetTop + offsetHeight) {
                    navLinks.forEach(link => {
                        link.classList.remove('active');
                        if (link.getAttribute('data-section') === section) {
                            link.classList.add('active');
                        }
                    });
                }
            }
        });
    });
}

// Initialize navigation when page loads
document.addEventListener('DOMContentLoaded', function() {
    initializeCarousel();
    initializeApp();
    initializeNavigation();
    loadPopularMovies();
    loadContinueWatching();
});
