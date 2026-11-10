// Wait for the DOM to be fully loaded
document.addEventListener('DOMContentLoaded', function () {
    if (typeof L === 'undefined') {
        console.error('Leaflet library not loaded');
        alert('Error: Leaflet mapping library not loaded. Please check your internet connection.');
        return;
    }

    const CITIES_URL = '/api/cities/';
    const weatherUrl = (cityId) => `/api/weather/${cityId}/`;
    const forecastUrl = (cityId) => `/api/forecast/${cityId}/`;
    const iconUrl = (icon) => `https://cdn.aerisapi.com/wxblox/icons/${encodeURIComponent(icon)}`;

    const SEARCH_RESULT_LIMIT = 8;
    const SEARCH_ZOOM = 8;

    // Initialize the map showing the whole world
    const map = L.map('map').setView([30, 10], 2);

    // Add OpenStreetMap tiles
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; OpenStreetMap contributors',
        maxZoom: 19,
    }).addTo(map);

    // Store markers and city records for reference
    const markers = {};
    let cities = [];

    // Temperature unit preference: 'C' or 'F'. The server always returns metric values,
    // so conversion happens only in the browser and cached responses suit both units.
    let temperatureUnit = 'C';

    // The popup that is currently open, so it can be redrawn when the unit changes
    let openPopup = null;

    // Custom icon for city markers
    const cityIcon = L.divIcon({
        className: 'custom-div-icon',
        html: `<div style="
            background-color: #667eea;
            width: 30px;
            height: 30px;
            border-radius: 50%;
            border: 3px solid white;
            box-shadow: 0 2px 5px rgba(0,0,0,0.3);
            cursor: pointer;
        "></div>`,
        iconSize: [30, 30],
        iconAnchor: [15, 15]
    });

    // Text from external APIs is escaped before it is placed in popup HTML
    function escapeHtml(value) {
        return String(value).replace(/[&<>"']/g, (character) => ({
            '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
        }[character]));
    }

    // ---------- Temperature conversion (Enhancement 4) ----------

    function celsiusToFahrenheit(celsius) {
        return (celsius * 9 / 5) + 32;
    }

    // Format a Celsius value in the selected unit; missing values show a dash
    function formatTemperature(celsius) {
        if (celsius === null || celsius === undefined || Number.isNaN(Number(celsius))) {
            return '—';
        }
        const value = temperatureUnit === 'F' ? celsiusToFahrenheit(Number(celsius)) : Number(celsius);
        return `${value.toFixed(1)}°${temperatureUnit}`;
    }

    const unitToggle = document.getElementById('unit-toggle');
    if (unitToggle) {
        unitToggle.addEventListener('click', () => {
            temperatureUnit = temperatureUnit === 'C' ? 'F' : 'C';
            unitToggle.textContent = temperatureUnit === 'C' ? 'Show °F' : 'Show °C';
            unitToggle.setAttribute('aria-pressed', String(temperatureUnit === 'F'));
            if (openPopup) renderPopup(openPopup);
        });
    }

    // ---------- Cities and markers ----------

    // Fetch and display cities
    async function loadCities() {
        try {
            const response = await fetch(CITIES_URL);
            if (!response.ok) {
                throw new Error(`Failed to fetch cities (HTTP ${response.status})`);
            }

            cities = await response.json();
            console.log(`Loaded ${cities.length} cities`);

            if (cities.length === 0) {
                showMapMessage('No cities found. Run: docker compose run --rm web python manage.py populate_cities');
                return;
            }

            cities.forEach(addCityMarker);

            // Show matches for anything typed into the search box while cities were loading
            if (searchInput && searchInput.value.trim()) updateSearchResults(searchInput.value);
        } catch (error) {
            console.error('Error loading cities:', error);
            showMapMessage(`Failed to load cities: ${error.message}`);
        }
    }

    // Show a message in a popup in the middle of the map
    function showMapMessage(message) {
        L.popup()
            .setLatLng(map.getCenter())
            .setContent(`<div class="error-message">${escapeHtml(message)}</div>`)
            .openOn(map);
    }

    // Add a marker for a city
    function addCityMarker(city) {
        const marker = L.marker([city.latitude, city.longitude], {
            icon: cityIcon,
            title: `${city.name}, ${city.country}`
        }).addTo(map);

        marker.on('click', () => fetchWeatherData(city.id, marker));
        markers[city.id] = marker;
    }

    // Fetch JSON from our Django API and turn error responses into exceptions
    async function fetchJson(url) {
        const response = await fetch(url);
        const data = await response.json().catch(() => ({}));
        if (!response.ok) {
            throw new Error(data.error || `Request failed (HTTP ${response.status})`);
        }
        return data;
    }

    // Fetch current weather for a city from OUR Django API (server-side proxy to XWeather)
    async function fetchWeatherData(cityId, marker) {
        showLoading();

        try {
            const weather = await fetchJson(weatherUrl(cityId));
            openPopup = {
                cityId,
                marker,
                weather,
                forecast: null,        // loaded when the Forecast tab is first opened
                forecastError: null,
                activeTab: 'current',
            };
            openPopup.element = createPopupElement(openPopup);
            renderPopup(openPopup);
            marker.bindPopup(openPopup.element, {
                maxWidth: 320,
                className: 'weather-popup-container'
            }).openPopup();
        } catch (error) {
            console.error('Error fetching weather:', error);
            openPopup = null;
            displayErrorPopup(marker, error.message);
        } finally {
            hideLoading();
        }
    }

    // Load the 3-day forecast for the open popup (Enhancement 1)
    async function loadForecast(state) {
        try {
            const data = await fetchJson(forecastUrl(state.cityId));
            state.forecast = data.forecast;
            state.forecastError = null;
        } catch (error) {
            console.error('Error fetching forecast:', error);
            state.forecastError = error.message;
        }
        if (openPopup === state) renderPopup(state);
    }

    // ---------- Popup rendering ----------

    // Build the popup frame (title, tabs, panel) once. Tab buttons are never replaced:
    // removing the clicked element mid-click makes Leaflet treat it as a map click and close the popup.
    function createPopupElement(state) {
        const { weather } = state;
        const element = document.createElement('div');
        element.className = 'weather-popup';
        element.innerHTML = `
            <h3>${escapeHtml(weather.city)}, ${escapeHtml(weather.country)}</h3>
            <div class="popup-tabs" role="tablist">
                <button type="button" class="popup-tab" role="tab" data-tab="current">Current</button>
                <button type="button" class="popup-tab" role="tab" data-tab="forecast">Forecast</button>
            </div>
            <div class="popup-panel" role="tabpanel"></div>
        `;
        element.querySelectorAll('.popup-tab').forEach((button) => {
            button.addEventListener('click', () => selectTab(state, button.dataset.tab));
        });
        return element;
    }

    // Update the tab states and the active panel's content
    function renderPopup(state) {
        state.element.querySelectorAll('.popup-tab').forEach((button) => {
            button.setAttribute('aria-selected', String(button.dataset.tab === state.activeTab));
        });
        state.element.querySelector('.popup-panel').innerHTML =
            state.activeTab === 'current' ? currentWeatherHtml(state.weather) : forecastHtml(state);

        // Let Leaflet resize the popup to fit the new content
        const popup = state.marker.getPopup();
        if (popup) popup.update();
    }

    function selectTab(state, tabId) {
        state.activeTab = tabId;
        const needsForecast = tabId === 'forecast' && !state.forecast;
        if (needsForecast) state.forecastError = null;
        renderPopup(state);
        if (needsForecast) loadForecast(state);
    }

    function currentWeatherHtml(data) {
        const description = escapeHtml(data.description);
        const item = (label, value) => `
            <div class="weather-item">
                <div>
                    <strong>${label}</strong>
                    <span>${value}</span>
                </div>
            </div>`;

        return `
            <div class="weather-icon-container">
                <img src="${iconUrl(data.icon)}" alt="${description}">
                <div class="weather-description">${description}</div>
            </div>
            <div class="weather-info">
                ${item('Temperature', formatTemperature(data.temperature))}
                ${item('Feels Like', formatTemperature(data.feels_like))}
                ${item('Humidity', `${Number(data.humidity)}%`)}
                ${item('Wind Speed', `${Number(data.wind_speed)} m/s`)}
                ${item('Pressure', `${Number(data.pressure)} hPa`)}
            </div>
        `;
    }

    function forecastHtml(state) {
        if (state.forecastError) {
            return `<div class="error-message">Unable to fetch forecast: ${escapeHtml(state.forecastError)}</div>`;
        }
        if (!state.forecast) {
            return '<p class="forecast-status">Loading forecast...</p>';
        }

        const days = state.forecast.map((day) => {
            const description = escapeHtml(day.description);
            // Parse as a calendar date (not UTC midnight) so the weekday is correct everywhere
            const date = new Date(`${day.date}T12:00:00`);
            const label = date.toLocaleDateString(undefined, { weekday: 'short', month: 'short', day: 'numeric' });
            return `
                <li class="forecast-day">
                    <img src="${iconUrl(day.icon)}" alt="${description}">
                    <div>
                        <div class="forecast-date">${escapeHtml(label)}</div>
                        <div class="weather-description">${description}</div>
                    </div>
                    <div class="forecast-temps">
                        <div>${formatTemperature(day.max_temp)} / ${formatTemperature(day.min_temp)}</div>
                        <div>${Number(day.precipitation_chance ?? 0)}% rain</div>
                    </div>
                </li>`;
        }).join('');

        return `<ul class="forecast-list">${days}</ul>`;
    }

    // Display an error message in a popup
    function displayErrorPopup(marker, errorMessage = 'Unknown error') {
        const errorContent = `
            <div class="weather-popup">
                <h3>Error</h3>
                <div class="error-message">
                    Unable to fetch weather data: ${escapeHtml(errorMessage)}
                    <br><br>
                    Please try again later.
                </div>
            </div>
        `;

        marker.bindPopup(errorContent).openPopup();
    }

    // Forget the popup state once the user closes it
    map.on('popupclose', (event) => {
        if (openPopup && event.popup === openPopup.marker.getPopup()) openPopup = null;
    });

    // ---------- City search (Enhancement 3) ----------

    const searchForm = document.getElementById('city-search');
    const searchInput = document.getElementById('city-search-input');
    const searchResults = document.getElementById('city-search-results');
    let searchMatches = [];
    let highlightedIndex = -1;

    if (searchForm && searchInput && searchResults) {
        // Stop map dragging/zooming when interacting with the search box
        L.DomEvent.disableClickPropagation(searchForm);
        L.DomEvent.disableScrollPropagation(searchForm);

        searchInput.addEventListener('input', () => updateSearchResults(searchInput.value));

        searchInput.addEventListener('keydown', (event) => {
            if (event.key === 'ArrowDown' || event.key === 'ArrowUp') {
                event.preventDefault();
                if (searchMatches.length === 0) return;
                const step = event.key === 'ArrowDown' ? 1 : -1;
                highlightedIndex = (highlightedIndex + step + searchMatches.length) % searchMatches.length;
                renderSearchResults();
            } else if (event.key === 'Escape') {
                clearSearch();
            }
        });

        // Enter selects the highlighted city, or the first match
        searchForm.addEventListener('submit', (event) => {
            event.preventDefault();
            const city = searchMatches[Math.max(highlightedIndex, 0)];
            if (city) selectCity(city);
        });

        searchResults.addEventListener('click', (event) => {
            const item = event.target.closest('li[data-index]');
            if (item) selectCity(searchMatches[Number(item.dataset.index)]);
        });

        // Close the results list when clicking elsewhere on the page
        document.addEventListener('click', (event) => {
            if (!searchForm.contains(event.target)) searchResults.hidden = true;
        });
    }

    function updateSearchResults(text) {
        const query = text.trim().toLowerCase();
        highlightedIndex = -1;
        searchMatches = query
            ? cities.filter((city) =>
                city.name.toLowerCase().includes(query) || city.country.toLowerCase().includes(query)
            ).slice(0, SEARCH_RESULT_LIMIT)
            : [];
        renderSearchResults(query);
    }

    function renderSearchResults(query = searchInput.value.trim()) {
        if (!query) {
            searchResults.hidden = true;
            searchResults.innerHTML = '';
            return;
        }

        searchResults.innerHTML = searchMatches.length
            ? searchMatches.map((city, index) => `
                <li role="option" data-index="${index}" aria-selected="${index === highlightedIndex}">
                    ${escapeHtml(city.name)}, ${escapeHtml(city.country)}
                </li>`).join('')
            : '<li class="no-results">No matching cities</li>';
        searchResults.hidden = false;
    }

    // Zoom to the city and open its weather popup
    function selectCity(city) {
        clearSearch();
        searchInput.value = `${city.name}, ${city.country}`;
        map.setView([city.latitude, city.longitude], SEARCH_ZOOM);
        fetchWeatherData(city.id, markers[city.id]);
    }

    function clearSearch() {
        searchMatches = [];
        highlightedIndex = -1;
        searchResults.hidden = true;
        searchResults.innerHTML = '';
    }

    // ---------- Loading overlay ----------

    function showLoading() {
        const loadingEl = document.getElementById('loading');
        if (loadingEl) loadingEl.classList.add('active');
    }

    function hideLoading() {
        const loadingEl = document.getElementById('loading');
        if (loadingEl) loadingEl.classList.remove('active');
    }

    // Initialize the application
    loadCities();

    // Helper for debugging in the browser console
    window.debugMap = { map, markers, loadCities };
});
