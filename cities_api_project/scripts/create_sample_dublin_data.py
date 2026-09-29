"""
Create sample Dublin spatial data for Week 2 lab.
Run inside the Docker container:
  docker compose run --rm web python scripts/create_sample_dublin_data.py
"""

import os
import sys
import django

# Add the project root to Python path so Django can find the hello_map module
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hello_map.settings')
django.setup()

from django.contrib.gis.geos import Point, Polygon, LineString
from spatial_analysis.models import DublinAdminArea, DublinRoad, DublinPOI, LandUseZone

def create_admin_areas():
    """Create sample Dublin administrative areas"""
    areas = [
        {
            'area_name': 'Dublin City Centre',
            'area_type': 'city_center',
            'population': 25000,
            'area_km2': 5.2,
            'geom': Polygon([
                (-6.2800, 53.3350),
                (-6.2400, 53.3350),
                (-6.2400, 53.3650),
                (-6.2800, 53.3650),
                (-6.2800, 53.3350),
            ], srid=4326)
        },
        {
            'area_name': 'Temple Bar District',
            'area_type': 'cultural_quarter',
            'population': 8000,
            'area_km2': 1.1,
            'geom': Polygon([
                (-6.2700, 53.3430),
                (-6.2600, 53.3430),
                (-6.2600, 53.3480),
                (-6.2700, 53.3480),
                (-6.2700, 53.3430),
            ], srid=4326)
        },
        {
            'area_name': 'Phoenix Park Area',
            'area_type': 'recreational',
            'population': 15000,
            'area_km2': 12.5,
            'geom': Polygon([
                (-6.3400, 53.3500),
                (-6.3200, 53.3500),
                (-6.3200, 53.3600),
                (-6.3400, 53.3600),
                (-6.3400, 53.3500),
            ], srid=4326)
        },
        {
            'area_name': 'Docklands',
            'area_type': 'business',
            'population': 18000,
            'area_km2': 3.8,
            'geom': Polygon([
                (-6.2300, 53.3400),
                (-6.2100, 53.3400),
                (-6.2100, 53.3500),
                (-6.2300, 53.3500),
                (-6.2300, 53.3400),
            ], srid=4326)
        },
        {
            'area_name': 'Ballsbridge',
            'area_type': 'residential',
            'population': 22000,
            'area_km2': 4.2,
            'geom': Polygon([
                (-6.2200, 53.3250),
                (-6.2000, 53.3250),
                (-6.2000, 53.3350),
                (-6.2200, 53.3350),
                (-6.2200, 53.3250),
            ], srid=4326)
        },
    ]

    for area_data in areas:
        area, created = DublinAdminArea.objects.get_or_create(
            area_name=area_data['area_name'],
            defaults=area_data
        )
        status = "Created" if created else "Exists"
        print(f"✓ {status}: {area.area_name}")

def create_roads():
    """Create sample Dublin roads"""
    roads = [
        {
            'road_name': "O'Connell Street",
            'road_type': 'main_street',
            'speed_limit': 30,
            'length_meters': 500,
            'geom': LineString([(-6.2603, 53.3498), (-6.2603, 53.3548)], srid=4326)
        },
        {
            'road_name': 'Grafton Street',
            'road_type': 'pedestrian',
            'speed_limit': 0,
            'length_meters': 400,
            'geom': LineString([(-6.2601, 53.3398), (-6.2601, 53.3448)], srid=4326)
        },
        {
            'road_name': 'Dame Street',
            'road_type': 'main_street',
            'speed_limit': 30,
            'length_meters': 600,
            'geom': LineString([(-6.2703, 53.3434), (-6.2603, 53.3434)], srid=4326)
        },
        {
            'road_name': 'Quays Road',
            'road_type': 'secondary',
            'speed_limit': 50,
            'length_meters': 1200,
            'geom': LineString([(-6.2803, 53.3468), (-6.2403, 53.3468)], srid=4326)
        },
        {
            'road_name': 'Ring Road M50',
            'road_type': 'motorway',
            'speed_limit': 100,
            'length_meters': 2000,
            'geom': LineString([(-6.3503, 53.3598), (-6.2003, 53.3298)], srid=4326)
        },
    ]

    for road_data in roads:
        road, created = DublinRoad.objects.get_or_create(
            road_name=road_data['road_name'],
            defaults=road_data
        )
        status = "Created" if created else "Exists"
        print(f"✓ {status}: {road.road_name}")

