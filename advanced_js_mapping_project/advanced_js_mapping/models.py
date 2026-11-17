from django.contrib.gis.db import models
from django.utils import timezone

class AdvancedCity(models.Model):
    """
    Enhanced city model with spatial capabilities for advanced mapping applications.
    Stores comprehensive city data including geographic location, demographics, and economic indicators.
    """

    # Basic Information
    name = models.CharField(max_length=100, help_text="Official city name")
    country = models.CharField(max_length=100, help_text="Country where the city is located")
    region = models.CharField(max_length=100, blank=True, null=True, help_text="State, province, or administrative region")

    # Geographic Data
    location = models.PointField(srid=4326, help_text="Geographic coordinates (longitude, latitude)")
    elevation_m = models.FloatField(blank=True, null=True, help_text="Elevation above sea level in meters")
    area_km2 = models.FloatField(blank=True, null=True, help_text="City area in square kilometers")

    # Demographic Data
    population = models.BigIntegerField(help_text="Current population count")
    population_year = models.IntegerField(default=2024, help_text="Year of population data")
    population_density = models.FloatField(blank=True, null=True, help_text="Population per square kilometer")

    # Economic Indicators
    gdp_per_capita = models.FloatField(blank=True, null=True, help_text="GDP per capita in USD")
    gdp_year = models.IntegerField(blank=True, null=True, help_text="Year of GDP data")
    unemployment_rate = models.FloatField(blank=True, null=True, help_text="Unemployment rate as percentage")

    # Classification
    city_type = models.CharField(
        max_length=50, 
        choices=[
            ('capital', 'Capital City'),
            ('major', 'Major City'),
            ('metropolitan', 'Metropolitan Area'),
            ('urban', 'Urban Center'),
            ('town', 'Town'),
            ('other', 'Other')
        ],
        default='other',
        help_text="Classification of the city"
    )

    # Administrative
    is_active = models.BooleanField(default=True, help_text="Whether this city is actively tracked")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Additional Data
    timezone_name = models.CharField(max_length=100, blank=True, null=True, help_text="IANA timezone identifier")
    climate_zone = models.CharField(max_length=50, blank=True, null=True, help_text="Köppen climate classification")

    class Meta:
        db_table = 'advanced_js_mapping_advancedcity'
        verbose_name = 'Advanced City'
        verbose_name_plural = 'Advanced Cities'
        ordering = ['-population']  # Order by population (largest first)
        indexes = [
            models.Index(fields=['country', 'name']),
            models.Index(fields=['population']),
            models.Index(fields=['city_type']),
        ]

    def __str__(self):
        return f"{self.name}, {self.country} (Pop: {self.population:,})"

    @property
    def latitude(self):
        """Get latitude from the location point."""
        return self.location.y if self.location else None

    @property
    def longitude(self):
        """Get longitude from the location point."""
        return self.location.x if self.location else None

    @property
    def coordinates(self):
        """Get coordinates as [longitude, latitude] for GeoJSON compatibility."""
        if self.location:
            return [self.location.x, self.location.y]
        return None

    def to_geojson_feature(self):
        """Convert city to GeoJSON feature format."""
        return {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": self.coordinates
            },
            "properties": {
                "id": self.id,
                "name": self.name,
                "country": self.country,
                "region": self.region,
                "population": self.population,
                "gdp_per_capita": self.gdp_per_capita,
                "city_type": self.city_type,
                "elevation_m": self.elevation_m,
                "area_km2": self.area_km2,
                "population_density": self.population_density,
                "timezone": self.timezone_name,
                "climate_zone": self.climate_zone
            }
        }

    def distance_to_point(self, longitude, latitude):
        """Calculate distance to a given point in kilometers."""
        from django.contrib.gis.geos import Point
        from django.contrib.gis.measure import Distance

        if not self.location:
            return None

        target_point = Point(longitude, latitude, srid=4326)
        return self.location.distance(target_point) * 111  # Approximate km conversion


