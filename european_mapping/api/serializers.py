# api/serializers.py
from rest_framework import serializers
from rest_framework_gis.serializers import GeoFeatureModelSerializer
from cities.models import City
from regions.models import Region

class CitySerializer(GeoFeatureModelSerializer):
    class Meta:
        model = City
        geo_field = "location"
        fields = [
            'id', 'name', 'country', 'population', 'latitude', 'longitude',
            'city_type', 'urban_area_km2', 'population_density', 
            'gdp_per_capita', 'unemployment_rate', 'green_space_percentage',
            'elevation', 'region_code', 'population_year', 'data_source'
        ]

class RegionSerializer(GeoFeatureModelSerializer):
    class Meta:
        model = Region
        geo_field = "geometry"
        fields = [
            'id', 'name', 'country', 'region_code', 'region_type',
            'area_km2', 'total_population', 'population_density',
            'urban_population_pct', 'gdp_per_capita', 'unemployment_rate',
            'admin_level', 'agricultural_area_pct', 'forest_area_pct',
            'urban_area_pct', 'population_year', 'data_source'
        ]