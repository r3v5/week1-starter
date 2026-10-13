// Replace addMarkersToMap with clustered version
// Store cities data and markers
console.log('map.js loaded');
let citiesData = [];
let markers = {};
let cityCount = 0;
let map = null;
let heatLayer = null;

// Proximity search state
let proximityMode = null;
let searchMarker = null;
let radiusCircle = null;
let proximityLayer;
let radiusLayer;

const INITIAL_VIEW = { center: [53.3498, -6.2603], zoom: 6 };

// API endpoint
const API_URL = '/api/';

// Initialize the map
async function initMap() {
    // Initialize Leaflet map centered on Dublin
    map = L.map('map').setView(INITIAL_VIEW.center, INITIAL_VIEW.zoom);

    // Add OpenStreetMap tile layer
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors',
        maxZoom: 19,
        minZoom: 2
    }).addTo(map);

    setupProximitySearch();

    showLoading(true);
    try {
        // Fetch cities from API
        console.log('Fetching from:', API_URL);
        const response = await fetch(API_URL);
        console.log('Response status:', response.status);
        console.log('Response headers:', response.headers);

        if (!response.ok) {
            const errorText = await response.text();
            console.error('Error response body:', errorText);
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        console.log('Data received:', data);
        citiesData = data.results || data;
        cityCount = citiesData.length;

        // Update city count
        document.getElementById('cityCount').textContent = cityCount;

        // Add markers to map
        addMarkersToMap(citiesData);

        // Draw the full-city heatmap
        clearProximityResults();

    } catch (error) {
        console.error('Error fetching cities:', error);
        console.error('Error details:', {
            message: error.message,
            stack: error.stack,
            name: error.name
        });
        alert('Failed to load cities data. Check console for details.');
    } finally {
        showLoading(false);
    }
}

// Add markers for each city
function addMarkersToMap(cities) {
    // Clear existing markers
    Object.values(markers).forEach(marker => map.removeLayer(marker));
    markers = {};

    cities.forEach(city => {
        const lat = parseFloat(city.latitude);
        const lng = parseFloat(city.longitude);

        if (isNaN(lat) || isNaN(lng)) {
            console.warn(`Invalid coordinates for ${city.name}`);
            return;
        }

        // Create marker
        const marker = L.circleMarker([lat, lng], {
            radius: 6,
            fillColor: '#007bff',
            color: '#0056b3',
            weight: 2,
            opacity: 1,
            fillOpacity: 0.8
        }).addTo(map);

        // Add popup with city information
        const popupContent = createPopupContent(city);
        marker.bindPopup(popupContent);

        // Use this API city as the proximity search origin
        marker.on('click', () => {
            if (proximityMode) runProximitySearch(city);
        });

        // Store reference
        markers[city.id] = marker;
    });
}

// Create HTML content for popup
function createPopupContent(city) {
    return `
        <div class="city-popup">
            <h3>${city.name}</h3>
            <p><strong>Country:</strong> ${city.country}</p>
            ${city.region ? `<p><strong>Region:</strong> ${city.region}</p>` : ''}
            <p><strong>Population:</strong> ${formatNumber(city.population)}</p>
            <p><strong>Coordinates:</strong> ${city.latitude.toFixed(4)}, ${city.longitude.toFixed(4)}</p>
            ${city.founded_year ? `<p><strong>Founded:</strong> ${city.founded_year}</p>` : ''}
            ${city.timezone ? `<p><strong>Timezone:</strong> ${city.timezone}</p>` : ''}
        </div>
    `;
}

// Format numbers with thousands separator
function formatNumber(num) {
    return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',');
}