class PolygonAnalysis(models.Model):
    """
    Track polygon-based spatial analysis operations for performance monitoring and analytics.
    Stores metadata about each polygon search including timing, results, and user context.
    """

    # Analysis Metadata
    analysis_timestamp = models.DateTimeField(default=timezone.now, help_text="When the analysis was performed")
    session_id = models.CharField(max_length=100, blank=True, null=True, help_text="User session identifier")
    user_agent = models.TextField(blank=True, null=True, help_text="Browser user agent string")
    ip_address = models.GenericIPAddressField(blank=True, null=True, help_text="Client IP address")

    # Polygon Data
    polygon_coordinates = models.JSONField(help_text="Polygon coordinates as GeoJSON")
    polygon_area_km2 = models.FloatField(blank=True, null=True, help_text="Calculated polygon area in km²")
    area_analyzed_km2 = models.FloatField(blank=True, null=True, help_text="Actual analyzed area (may differ from polygon)")

    # Results
    cities_count = models.IntegerField(help_text="Number of cities found within the polygon")
    cities_found = models.JSONField(blank=True, null=True, help_text="List of city IDs found")
    total_population = models.BigIntegerField(blank=True, null=True, help_text="Sum of population in found cities")
    average_gdp = models.FloatField(blank=True, null=True, help_text="Average GDP per capita of found cities")

    # Performance Metrics
    query_duration_ms = models.IntegerField(blank=True, null=True, help_text="Query execution time in milliseconds")
    database_hits = models.IntegerField(default=1, help_text="Number of database queries executed")
    cache_used = models.BooleanField(default=False, help_text="Whether cached results were used")

    # Geographic Context
    centroid_latitude = models.FloatField(blank=True, null=True, help_text="Polygon centroid latitude")
    centroid_longitude = models.FloatField(blank=True, null=True, help_text="Polygon centroid longitude")
    bounding_box = models.JSONField(blank=True, null=True, help_text="Polygon bounding box coordinates")

    # Analysis Type
    analysis_type = models.CharField(
        max_length=50,
        choices=[
            ('polygon', 'Polygon Search'),
            ('rectangle', 'Rectangle Search'),
            ('circle', 'Circle Search'),
            ('custom', 'Custom Geometry')
        ],
        default='polygon',
        help_text="Type of spatial analysis performed"
    )

    class Meta:
        db_table = 'advanced_js_mapping_polygonanalysis'
        verbose_name = 'Polygon Analysis'
        verbose_name_plural = 'Polygon Analyses'
        ordering = ['-analysis_timestamp']
        indexes = [
            models.Index(fields=['analysis_timestamp']),
            models.Index(fields=['cities_count']),
            models.Index(fields=['session_id']),
        ]

    def __str__(self):
        return f"Analysis {self.id}: {self.cities_count} cities found on {self.analysis_timestamp.date()}"

    @property
    def efficiency_score(self):
        """Calculate efficiency score based on query time and results."""
        if not self.query_duration_ms or self.cities_count == 0:
            return 0
        return min(100, max(0, 100 - (self.query_duration_ms / 10)))

    def get_performance_category(self):
        """Categorize performance based on query duration."""
        if not self.query_duration_ms:
            return 'unknown'
        elif self.query_duration_ms < 100:
            return 'excellent'
        elif self.query_duration_ms < 500:
            return 'good'
        elif self.query_duration_ms < 1000:
            return 'acceptable'
        else:
            return 'slow'


class SearchSession(models.Model):
    """
    Track user sessions for analytics and user experience optimization.
    Aggregates multiple polygon analyses within a single user session.
    """

    session_id = models.CharField(max_length=100, unique=True, help_text="Unique session identifier")
    start_timestamp = models.DateTimeField(default=timezone.now, help_text="Session start time")
    end_timestamp = models.DateTimeField(blank=True, null=True, help_text="Session end time")

    # User Context
    user_agent = models.TextField(blank=True, null=True, help_text="Browser user agent")
    ip_address = models.GenericIPAddressField(blank=True, null=True, help_text="Client IP address")
    referrer_url = models.URLField(blank=True, null=True, help_text="Referring website")

    # Session Metrics
    total_analyses = models.IntegerField(default=0, help_text="Number of analyses in this session")
    total_cities_found = models.IntegerField(default=0, help_text="Total cities found across all analyses")
    average_query_time = models.FloatField(blank=True, null=True, help_text="Average query time in milliseconds")

    # Geographic Coverage
    unique_countries = models.IntegerField(default=0, help_text="Number of unique countries analyzed")
    total_area_analyzed = models.FloatField(blank=True, null=True, help_text="Total area analyzed in km²")

    # Session Quality
    completion_rate = models.FloatField(blank=True, null=True, help_text="Percentage of successful analyses")
    engagement_score = models.FloatField(blank=True, null=True, help_text="User engagement score (0-100)")

    class Meta:
        db_table = 'advanced_js_mapping_searchsession'
        verbose_name = 'Search Session'
        verbose_name_plural = 'Search Sessions'
        ordering = ['-start_timestamp']

    def __str__(self):
        duration = self.duration_minutes
        return f"Session {self.session_id[:8]}: {self.total_analyses} analyses in {duration:.1f}min"

    @property
    def duration_minutes(self):
        """Calculate session duration in minutes."""
        if self.end_timestamp:
            delta = self.end_timestamp - self.start_timestamp
            return delta.total_seconds() / 60
        else:
            delta = timezone.now() - self.start_timestamp
            return delta.total_seconds() / 60

    @property
    def is_active(self):
        """Check if session is still active (no end timestamp and recent activity)."""
        if self.end_timestamp:
            return False
        return self.duration_minutes < 60  # Consider active if less than 1 hour

    def update_metrics(self):
        """Update session metrics based on associated polygon analyses."""
        analyses = PolygonAnalysis.objects.filter(session_id=self.session_id)

        self.total_analyses = analyses.count()
        self.total_cities_found = sum(a.cities_count for a in analyses)

        query_times = [a.query_duration_ms for a in analyses if a.query_duration_ms]
        if query_times:
            self.average_query_time = sum(query_times) / len(query_times)

        # Calculate unique countries (requires joining with AdvancedCity)
        cities_found = []
        for analysis in analyses:
            if analysis.cities_found:
                cities_found.extend(analysis.cities_found)

        if cities_found:
            countries = set()
            for city_id in cities_found:
                try:
                    city = AdvancedCity.objects.get(id=city_id)
                    countries.add(city.country)
                except AdvancedCity.DoesNotExist:
                    continue
            self.unique_countries = len(countries)

        self.save()