def create_pois():
    """Create sample Dublin points of interest"""
    pois = [
        {
            'poi_name': 'Trinity College Library',
            'poi_type': 'education',
            'visitors_per_day': 2500,
            'rating': 4.8,
            'description': 'Historic university library with the Book of Kells',
            'geom': Point(-6.2603, 53.3441, srid=4326)
        },
        {
            'poi_name': 'Dublin Castle',
            'poi_type': 'historic',
            'visitors_per_day': 1800,
            'rating': 4.5,
            'description': 'Historic castle in the heart of Dublin',
            'geom': Point(-6.2674, 53.3429, srid=4326)
        },
        {
            'poi_name': 'Temple Bar Pub',
            'poi_type': 'entertainment',
            'visitors_per_day': 3000,
            'rating': 4.2,
            'description': 'Historic pub in Temple Bar cultural quarter',
            'geom': Point(-6.2668, 53.3453, srid=4326)
        },
        {
            'poi_name': 'Phoenix Park Visitor Centre',
            'poi_type': 'attraction',
            'visitors_per_day': 1200,
            'rating': 4.6,
            'description': 'Visitor centre for Europe\'s largest enclosed urban park',
            'geom': Point(-6.3298, 53.3558, srid=4326)
        },
        {
            'poi_name': 'Dublin Port',
            'poi_type': 'transport',
            'visitors_per_day': 5000,
            'rating': 4.0,
            'description': 'Major shipping and ferry terminal',
            'geom': Point(-6.2200, 53.3450, srid=4326)
        },
        {
            'poi_name': "St. Stephen's Green Shopping",
            'poi_type': 'commercial',
            'visitors_per_day': 15000,
            'rating': 4.4,
            'description': 'Major shopping center on historic green space',
            'geom': Point(-6.2580, 53.3388, srid=4326)
        },
        {
            'poi_name': 'Guinness Storehouse',
            'poi_type': 'attraction',
            'visitors_per_day': 4000,
            'rating': 4.7,
            'description': 'Museum and visitor attraction dedicated to Guinness',
            'geom': Point(-6.2738, 53.3412, srid=4326)
        },
    ]

    for poi_data in pois:
        poi, created = DublinPOI.objects.get_or_create(
            poi_name=poi_data['poi_name'],
            defaults=poi_data
        )
        status = "Created" if created else "Exists"
        print(f"✓ {status}: {poi.poi_name}")

def create_zones():
    """Create sample land use zones"""
    zones = [
        {
            'zone_name': 'City Centre Mixed Use',
            'zone_type': 'mixed_use',
            'zoning_code': 'Z01',
            'permitted_uses': 'Retail, Office, Residential, Cultural, Recreation',
            'geom': Polygon([
                (-6.2800, 53.3350),
                (-6.2400, 53.3350),
                (-6.2400, 53.3650),
                (-6.2800, 53.3650),
                (-6.2800, 53.3350),
            ], srid=4326)
        },
        {
            'zone_name': 'Docklands Commercial',
            'zone_type': 'commercial',
            'zoning_code': 'Z02',
            'permitted_uses': 'Office, Retail, Business Services, Hotels',
            'geom': Polygon([
                (-6.2300, 53.3400),
                (-6.2100, 53.3400),
                (-6.2100, 53.3500),
                (-6.2300, 53.3500),
                (-6.2300, 53.3400),
            ], srid=4326)
        },
        {
            'zone_name': 'Residential South Dublin',
            'zone_type': 'residential',
            'zoning_code': 'Z03',
            'permitted_uses': 'Residential, Local Services, Community Facilities',
            'geom': Polygon([
                (-6.2200, 53.3250),
                (-6.2000, 53.3250),
                (-6.2000, 53.3350),
                (-6.2200, 53.3350),
                (-6.2200, 53.3250),
            ], srid=4326)
        },
        {
            'zone_name': 'Phoenix Park Protected',
            'zone_type': 'protected',
            'zoning_code': 'Z04',
            'permitted_uses': 'Recreation, Cultural Events, Education, Conservation',
            'geom': Polygon([
                (-6.3400, 53.3500),
                (-6.3200, 53.3500),
                (-6.3200, 53.3600),
                (-6.3400, 53.3600),
                (-6.3400, 53.3500),
            ], srid=4326)
        },
    ]

    for zone_data in zones:
        zone, created = LandUseZone.objects.get_or_create(
            zoning_code=zone_data['zoning_code'],
            defaults=zone_data
        )
        status = "Created" if created else "Exists"
        print(f"✓ {status}: {zone.zone_name}")

if __name__ == '__main__':
    print(" Creating sample Dublin spatial data...\n")

    print(" Creating administrative areas...")
    create_admin_areas()

    print("\n Creating roads...")
    create_roads()

    print("\n Creating points of interest...")
    create_pois()

    print("\n Creating land use zones...")
    create_zones()

    print("\n Sample data creation completed!")