// Search functionality
function setupSearchListener() {
    document.getElementById('searchInput').addEventListener('input', function(e) {
        const query = e.target.value.toLowerCase();
        const resultsDiv = document.getElementById('results');

        if (query.length === 0) {
            resultsDiv.innerHTML = '';
            addMarkersToMap(citiesData);
            return;
        }

        // Filter cities
        const filtered = citiesData.filter(city => 
            city.name.toLowerCase().includes(query) ||
            city.country.toLowerCase().includes(query)
        );

        // Display results
        if (filtered.length === 0) {
            resultsDiv.innerHTML = '<p style="color: #999;">No cities found</p>';
            // Clear markers
            Object.values(markers).forEach(marker => map.removeLayer(marker));
            markers = {};
        } else {
            // Show matching markers only
            Object.values(markers).forEach(marker => map.removeLayer(marker));
            markers = {};
            addMarkersToMap(filtered);

            // Update results list
            resultsDiv.innerHTML = filtered.map(city => `
                <div style="padding: 8px; border-bottom: 1px solid #eee; cursor: pointer;" onclick="goToCity(${city.id})">
                    <strong>${city.name}</strong>, ${city.country}
                </div>
            `).join('');
        }
    });
}

// Navigate to city on map
function goToCity(cityId) {
    const city = citiesData.find(c => c.id === cityId);
    if (city) {
        map.setView([city.latitude, city.longitude], 10);
        if (markers[cityId]) {
            markers[cityId].openPopup();
        }
    }
}

// Reset map view
function setupResetListener() {
    document.getElementById('resetBtn').addEventListener('click', function() {
        map.setView(INITIAL_VIEW.center, INITIAL_VIEW.zoom, { animate: false });
        document.getElementById('searchInput').value = '';
        document.getElementById('results').innerHTML = '';
        addMarkersToMap(citiesData);
        // Disarm proximity search and clear its results and overlays
        setProximityMode(null);
    });
}

// Show/hide loading indicator
function showLoading(show) {
    document.getElementById('loading').style.display = show ? 'block' : 'none';
}

// Initialize map on page load
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM loaded, initializing map...');
    initMap();
    setupSearchListener();
    setupResetListener();
});


// Proximity search controls
function setupProximitySearch() {
    proximityLayer = L.layerGroup().addTo(map);
    radiusLayer = L.layerGroup().addTo(map);

    document.getElementById('nearest-search-btn').addEventListener('click', () => {
        setProximityMode('nearest');
    });
    document.getElementById('radius-search-btn').addEventListener('click', () => {
        setProximityMode('radius');
    });
}

function setProximityMode(mode) {
    proximityMode = proximityMode === mode ? null : mode;
    document.getElementById('radius-control').classList.toggle(
        'd-none', proximityMode !== 'radius'
    );
    document.getElementById('nearest-search-btn')
        .setAttribute('aria-pressed', proximityMode === 'nearest');
    document.getElementById('radius-search-btn')
        .setAttribute('aria-pressed', proximityMode === 'radius');
    document.getElementById('proximity-status').textContent = {
        nearest: 'Click a city marker to find its 10 nearest cities.',
        radius: 'Set a radius, then click a city marker.'
    }[proximityMode] || 'Choose a search, then click a city marker.';
    document.getElementById('proximity-status').classList.remove('is-error');
    map.getContainer().style.cursor = proximityMode ? 'crosshair' : '';
    clearProximityResults();
}

