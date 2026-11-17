/**
 * Advanced JavaScript Mapping - Map Interface Module
 * Handles Leaflet map initialization, drawing tools, and core mapping functionality
 */

(function(global) {
    'use strict';

    // Module namespace
    const AdvancedMapping = {
        map: null,
        drawControl: null,
        drawnItems: null,
        markersLayer: null,
        currentResults: null,

        // Configuration
        config: {
            initialView: [54.5, 15.0],
            initialZoom: 4,
            maxZoom: 18,
            minZoom: 2
        },

        /**
         * Initialize the mapping application
         */
        init() {
            console.log(' Initializing map interface...');

            try {
                this.setupConfig();
                this.initializeMap();
                this.setupDrawingTools();
                this.setupEventHandlers();
                this.loadInitialData();

                console.log(' Map interface initialized successfully');
            } catch (error) {
                console.error(' Map initialization failed:', error);
                if (window.UIControls) {
                    window.UIControls.showError('Failed to initialize map. Check the browser console and CDN connection.');
                }
            }
        },

        /**
         * Setup configuration from global variables
         */
        setupConfig() {
            if (window.MAP_CONFIG) {
                this.config = { ...this.config, ...window.MAP_CONFIG };
            }
        },

        /**
         * Initialize the Leaflet map
         */
        initializeMap() {
            // Initialize map
            this.map = L.map('map', {
                center: this.config.initialView,
                zoom: this.config.initialZoom,
                maxZoom: this.config.maxZoom,
                minZoom: this.config.minZoom,
                zoomControl: true,
                attributionControl: true
            });

            // Add tile layers
            this.addTileLayers();

            // Initialize layer groups
            this.drawnItems = new L.FeatureGroup();
            this.markersLayer = new L.FeatureGroup();

            this.map.addLayer(this.drawnItems);
            this.map.addLayer(this.markersLayer);

            // Add scale control
            L.control.scale({
                position: 'bottomleft',
                imperial: false
            }).addTo(this.map);

            console.log('📍 Map initialized with center:', this.config.initialView);
        },

        /**
         * Add tile layer options
         */
        addTileLayers() {
            L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                attribution: '&copy; OpenStreetMap contributors',
                maxZoom: 19
            }).addTo(this.map);
        },

        /**
         * Setup drawing tools and controls
         */
        setupDrawingTools() {
            if (typeof L.Control.Draw !== 'undefined') {
                this.setupLeafletDraw();
            } else {
                throw new Error('Leaflet.draw could not be loaded');
            }
        },

        /**
         * Setup Leaflet.draw controls
         */
        setupLeafletDraw() {
            // Drawing options
            const drawOptions = {
                draw: {
                    polygon: {
                        allowIntersection: false,
                        drawError: {
                            color: '#e1e100',
                            message: '<strong>Error:</strong> Shape edges cannot cross!'
                        },
                        shapeOptions: {
                            color: '#2563eb',
                            fillOpacity: 0.3,
                            weight: 3
                        }
                    },
                    rectangle: {
                        shapeOptions: {
                            color: '#16a34a',
                            fillOpacity: 0.3,
                            weight: 3
                        }
                    },
                    circle: false,
                    marker: false,
                    polyline: false,  // Disable polyline
                    circlemarker: false  // Disable circle marker
                },
                edit: {
                    featureGroup: this.drawnItems,
                    remove: true
                }
            };

            // Add draw control
            this.drawControl = new L.Control.Draw(drawOptions);
            this.map.addControl(this.drawControl);

            console.log(' Leaflet.draw controls added');
        },

        setupEventHandlers() {
            this.map.on(L.Draw.Event.CREATED, event => {
                this.drawnItems.clearLayers();
                this.drawnItems.addLayer(event.layer);
                this.searchLayer(event.layer);
            });
            this.map.on(L.Draw.Event.EDITED, event => {
                event.layers.eachLayer(layer => this.searchLayer(layer));
            });
            this.map.on(L.Draw.Event.DELETED, () => this.clearResults());
        },

        searchLayer(layer) {
            const coordinates = layer.toGeoJSON().geometry.coordinates[0];
            document.dispatchEvent(new CustomEvent('drawingCompleted', {
                detail: { coordinates }
            }));
        },

        loadInitialData() {
            const features = window.INITIAL_CITIES?.features || [];
            features.forEach(feature => {
                const [longitude, latitude] = feature.geometry.coordinates;
                const city = { ...feature.properties, latitude, longitude };
                L.marker([latitude, longitude], { icon: this.createCityIcon(city) })
                    .bindPopup(this.createCityPopupContent(city))
                    .addTo(this.markersLayer);
            });
        },

        /**
         * Display search results on the map
         */
        displayResults(results) {
            console.log(' Displaying', results.cities.length, 'cities on map');

            // Clear existing markers
            this.markersLayer.clearLayers();

            // Store current results
            this.currentResults = results;

            // Create markers for each city
            results.cities.forEach(city => {
                if (city.latitude != null && city.longitude != null) {
                    const marker = L.marker([city.latitude, city.longitude], {
                        icon: this.createCityIcon(city)
                    }).addTo(this.markersLayer);

                    // Create popup content
                    const popupContent = this.createCityPopupContent(city);
                    marker.bindPopup(popupContent);
                }
            });

            // Fit map to show all results if there are any
            if (results.cities.length > 0) {
                const group = new L.featureGroup([this.markersLayer, this.drawnItems]);
                this.map.fitBounds(group.getBounds().pad(0.1));
            }
        },

        /**
         * Create custom icon for city markers
         */
        createCityIcon(city) {
            // Color based on population
            let color = '#dc2626';  // Red for small cities
            if (city.population > 1000000) {
                color = '#7c3aed';  // Purple for megacities
            } else if (city.population > 500000) {
                color = '#2563eb';  // Blue for large cities
            } else if (city.population > 100000) {
                color = '#16a34a';  // Green for medium cities
            }

            return L.divIcon({
                className: 'city-marker',
                html: `<div style="
                    background-color: ${color};
                    width: 12px;
                    height: 12px;
                    border-radius: 50%;
                    border: 2px solid white;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.3);
                "></div>`,
                iconSize: [16, 16],
                iconAnchor: [8, 8]
            });
        },

        /**
         * Create popup content for city markers
         */
        createCityPopupContent(city) {
            const population = city.population ? city.population.toLocaleString() : 'Unknown';
            const gdp = city.gdp_per_capita ? `$${parseFloat(city.gdp_per_capita).toLocaleString()}` : 'N/A';

            return `
                <div class="city-popup">
                    <h6 class="mb-2">
                        <i class="fas fa-city me-1"></i>
                        ${city.name}
                    </h6>
                    <table class="table table-sm table-borderless mb-0">
                        <tr>
                            <td><i class="fas fa-flag me-1"></i> Country:</td>
                            <td><strong>${city.country}</strong></td>
                        </tr>
                        <tr>
                            <td><i class="fas fa-users me-1"></i> Population:</td>
                            <td><strong>${population}</strong></td>
                        </tr>
                        <tr>
                            <td><i class="fas fa-dollar-sign me-1"></i> GDP/Capita:</td>
                            <td><strong>${gdp}</strong></td>
                        </tr>
                    </table>
                </div>
            `;
        },

        /**
         * Clear all drawings and results
         */
        clearAll() {
            this.drawnItems.clearLayers();
            this.markersLayer.clearLayers();
            this.clearResults();
            console.log('🧹 Cleared all drawings and results');
        },

        /**
         * Reset map to initial view
         */
        resetView() {
            this.map.setView(this.config.initialView, this.config.initialZoom, {
                animate: true,
                duration: 1.5
            });
            console.log('🔄 Reset to initial view');
        },

        /**
         * Clear search results
         */
        clearResults() {
            if (window.SpatialAnalysis) {
                window.SpatialAnalysis.cancelCurrentRequest();
            }
            this.markersLayer.clearLayers();
            this.currentResults = null;

            // Update UI
            if (window.UIControls && window.UIControls.clearResults) {
                window.UIControls.clearResults();
            }
        },

        /**
         * Export current results
         */
        exportResults() {
            if (!this.currentResults || this.currentResults.cities.length === 0) {
                alert('No results to export. Please search for cities first.');
                return;
            }

            // Create CSV content
            const csvContent = this.createCSVExport(this.currentResults.cities);

            // Download CSV file
            const blob = new Blob([csvContent], { type: 'text/csv' });
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `city_search_results_${new Date().toISOString().slice(0,10)}.csv`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);

            console.log(' Exported', this.currentResults.cities.length, 'cities to CSV');
        },

        /**
         * Create CSV content from cities data
         */
        createCSVExport(cities) {
            const headers = ['Name', 'Country', 'Population', 'GDP per Capita', 'Latitude', 'Longitude'];
            const csvRows = [headers.join(',')];

            cities.forEach(city => {
                const row = [
                    `"${city.name || ''}"`,
                    `"${city.country || ''}"`,
                    city.population || '',
                    city.gdp_per_capita || '',
                    city.latitude || '',
                    city.longitude || ''
                ];
                csvRows.push(row.join(','));
            });

            return csvRows.join('\n');
        }
    };

    // Expose module globally
    global.AdvancedMapping = AdvancedMapping;

})(window);
