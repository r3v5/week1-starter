# cities/models.py
from django.contrib.gis.db import models
from django.contrib.gis.geos import Point

class City(models.Model):
    CITY_TYPE_CHOICES = [
        ('capital', 'Capital City'),
        ('major', 'Major City'),
        ('regional', 'Regional City'),
        ('town', 'Town'),
    ]

    # Basic information
    name = models.CharField(max_length=100)
    country = models.CharField(max_length=100)
    population = models.IntegerField()

    # Geographic data
    latitude = models.FloatField()
    longitude = models.FloatField()
    location = models.PointField(srid=4326)
    elevation = models.IntegerField(null=True, blank=True)

    # City characteristics
    city_type = models.CharField(max_length=20, choices=CITY_TYPE_CHOICES, default='town')
    urban_area_km2 = models.FloatField(null=True, blank=True)
    population_density = models.FloatField(null=True, blank=True)

    # Economic data
    gdp_per_capita = models.IntegerField(null=True, blank=True)
    unemployment_rate = models.FloatField(null=True, blank=True)

    # Environmental data
    green_space_percentage = models.FloatField(null=True, blank=True)

    # Administrative data - ADD THESE MISSING FIELDS
    region_code = models.CharField(max_length=10, blank=True, null=True)

    # Metadata - ADD THESE MISSING FIELDS  
    population_year = models.IntegerField(null=True, blank=True)
    data_source = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    #updated_at = models.DateTimeField(auto_now=True)
    last_updated = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        # Automatically create Point from lat/lng
        if self.latitude is not None and self.longitude is not None:
            self.location = Point(float(self.longitude), float(self.latitude), srid=4326)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name}, {self.country}"

    class Meta:
        db_table = 'cities_city'
        unique_together = ['name', 'country']
        indexes = [
            models.Index(fields=['country']),
            models.Index(fields=['city_type']),
            models.Index(fields=['population']),
        ]