from rest_framework import serializers
from rest_framework_gis.serializers import GeoFeatureModelSerializer
from .models import City

class CityListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for city lists"""

    latitude = serializers.ReadOnlyField()
    longitude = serializers.ReadOnlyField()
    population_category = serializers.ReadOnlyField()

    class Meta:
        model = City
        fields = [
            'id', 'name', 'country', 'population',
            'latitude', 'longitude', 'is_capital',
            'population_category'
        ]

class CityDetailSerializer(serializers.ModelSerializer):
    """Comprehensive serializer for city details"""

    latitude = serializers.ReadOnlyField()
    longitude = serializers.ReadOnlyField()
    coordinates = serializers.ReadOnlyField()
    population_category = serializers.ReadOnlyField()
    age_years = serializers.ReadOnlyField()

    class Meta:
        model = City
        fields = [
            'id', 'name', 'country', 'region', 'population',
            'latitude', 'longitude', 'coordinates',
            'elevation_m', 'founded_year', 'age_years',
            'is_capital', 'timezone', 'population_category',
            'created_at', 'updated_at'
        ]

class CityGeoJSONSerializer(GeoFeatureModelSerializer):
    """GeoJSON serializer for mapping applications"""

    population_category = serializers.ReadOnlyField()
    age_years = serializers.ReadOnlyField()

    class Meta:
        model = City
        geo_field = 'location'
        fields = [
            'id', 'name', 'country', 'region', 'population',
            'elevation_m', 'founded_year', 'age_years',
            'is_capital', 'timezone', 'population_category'
        ]

class CityCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating new cities"""

    latitude = serializers.FloatField(write_only=True)
    longitude = serializers.FloatField(write_only=True)

    class Meta:
        model = City
        fields = [
            'name', 'country', 'region', 'population',
            'latitude', 'longitude', 'elevation_m',
            'founded_year', 'is_capital', 'timezone'
        ]

    def validate_latitude(self, value):
        """Validate latitude range"""
        if not -90 <= value <= 90:
            raise serializers.ValidationError("Latitude must be between -90 and 90")
        return value

    def validate_longitude(self, value):
        """Validate longitude range"""
        if not -180 <= value <= 180:
            raise serializers.ValidationError("Longitude must be between -180 and 180")
        return value

    def create(self, validated_data):
        """Create city with Point geometry from lat/lon"""
        from django.contrib.gis.geos import Point

        latitude = validated_data.pop('latitude')
        longitude = validated_data.pop('longitude')
        validated_data['location'] = Point(longitude, latitude, srid=4326)

        return super().create(validated_data)

class CitySummarySerializer(serializers.Serializer):
    """Serializer for API statistics"""

    total_cities = serializers.IntegerField()
    total_population = serializers.IntegerField()
    countries_count = serializers.IntegerField()
    capitals_count = serializers.IntegerField()
    average_population = serializers.FloatField()
    largest_city = serializers.CharField()
    smallest_city = serializers.CharField()

class DistanceSerializer(serializers.Serializer):
    """Serializer for distance-based queries"""

    latitude = serializers.FloatField()
    longitude = serializers.FloatField()
    radius_km = serializers.FloatField(min_value=0.1, max_value=20000)

    def validate_latitude(self, value):
        if not -90 <= value <= 90:
            raise serializers.ValidationError("Latitude must be between -90 and 90")
        return value

    def validate_longitude(self, value):
        if not -180 <= value <= 180:
            raise serializers.ValidationError("Longitude must be between -180 and 180")
        return value

class BoundingBoxSerializer(serializers.Serializer):
    """Serializer for bounding box queries"""

    min_longitude = serializers.FloatField()
    min_latitude = serializers.FloatField()
    max_longitude = serializers.FloatField()
    max_latitude = serializers.FloatField()

    def validate(self, data):
        """Validate bounding box coordinates"""
        if data['min_longitude'] >= data['max_longitude']:
            raise serializers.ValidationError("min_longitude must be less than max_longitude")

        if data['min_latitude'] >= data['max_latitude']:
            raise serializers.ValidationError("min_latitude must be less than max_latitude")

        # Validate coordinate ranges
        for coord in ['min_longitude', 'max_longitude']:
            if not -180 <= data[coord] <= 180:
                raise serializers.ValidationError(f"{coord} must be between -180 and 180")

        for coord in ['min_latitude', 'max_latitude']:
            if not -90 <= data[coord] <= 90:
                raise serializers.ValidationError(f"{coord} must be between -90 and 90")

        return data