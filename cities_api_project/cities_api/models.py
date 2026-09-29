from django.contrib.gis.db import models
from django.contrib.gis.geos import Point
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone

class CityManager(models.Manager):
    """Custom manager for City model with spatial queries"""

    def capitals(self):
        """Return only capital cities"""
        return self.filter(is_capital=True)

    def by_country(self, country_name):
        """Filter cities by country"""
        return self.filter(country__icontains=country_name)

    def large_cities(self, min_population=1000000):
        """Return cities above population threshold"""
        return self.filter(population__gte=min_population)

    def within_radius(self, point, radius_km):
        """Find cities within radius of a point"""
        from django.contrib.gis.measure import Distance
        return self.filter(
            location__distance_lte=(point, Distance(km=radius_km))
        )

    def in_bounding_box(self, bbox):
        """Find cities within bounding box [min_lon, min_lat, max_lon, max_lat]"""
        from django.contrib.gis.geos import Polygon

        min_lon, min_lat, max_lon, max_lat = bbox
        bbox_polygon = Polygon.from_bbox((min_lon, min_lat, max_lon, max_lat))
        return self.filter(location__within=bbox_polygon)


class City(models.Model):
    """
    Comprehensive city model with spatial capabilities
    """
    # Basic information
    name = models.CharField(max_length=200, db_index=True)
    country = models.CharField(max_length=100, db_index=True)
    region = models.CharField(max_length=200, blank=True)

    # Demographics
    population = models.PositiveIntegerField()

    # Geographic information
    location = models.PointField(srid=4326, help_text="City center coordinates")
    elevation_m = models.IntegerField(
        null=True,
        blank=True,
        help_text="Elevation above sea level in meters"
    )

    # Historical data
    founded_year = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(-4000), MaxValueValidator(2025)]
    )

    # Administrative
    is_capital = models.BooleanField(default=False)
    timezone = models.CharField(max_length=50, blank=True)

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = CityManager()

    class Meta:
        verbose_name = "City"
        verbose_name_plural = "Cities"
        ordering = ['-population', 'name']
        indexes = [
            models.Index(fields=['country', 'population']),
            models.Index(fields=['is_capital']),
            models.Index(fields=['population']),
        ]

    def __str__(self):
        return f"{self.name}, {self.country}"

    @property
    def latitude(self):
        """Return latitude coordinate"""
        return self.location.y if self.location else None

    @property
    def longitude(self):
        """Return longitude coordinate"""
        return self.location.x if self.location else None

    @property
    def coordinates(self):
        """Return coordinates as [longitude, latitude] for GeoJSON"""
        return [self.longitude, self.latitude] if self.location else None

    @property
    def population_category(self):
        """Categorize city by population size"""
        if self.population >= 10000000:
            return "Megacity"
        elif self.population >= 5000000:
            return "Large Metropolis"
        elif self.population >= 1000000:
            return "Metropolis"
        elif self.population >= 500000:
            return "Large City"
        elif self.population >= 100000:
            return "City"
        else:
            return "Town"

    @property
    def age_years(self):
        """Calculate city age in years"""
        if self.founded_year:
            current_year = timezone.now().year
            return current_year - self.founded_year
        return None
