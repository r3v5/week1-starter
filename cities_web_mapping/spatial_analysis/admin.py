from django.contrib import admin
from django.contrib.gis.admin import GISModelAdmin
from .models import DublinAdminArea, DublinRoad, DublinPOI, LandUseZone

@admin.register(DublinAdminArea)
class DublinAdminAreaAdmin(GISModelAdmin):
    list_display = ['area_name', 'area_type', 'population', 'area_km2']
    list_filter = ['area_type', 'created_at']
    search_fields = ['area_name']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(DublinRoad)
class DublinRoadAdmin(GISModelAdmin):
    list_display = ['road_name', 'road_type', 'speed_limit', 'length_meters']
    list_filter = ['road_type', 'speed_limit']
    search_fields = ['road_name']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(DublinPOI)
class DublinPOIAdmin(GISModelAdmin):
    list_display = ['poi_name', 'poi_type', 'rating', 'visitors_per_day']
    list_filter = ['poi_type', 'rating']
    search_fields = ['poi_name', 'description']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(LandUseZone)
class LandUseZoneAdmin(GISModelAdmin):
    list_display = ['zone_name', 'zone_type', 'zoning_code']
    list_filter = ['zone_type']
    search_fields = ['zone_name', 'zoning_code']
    readonly_fields = ['created_at', 'updated_at']