async function runProximitySearch(city) {
    if (!proximityMode) return;
    // These coordinates come from the selected city's existing API record.
    const lat = Number(city.latitude);
    const lng = Number(city.longitude);
    const radiusKm = Number(document.getElementById('radius-input').value);
    const isRadiusSearch = proximityMode === 'radius';
    const status = document.getElementById('proximity-status');
    status.classList.add('is-error');

    if (!Number.isFinite(lat) || !Number.isFinite(lng)) {
        status.textContent = `${city.name} has invalid coordinates in the API response.`;
        return;
    }
    if (isRadiusSearch && (!Number.isFinite(radiusKm) || radiusKm <= 0 || radiusKm > 20000)) {
        status.textContent = 'Enter a radius greater than 0 and no more than 20000 km.';
        return;
    }

    status.textContent = `Searching near ${city.name}…`;
    status.classList.remove('is-error');
    clearProximityResults();
    try {
        const response = await fetch(
            isRadiusSearch ? `${API_URL}cities/radius/` : `${API_URL}cities/nearest/`,
            {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(isRadiusSearch
                    ? { lat, lng, radius_km: radiusKm }
                    : { lat, lng })
            }
        );
        const data = await response.json();
        if (!response.ok) throw new Error(data.error || `Search failed (${response.status})`);

        searchMarker = L.marker([lat, lng]).addTo(map);
        const cities = isRadiusSearch ? data.cities : data.nearest_cities;
        const heading = isRadiusSearch
            ? `${data.total_found} cities within ${data.radius_km} km of ${city.name}`
            : `${data.total_found} nearest cities to ${city.name}`;
        showProximityResults(cities, heading);
        updateHeatmapForResults(cities, isRadiusSearch ? 'radius' : 'nearest');

        map.setView([lat, lng], Math.max(map.getZoom(), 6), { animate: false });

        if (isRadiusSearch) {
            radiusCircle = L.circle([lat, lng], {
                radius: radiusKm * 1000,
                color: '#198754',
                fillOpacity: 0.08
            }).addTo(map);
            map.fitBounds(radiusCircle.getBounds(), {
                padding: [30, 30],
                animate: false
            });
            map.setView([lat, lng], map.getZoom(), { animate: false });
            cities.forEach((result) => L.circleMarker([
                result.coordinates.lat, result.coordinates.lng
            ], { radius: 8, color: '#198754' })
                .bindTooltip(`${result.name} — ${result.distance_km} km`)
                .addTo(radiusLayer));
        } else {
            cities.forEach((result) => L.marker([
                result.coordinates.lat, result.coordinates.lng
            ], { icon: numberedIcon(result.rank) })
                .bindTooltip(`${result.rank}. ${result.name} — ${result.distance_km} km`)
                .addTo(proximityLayer));
        }
        status.textContent = 'Search complete.';
    } catch (error) {
        status.textContent = `Search failed: ${error.message}`;
        status.classList.add('is-error');
    }
}

function showProximityResults(cities, heading) {
    const results = document.getElementById('proximity-results');
    results.replaceChildren();
    const title = document.createElement('strong');
    title.textContent = heading;
    results.append(title);
    const list = document.createElement('ol');
    cities.forEach((city) => {
        const item = document.createElement('li');
        // Clicking a result zooms to that city's marker
        const button = document.createElement('button');
        button.type = 'button';
        button.className = 'proximity-result';
        button.textContent = `${city.name}, ${city.country} — ${city.distance_km} km`;
        button.addEventListener('click', () => goToCity(city.id));
        item.append(button);
        list.append(item);
    });
    results.append(list);
}

// Numbered badge placed up and right of the city dot so the dot stays clickable
function numberedIcon(rank) {
    return L.divIcon({
        className: 'nearest-rank-icon',
        html: `<span>${rank}</span>`,
        iconSize: [22, 22],
        iconAnchor: [-4, 26]
    });
}

function updateHeatmapForResults(cities, mode) {
    const heatData = cities
        .map(city => [city.coordinates.lat, city.coordinates.lng, 1])
        .filter(([lat, lng]) => Number.isFinite(lat) && Number.isFinite(lng));
    replaceHeatmap(heatData, mode);
}

function replaceHeatmap(heatData, mode) {
    if (heatLayer) map.removeLayer(heatLayer);
    const gradients = {
        default: { 0.2: '#0000ff', 0.5: '#00ffff', 0.75: '#ffff00', 1: '#ff0000' },
        nearest: { 0.2: '#00ffff', 0.5: '#00ff00', 0.75: '#ffff00', 1: '#ff7f00' },
        radius: { 0.2: '#00ff00', 0.5: '#ffff00', 0.75: '#ff7f00', 1: '#ff0000' }
    };
    heatLayer = L.heatLayer(heatData, {
        radius: 25,
        blur: 15,
        maxZoom: 10,
        minOpacity: 0.2,
        gradient: gradients[mode]
    }).addTo(map);
}

// Remove proximity overlays and restore the full-city heatmap
function clearProximityResults() {
    if (searchMarker) map.removeLayer(searchMarker);
    if (radiusCircle) map.removeLayer(radiusCircle);
    searchMarker = radiusCircle = null;
    proximityLayer?.clearLayers();
    radiusLayer?.clearLayers();
    document.getElementById('proximity-results').replaceChildren();
    const allCityHeat = citiesData
        .map(city => [Number(city.latitude), Number(city.longitude), 0.8])
        .filter(([lat, lng]) => Number.isFinite(lat) && Number.isFinite(lng));
    replaceHeatmap(allCityHeat, 'default');
}
