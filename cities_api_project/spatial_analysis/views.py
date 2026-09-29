from django.shortcuts import render
from django.contrib.gis.db.models import Q
from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.geos import Point
from .models import DublinAdminArea, DublinRoad, DublinPOI, LandUseZone

def spatial_analysis_dashboard(request):
    """Dashboard showing spatial analysis of Dublin data"""

    context = {
        'total_admin_areas': DublinAdminArea.objects.count(),
        'total_roads': DublinRoad.objects.count(),
        'total_pois': DublinPOI.objects.count(),
        'total_zones': LandUseZone.objects.count(),

        'admin_areas': DublinAdminArea.objects.all(),
        'major_roads': DublinRoad.objects.filter(
            road_type__in=['motorway', 'main_street']
        ).order_by('-speed_limit'),
        'attractions': DublinPOI.objects.filter(
            poi_type__in=['attraction', 'historic']
        ).order_by('-rating'),
        'zones': LandUseZone.objects.all(),
    }

    return render(request, 'spatial_analysis/dashboard.html', context)

def poi_detail(request, pk):
    """Detail view for a single POI"""
    poi = DublinPOI.objects.get(pk=pk)

    # Find nearby roads (within 1km)
    nearby_roads = DublinRoad.objects.filter(
        geom__distance_lte=(poi.geom, 1000)  # 1km, in meters (ST_DistanceSphere)
    ).annotate(
        distance=Distance('geom', poi.geom)
    ).order_by('distance')[:5]

    context = {
        'poi': poi,
        'nearby_roads': nearby_roads,
        'poi_json': poi.geom.json,
    }

    return render(request, 'spatial_analysis/poi_details.html', context)
