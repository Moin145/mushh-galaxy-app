// Configuration
const FALLBACK_POSTER = 'https://via.placeholder.com/200x300?text=No+Image';
const SECTIONS = [
  { key: 'only-on-netflix', title: 'Only on Netflix', keyword: 'Netflix' },
  { key: 'documentaries', title: 'Documentaries', keyword: 'Documentary' },
  { key: 'dubbed-tamil', title: 'Movies & TV Shows Dubbed in Tamil', keyword: 'Tamil' },
  { key: 'top-10-movies', title: 'Top 10 Movies in Netflix Today', keyword: 'Popular' },
  { key: 'asian-tv', title: 'Asian TV Shows', keyword: 'Asian' },
  { key: 'anime', title: 'Anime', keyword: 'Anime' },
  { key: 'comedy-movies', title: 'Comedy Movies', keyword: 'Comedy' },
  { key: 'blockbuster-movies', title: 'Blockbuster Movies', keyword: 'Action' }
];

// Fallback data for when API fails
const FALLBACK_SECTION_MOVIES = {
  'only-on-netflix': [
    { Title: 'Squid Game', Year: '2021', imdbID: 'tt10919420', Poster: 'https://m.media-amazon.com/images/M/MV5BYWE3MDVkN2EtNjQ5MS00ZDQ4LWI3YzgtMTUwNWIwOWY2ZTI4XkEyXkFqcGdeQXVyMTEzMTI1Mjk3._V1_SX300.jpg' },
    { Title: 'Money Heist', Year: '2017', imdbID: 'tt6468322', Poster: 'https://m.media-amazon.com/images/M/MV5BODI0ZTljYTMtODQ1NC00NmI0LTk1YWUtN2FlNDM1MDExMDlhXkEyXkFqcGdeQXVyMTMxODk2OTU@._V1_SX300.jpg' }
  ],
  'documentaries': [
    { Title: 'My Octopus Teacher', Year: '2020', imdbID: 'tt12888462', Poster: 'https://m.media-amazon.com/images/M/MV5BNTYxZDkzNGEtNzg3NS00NmQxLWJlNmMtNDY3NzVkNTU3ZTEwXkEyXkFqcGdeQXVyMTMxODk2OTU@._V1_SX300.jpg' }
  ],
  'comedy-movies': [
    { Title: 'The Hangover', Year: '2009', imdbID: 'tt1119646', Poster: 'https://m.media-amazon.com/images/M/MV5BNGQwZjg5YmYtY2VkNC00NzliLTljYTctNzI5NmU3MjE2ODQzXkEyXkFqcGdeQXVyNzkwMjQ5NzM@._V1_SX300.jpg' }
  ],
  'blockbuster-movies': [
    { Title: 'Avengers: Endgame', Year: '2019', imdbID: 'tt4154796', Poster: 'https://m.media-amazon.com/images/M/MV5BMTc5MDE2ODcwNV5BMl5BanBnXkFtZTgwMzI2NzQ2NzM@._V1_SX300.jpg' }
  ]
};

// DOM Elements
const heroBg = document.querySelector('.hero-bg');
const heroTitle = document.getElementById('hero-title');
const heroOverview = document.getElementById('hero-overview');
const heroBtn = document.getElementById('hero-play-btn');

// 1. Movie Card Creation
function createMovieCard(movie) {
  if (!movie?.imdbID || movie.imdbID === 'N/A') return null;
  
  const card = document.createElement('div');
  card.className = 'movie-card';
  card.dataset.imdbid = movie.imdbID;
  
  const posterUrl = movie.Poster && movie.Poster !== 'N/A' ? movie.Poster : FALLBACK_POSTER;
  
  card.innerHTML = `
    <img src="${posterUrl}" 
         alt="${movie.Title}"
         onerror="this.src='${FALLBACK_POSTER}'">
    <div class="card-overlay">
      <div class="play-btn">&#9658;</div>
      <div class="movie-title">${movie.Title}</div>
      <div class="movie-year">${movie.Year || ''}</div>
    </div>
  `;
  
  // Add click event listener
  card.addEventListener('click', (e) => {
    e.preventDefault();
    navigateToMovie(movie.imdbID);
  });
  
  return card;
}

function navigateToMovie(imdbID) {
  if (imdbID && imdbID !== 'N/A') {
    console.log('Navigating to movie:', imdbID);
    window.location.href = `/watch/${imdbID}`;
  } else {
    console.error('Invalid IMDb ID:', imdbID);
  }
}

// 2. Row Population
async function populateRow(sectionKey, keyword) {
  const row = document.querySelector(`.movie-row[data-section="${sectionKey}"] .row-posters`);
  if (!row) return;
  
  row.innerHTML = '<div class="loading-spinner">Loading...</div>';
  
  try {
    console.log(`Loading section: ${sectionKey} with keyword: ${keyword}`);
    const res = await fetch(`/api/search?title=${encodeURIComponent(keyword)}`);
    const data = await res.json();
    
    if (data.error) {
      throw new Error(data.error);
    }
    
    const movies = Array.isArray(data) ? data : [];
    const validMovies = movies
      .filter(movie => movie?.imdbID && movie.imdbID !== 'N/A')
      .slice(0, 10);
    
    console.log(`Found ${validMovies.length} valid movies for ${sectionKey}`);
    displayMovies(row, validMovies, sectionKey);
    
  } catch (err) {
    console.error(`Failed loading ${sectionKey}:`, err);
    useFallbackContent(row, sectionKey);
  }
}

