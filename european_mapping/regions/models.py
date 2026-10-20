from django.contrib.gis.db import models
from django.contrib.gis.geos import GEOSGeometry
from django.core.validators import MinValueValidator, MaxValueValidator

class Region(models.Model):
    # Basic Information
    name = models.CharField(max_length=100, db_index=True)
    country = models.CharField(max_length=100, db_index=True)
    region_code = models.CharField(max_length=10, unique=True)
    region_type = models.CharField(max_length=50, choices=[
        ('country', 'Country'),
        ('state', 'State/Province'),
        ('county', 'County'),
        ('municipality', 'Municipality'),
        ('district', 'District'),
    ])

    # Geographic Data
    geometry = models.MultiPolygonField(srid=4326)
    centroid = models.PointField(srid=4326, null=True, blank=True)
    area_km2 = models.FloatField(validators=[MinValueValidator(0)])
    perimeter_km = models.FloatField(null=True, blank=True)

    # Population Data
    total_population = models.IntegerField(validators=[MinValueValidator(0)])
    population_year = models.IntegerField(default=2023)
    population_density = models.FloatField()  # people per km²
    urban_population_pct = models.FloatField(
        null=True, blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )

    # Economic Indicators
    gdp_total = models.FloatField(null=True, blank=True)  # Million EUR
    gdp_per_capita = models.FloatField(null=True, blank=True)  # EUR
    unemployment_rate = models.FloatField(
        null=True, blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )

    # Land Use Data
    agricultural_area_pct = models.FloatField(
        null=True, blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    forest_area_pct = models.FloatField(
        null=True, blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    urban_area_pct = models.FloatField(
        null=True, blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )

    # Administrative Hierarchy
    parent_region = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True)
    admin_level = models.IntegerField(default=1)  # 1=country, 2=state, 3=county, etc.

    # Metadata
    data_source = models.CharField(max_length=200, blank=True)
    last_updated = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        # Calculate area from geometry if not provided
        if self.geometry and not self.area_km2:
            # Transform to equal-area projection for accurate area calculation
            geom_transformed = self.geometry.transform(3857, clone=True)  # Web Mercator
            self.area_km2 = geom_transformed.area / 1000000  # Convert m² to km²

        # Calculate population density
        if self.total_population and self.area_km2:
            self.population_density = self.total_population / self.area_km2

        # Calculate centroid
        if self.geometry:
            self.centroid = self.geometry.centroid

        super().save(*args, **kwargs)

    @property
    def cities_count(self):
        """Count cities within this region"""
        from cities.models import City
        return City.objects.filter(location__within=self.geometry).count()

    def __str__(self):
        return f"{self.name} ({self.region_type}) - {self.total_population:,}"

    class Meta:
        db_table = 'regions_region'
        unique_together = ['name', 'country', 'region_type']
        indexes = [
            models.Index(fields=['country']),
            models.Index(fields=['region_type']),
            models.Index(fields=['total_population']),
            models.Index(fields=['area_km2']),
        ]