from django.db import models
from django.contrib.gis.db import models as gis_models
from django.contrib.gis.geos import Point, LineString, Polygon

# Note: Django automatically creates spatial GIST indexes for all geometry fields,
# so we don't need to manually declare them in the Meta class.

class DublinAdminArea(gis_models.Model):
    """Administrative areas and districts in Dublin"""

    area_name = models.CharField(max_length=100)
    area_type = models.CharField(
        max_length=50,
        choices=[
            ('city_center', 'City Center'),
            ('cultural_quarter', 'Cultural Quarter'),
            ('residential', 'Residential'),
            ('business', 'Business District'),
            ('recreational', 'Recreational'),
        ]
    )
    population = models.IntegerField(null=True, blank=True)
    area_km2 = models.DecimalField(max_digits=10, decimal_places=2)

    # Geometry field for polygon boundaries
    geom = gis_models.PolygonField(srid=4326, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Dublin Admin Areas"

    def __str__(self):
        return f"{self.area_name} ({self.area_type})"


class DublinRoad(gis_models.Model):
    """Road network in Dublin"""

    ROAD_TYPES = [
        ('motorway', 'Motorway'),
        ('main_street', 'Main Street'),
        ('secondary', 'Secondary Road'),
        ('tertiary', 'Tertiary Road'),
        ('pedestrian', 'Pedestrian Street'),
        ('residential', 'Residential Street'),
    ]

    road_name = models.CharField(max_length=100)
    road_type = models.CharField(max_length=20, choices=ROAD_TYPES)
    speed_limit = models.IntegerField()  # km/h
    length_meters = models.DecimalField(max_digits=10, decimal_places=2)

    # Geometry field for line geometry
    geom = gis_models.LineStringField(srid=4326, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Dublin Roads"

    def __str__(self):
        return f"{self.road_name} ({self.road_type})"


class DublinPOI(gis_models.Model):
    """Points of Interest in Dublin"""

    POI_TYPES = [
        ('landmark', 'Landmark'),
        ('amenity', 'Amenity'),
        ('transport', 'Transport Hub'),
        ('attraction', 'Tourist Attraction'),
        ('entertainment', 'Entertainment'),
        ('commercial', 'Commercial'),
        ('education', 'Education'),
        ('historic', 'Historic Site'),
    ]

    poi_name = models.CharField(max_length=100)
    poi_type = models.CharField(max_length=20, choices=POI_TYPES)
    description = models.TextField(blank=True)
    visitors_per_day = models.IntegerField(null=True, blank=True)
    rating = models.DecimalField(max_digits=3, decimal_places=2, null=True, blank=True)

    # Geometry field for point location
    geom = gis_models.PointField(srid=4326, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Dublin POI"
        verbose_name_plural = "Dublin POIs"

    def __str__(self):
        return f"{self.poi_name} ({self.poi_type})"


class LandUseZone(gis_models.Model):
    """Land use zoning in Dublin"""

    ZONE_TYPES = [
        ('residential', 'Residential'),
        ('commercial', 'Commercial'),
        ('industrial', 'Industrial'),
        ('recreational', 'Recreational'),
        ('mixed_use', 'Mixed Use'),
        ('protected', 'Protected Area'),
    ]

    zone_name = models.CharField(max_length=100)
    zone_type = models.CharField(max_length=20, choices=ZONE_TYPES)
    zoning_code = models.CharField(max_length=20, unique=True)
    permitted_uses = models.TextField()  # Comma-separated or formatted text

    # Geometry field for zone polygon
    geom = gis_models.PolygonField(srid=4326, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Land Use Zone"
        verbose_name_plural = "Land Use Zones"

    def __str__(self):
        return f"{self.zone_name} ({self.zone_type})"