function displayMovies(row, movies, sectionKey) {
  row.innerHTML = '';
  
  // Use fallback if no movies found
  if (!movies?.length && FALLBACK_SECTION_MOVIES[sectionKey]) {
    movies = FALLBACK_SECTION_MOVIES[sectionKey];
  }
  
  if (!movies?.length) {
    row.innerHTML = '<div class="error-message">No movies found</div>';
    return;
  }
  
  movies.forEach(movie => {
    const card = createMovieCard(movie);
    if (card) row.appendChild(card);
  });
}

function useFallbackContent(row, sectionKey) {
  if (FALLBACK_SECTION_MOVIES[sectionKey]) {
    console.log(`Using fallback content for ${sectionKey}`);
    displayMovies(row, FALLBACK_SECTION_MOVIES[sectionKey], sectionKey);
  } else {
    row.innerHTML = '<div class="error-message">Failed to load content</div>';
  }
}

// 3. Hero Section
async function populateHero() {
  const heroMovies = [
    { Title: 'Squid Game', Year: '2021', imdbID: 'tt10919420', Poster: 'https://m.media-amazon.com/images/M/MV5BYWE3MDVkN2EtNjQ5MS00ZDQ4LWI3YzgtMTUwNWIwOWY2ZTI4XkEyXkFqcGdeQXVyMTEzMTI1Mjk3._V1_SX300.jpg' },
    { Title: 'Money Heist', Year: '2017', imdbID: 'tt6468322', Poster: 'https://m.media-amazon.com/images/M/MV5BODI0ZTljYTMtODQ1NC00NmI0LTk1YWUtN2FlNDM1MDExMDlhXkEyXkFqcGdeQXVyMTMxODk2OTU@._V1_SX300.jpg' },
    { Title: 'Stranger Things', Year: '2016', imdbID: 'tt4574334', Poster: 'https://m.media-amazon.com/images/M/MV5BMjEzMDAxOTUyMV5BMl5BanBnXkFtZTgwNzAxMzYzOTE@._V1_SX300.jpg' }
  ];
  
  // Try to fetch from API first
  try {
    const res = await fetch('/api/search?title=Popular');
    const data = await res.json();
    
    if (Array.isArray(data) && data.length > 0) {
      const movie = data.find(m => m?.Poster && m.Poster !== 'N/A' && m.imdbID);
      if (movie) {
        updateHeroSection(movie);
        return;
      }
    }
  } catch (err) {
    console.error('Failed to fetch hero content from API:', err);
  }
  
  // Use fallback
  const randomMovie = heroMovies[Math.floor(Math.random() * heroMovies.length)];
  updateHeroSection(randomMovie);
}

function updateHeroSection(movie) {
  if (movie.Poster && movie.Poster !== 'N/A') {
    heroBg.style.backgroundImage = `url('${movie.Poster}')`;
    heroBg.classList.add('loaded');
  }
  
  heroTitle.textContent = movie.Title;
  heroOverview.textContent = movie.Year ? `Released: ${movie.Year}` : 'Discover amazing content';
  heroBtn.onclick = () => navigateToMovie(movie.imdbID);
}

// 4. Row Scrolling
function setupRowScrolling() {
  document.querySelectorAll('.movie-row').forEach(row => {
    const posters = row.querySelector('.row-posters');
    const leftArrow = row.querySelector('.arrow.left');
    const rightArrow = row.querySelector('.arrow.right');
    
    leftArrow?.addEventListener('click', () => {
      posters.scrollBy({ left: -400, behavior: 'smooth' });
    });
    
    rightArrow?.addEventListener('click', () => {
      posters.scrollBy({ left: 400, behavior: 'smooth' });
    });
  });
}

// 5. Search Functionality
function setupSearch() {
  const form = document.getElementById('search-form');
  const input = document.getElementById('search-input');
  const resultsSection = document.getElementById('search-results');
  const resultsRow = resultsSection?.querySelector('.row-posters');
  
  if (!form || !resultsRow) return;
  
  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const query = input.value.trim();
    if (!query) return;
    
    resultsSection.style.display = 'block';
    resultsRow.innerHTML = '<div class="loading-spinner">Searching...</div>';
    
    try {
      const res = await fetch(`/api/search?title=${encodeURIComponent(query)}`);
      const data = await res.json();
      
      resultsRow.innerHTML = '';
      
      if (data.error) {
        resultsRow.innerHTML = '<div class="error-message">Search failed</div>';
        return;
      }
      
      const movies = Array.isArray(data) ? data : [];
      const validMovies = movies.filter(movie => movie?.imdbID && movie.imdbID !== 'N/A');
      
      if (validMovies.length === 0) {
        resultsRow.innerHTML = '<div class="error-message">No results found</div>';
        return;
      }
      
      validMovies.forEach(movie => {
        const card = createMovieCard(movie);
        if (card) resultsRow.appendChild(card);
      });
      
    } catch (err) {
      resultsRow.innerHTML = '<div class="error-message">Search failed</div>';
      console.error('Search error:', err);
    }
  });
  
  // Hide results when input is cleared
  input.addEventListener('input', () => {
    if (!input.value.trim()) {
      resultsSection.style.display = 'none';
    }
  });
}

// 6. Initialization
function initializeApp() {
  console.log('Initializing MOinMirror app...');
  
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', startApp);
  } else {
    startApp();
  }
}

function startApp() {
  try {
    console.log('Starting app...');
    populateAllRows();
    populateHero();
    setupRowScrolling();
    setupSearch();
    console.log('App initialized successfully');
  } catch (err) {
    console.error('Initialization failed:', err);
  }
}

function populateAllRows() {
  SECTIONS.forEach(section => {
    populateRow(section.key, section.keyword);
  });
}

// Start the app
initializeApp();
