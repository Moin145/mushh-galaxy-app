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

// Handle search input changes
function handleSearchInput(e) {
    const query = e.target.value.trim();
    if (query.length > 2 && query !== currentQuery) {
        searchMovies(query);
    } else if (query.length === 0) {
        hideSearchResults();
    }
}

// Search movies function
async function searchMovies(query) {
    if (isSearching) return;
    
    isSearching = true;
    currentQuery = query;
    
    showLoading();
    hideSearchResults();
    
    try {
        console.log(`Searching for: ${query}`);
        
        const response = await fetch(`/search?q=${encodeURIComponent(query)}`);
        const data = await response.json();
        
        if (data.movies && data.movies.length > 0) {
            displaySearchResults(data.movies);
        } else {
            displayNoResults(query);
        }
        
    } catch (error) {
        console.error('Search error:', error);
        displayError('Search failed. Please try again.');
    } finally {
        hideLoading();
        isSearching = false;
    }
}

// Display search results
function displaySearchResults(movies) {
    if (!moviesGrid) return;
    
    moviesGrid.innerHTML = '';
    
    movies.forEach(movie => {
        const movieCard = createMovieCard(movie);
        moviesGrid.appendChild(movieCard);
    });
    
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
    
    const posterUrl = movie.Poster && movie.Poster !== 'N/A' 
        ? movie.Poster 
        : null;
    
    card.innerHTML = `
        <div class="movie-poster">
            ${posterUrl 
                ? `<img src="${posterUrl}" alt="${movie.Title}" loading="lazy">` 
                : '<i class="fas fa-film"></i>'
            }
        </div>
        <div class="movie-info">
            <h3 class="movie-title">${movie.Title}</h3>
            <p class="movie-year">${movie.Year}</p>
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

// Show/hide search results
function showSearchResults() {
    if (searchResults) {
        searchResults.classList.remove('d-none');
    }
}

function hideSearchResults() {
    if (searchResults) {
        searchResults.classList.add('d-none');
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

function showHeroMovie(index) {
    if (index >= heroMovies.length) return;
    
    const movie = heroMovies[index];
    currentHeroIndex = index;
    
    // Update hero content
    const heroTitle = document.getElementById('hero-title');
    const heroSubtitle = document.getElementById('hero-subtitle');
    const heroYear = document.getElementById('hero-year');
    const heroRating = document.getElementById('hero-rating');
    const heroGenre = document.getElementById('hero-genre');
    const heroPoster = document.getElementById('hero-poster');
    const heroWatchBtn = document.getElementById('hero-watch-btn');
    const heroBackground = document.getElementById('hero-background');
    
    if (heroTitle) {
        heroTitle.textContent = movie.title;
    }
    
    if (heroSubtitle) {
        heroSubtitle.textContent = movie.plot || 'Experience this amazing movie with high-quality streaming. No registration required.';
    }
    
    if (heroYear) {
        heroYear.textContent = movie.year || '';
        heroYear.style.display = movie.year ? 'inline-block' : 'none';
    }
    
    if (heroRating) {
        heroRating.textContent = movie.rating || '';
        heroRating.style.display = movie.rating ? 'inline-block' : 'none';
    }
    
    if (heroGenre) {
        heroGenre.textContent = movie.genre || '';
        heroGenre.style.display = movie.genre ? 'inline-block' : 'none';
    }
    
    if (heroPoster && movie.poster && movie.poster !== 'N/A') {
        heroPoster.src = movie.poster;
        heroPoster.alt = movie.title;
        heroPoster.style.display = 'block';
    }
    
    if (heroWatchBtn) {
        heroWatchBtn.onclick = () => watchMovie(movie.imdb_id);
    }
    
    if (heroBackground && movie.poster && movie.poster !== 'N/A') {
        heroBackground.style.backgroundImage = `url(${movie.poster})`;
        heroBackground.style.backgroundSize = 'cover';
        heroBackground.style.backgroundPosition = 'center';
        heroBackground.style.filter = 'blur(20px)';
        heroBackground.style.opacity = '0.3';
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
