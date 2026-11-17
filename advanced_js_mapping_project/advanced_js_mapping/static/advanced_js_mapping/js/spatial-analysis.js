/**
 * Advanced JavaScript Mapping - Spatial Analysis Module
 * Handles API communication for polygon-based spatial queries
 */

(function(global) {
    'use strict';

    // Module namespace
    const SpatialAnalysis = {
        currentRequest: null,
        apiEndpoint: '/advanced-js-mapping/api/polygon-search/',

        /**
         * Initialize spatial analysis module
         */
        init() {
            console.log('🔬 Initializing spatial analysis module...');

            try {
                this.setupEventHandlers();
                console.log(' Spatial analysis module initialized successfully');
            } catch (error) {
                console.error(' Spatial analysis initialization failed:', error);
            }
        },

        /**
         * Setup event handlers
         */
        setupEventHandlers() {
            // Listen for drawing completion events
            document.addEventListener('drawingCompleted', (e) => {
                if (e.detail && e.detail.coordinates) {
                    this.searchByPolygon(e.detail.coordinates);
                }
            });
        },

        /**
         * Perform polygon-based spatial search
         */
        async searchByPolygon(coordinates) {
            console.log('🔍 Starting polygon search with', coordinates.length, 'coordinates');

            // Validate coordinates
            if (!this.validateCoordinates(coordinates)) {
                this.cancelCurrentRequest();
                this.handleError('Invalid coordinates provided for search.');
                return;
            }

            // Show loading state
            if (window.UIControls && window.UIControls.showLoading) {
                window.UIControls.showLoading('Searching for cities...');
            }

            if (this.currentRequest) {
                this.currentRequest.abort();
            }
            const request = new AbortController();
            this.currentRequest = request;

            try {

                const startTime = performance.now();

                // Make API request
                const response = await fetch(this.apiEndpoint, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': this.getCSRFToken()
                    },
                    body: JSON.stringify({
                        coordinates: coordinates
                    }),
                    signal: request.signal
                });

                const endTime = performance.now();
                const clientTime = Math.round(endTime - startTime);

                console.log(`⚡ API request completed in ${clientTime}ms`);

                // Handle response
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }

                const data = await response.json();

                if (this.currentRequest !== request) {
                    return;
                }

                // Validate response data
                if (!this.validateResponse(data)) {
                    throw new Error('Invalid response data received from server');
                }

                // Add client-side timing
                data.client_time_ms = clientTime;

                // Process successful response
                this.handleSuccess(data);

            } catch (error) {
                if (error.name === 'AbortError' || this.currentRequest !== request) {
                    console.log(' Request was cancelled');
                } else {
                    console.error(' Search failed:', error);
                    this.handleError(error.message || 'Search request failed');
                }
            } finally {
                if (this.currentRequest === request) {
                    if (window.UIControls && window.UIControls.hideLoading) {
                        window.UIControls.hideLoading();
                    }
                    this.currentRequest = null;
                }
            }
        },

        /**
         * Validate coordinates array
         */
        validateCoordinates(coordinates) {
            if (!Array.isArray(coordinates)) {
                console.error('❌ Coordinates must be an array');
                return false;
            }

            if (coordinates.length < 3) {
                console.error(' At least 3 coordinate pairs required for polygon');
                return false;
            }

            // Validate each coordinate pair
            for (let i = 0; i < coordinates.length; i++) {
                const coord = coordinates[i];

                if (!Array.isArray(coord) || coord.length !== 2) {
                    console.error(` Invalid coordinate at index ${i}:`, coord);
                    return false;
                }

                const [lng, lat] = coord;

                if (typeof lng !== 'number' || typeof lat !== 'number') {
                    console.error(` Coordinate values must be numbers at index ${i}:`, coord);
                    return false;
                }

                if (lng < -180 || lng > 180 || lat < -90 || lat > 90) {
                    console.error(` Coordinate out of bounds at index ${i}:`, coord);
                    return false;
                }
            }

            console.log(' Coordinates validation passed');
            return true;
        },

        /**
         * Validate API response
         */
        validateResponse(data) {
            if (!data || typeof data !== 'object') {
                console.error(' Response data is not an object');
                return false;
            }

            if (data.status !== 'success') {
                console.error(' API returned error status:', data.message || 'Unknown error');
                return false;
            }

            if (!Array.isArray(data.cities)) {
                console.error(' Response does not contain cities array');
                return false;
            }

            console.log(' Response validation passed');
            return true;
        },

        /**
         * Handle successful search response
         */
        handleSuccess(data) {
            console.log('🎉 Search completed successfully:', {
                cities_found: data.cities_found,
                total_population: data.total_population,
                query_time: data.query_time_ms + 'ms',
                client_time: data.client_time_ms + 'ms'
            });

            // Process city data for consistent formatting
            const processedCities = this.processCityData(data.cities);

            // Update response with processed data
            const processedData = {
                ...data,
                cities: processedCities
            };

            // Display results in UI
            if (window.UIControls && window.UIControls.displayResults) {
                window.UIControls.displayResults(processedData);
            }

            // Display results on map
            if (window.AdvancedMapping && window.AdvancedMapping.displayResults) {
                window.AdvancedMapping.displayResults(processedData);
            }

            // Show success notification
            if (window.UIControls && window.UIControls.showSuccess) {
                const message = `Found ${data.cities_found} cities in ${data.query_time_ms}ms`;
                window.UIControls.showSuccess(message);
            }

            // Dispatch custom event for other components
            document.dispatchEvent(new CustomEvent('searchCompleted', {
                detail: processedData
            }));
        },

        /**
         * Process city data for consistent formatting
         */
        processCityData(cities) {
            return cities.map(city => {
                // Ensure numeric values are properly parsed
                const processedCity = { ...city };

                // Convert string numbers to actual numbers
                if (typeof city.population === 'string') {
                    processedCity.population = parseFloat(city.population) || 0;
                }

                if (typeof city.gdp_per_capita === 'string') {
                    processedCity.gdp_per_capita = parseFloat(city.gdp_per_capita) || 0;
                }

                if (typeof city.latitude === 'string') {
                    processedCity.latitude = parseFloat(city.latitude) || null;
                }

                if (typeof city.longitude === 'string') {
                    processedCity.longitude = parseFloat(city.longitude) || null;
                }

                // Ensure required fields exist
                processedCity.name = city.name || 'Unknown';
                processedCity.country = city.country || 'Unknown';

                return processedCity;
            });
        },

        /**
         * Handle search errors
         */
        handleError(message) {
            console.error(' Spatial analysis error:', message);

            // Show error in UI
            if (window.UIControls && window.UIControls.showError) {
                window.UIControls.showError(message);
            }

            // Clear any partial results
            if (window.UIControls && window.UIControls.clearResults) {
                window.UIControls.clearResults();
            }

            // Dispatch error event
            document.dispatchEvent(new CustomEvent('searchError', {
                detail: { message }
            }));
        },

        /**
         * Get CSRF token for Django
         */
        getCSRFToken() {
            // Try to get from global variable first
            if (window.CSRF_TOKEN) {
                return window.CSRF_TOKEN;
            }

            // Try to get from cookie
            const name = 'csrftoken';
            let cookieValue = null;

            if (document.cookie && document.cookie !== '') {
                const cookies = document.cookie.split(';');
                for (let i = 0; i < cookies.length; i++) {
                    const cookie = cookies[i].trim();
                    if (cookie.substring(0, name.length + 1) === (name + '=')) {
                        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                        break;
                    }
                }
            }

            // Try to get from meta tag
            if (!cookieValue) {
                const csrfMeta = document.querySelector('meta[name=csrf-token]');
                if (csrfMeta) {
                    cookieValue = csrfMeta.getAttribute('content');
                }
            }

            return cookieValue || '';
        },

        /**
         * Cancel current search request
         */
        cancelCurrentRequest() {
            if (this.currentRequest) {
                this.currentRequest.abort();
                this.currentRequest = null;
                if (window.UIControls && window.UIControls.hideLoading) {
                    window.UIControls.hideLoading();
                }
                console.log('🚫 Cancelled current search request');
            }
        },

        /**
         * Get search statistics
         */
        getSearchStatistics() {
            // Could implement caching and statistics tracking here
            return {
                totalSearches: 0,
                averageResponseTime: 0,
                totalCitiesFound: 0
            };
        }
    };

    // Expose module globally
    global.SpatialAnalysis = SpatialAnalysis;

})(window);
