// Replace addMarkersToMap with clustered version
// Store cities data and markers
console.log('map.js loaded');
let citiesData = [];
let markers = {};
let cityCount = 0;
let map = null;

// API endpoint
const API_URL = '/api/';

// Initialize the map
async function initMap() {
    // Initialize Leaflet map centered on Dublin
    map = L.map('map').setView([53.3498, -6.2603], 6);

    // Add OpenStreetMap tile layer
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors',
        maxZoom: 19,
        minZoom: 2
    }).addTo(map);

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
        map.setView([53.3498, -6.2603], 6);
        document.getElementById('searchInput').value = '';
        document.getElementById('results').innerHTML = '';
        addMarkersToMap(citiesData);
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


function addHeatmapLayer(cities) {
    const heatData = cities.map(city => [
        parseFloat(city.latitude),
        parseFloat(city.longitude),
        0.8  // Intensity
    ]);

    L.heatLayer(heatData, {
        radius: 25,
        blur: 15,
        maxZoom: 1,
        minOpacity: 0.2
    }).addTo(map);
}