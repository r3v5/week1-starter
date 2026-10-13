from rest_framework import generics, status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from rest_framework_gis.pagination import GeoJsonPagination
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from django.contrib.gis.geos import Point
from django.contrib.gis.measure import D
from django.db.models import Count, Avg, Q, Sum
from django.contrib.gis.db.models.functions import Distance

from .models import City
from .serializers import (
    CityListSerializer, CityDetailSerializer, CityGeoJSONSerializer,
    CityCreateSerializer, CitySummarySerializer, DistanceSerializer,
    BoundingBoxSerializer
)
from .filters import CityFilter
import json

class StandardResultsSetPagination(PageNumberPagination):
    """Custom pagination class"""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class GeoJSONResultsSetPagination(GeoJsonPagination):
    """Pagination that keeps the response a valid GeoJSON FeatureCollection"""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100

class CityListCreateView(generics.ListCreateAPIView):
    """
    List all cities or create a new city
    """
    queryset = City.objects.all()
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = CityFilter
    search_fields = ['name', 'country', 'region']
    ordering_fields = ['name', 'country', 'population', 'founded_year']
    ordering = ['-population']  # Default ordering

    def get_serializer_class(self):
        """Use different serializers for list vs create"""
        if self.request.method == 'POST':
            return CityCreateSerializer
        return CityListSerializer

    def get_queryset(self):
        """Optionally filter queryset based on query parameters"""
        queryset = City.objects.all()

        # Additional custom filters
        min_population = self.request.query_params.get('min_population')
        if min_population:
            try:
                min_pop = int(min_population)
                queryset = queryset.filter(population__gte=min_pop)
            except ValueError:
                pass

        capitals_only = self.request.query_params.get('capitals_only')
        if capitals_only and capitals_only.lower() == 'true':
            queryset = queryset.filter(is_capital=True)

        return queryset

class CityDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update, or delete a city instance
    """
    queryset = City.objects.all()
    serializer_class = CityDetailSerializer

    def get_serializer_class(self):
        """Use create serializer for updates"""
        if self.request.method in ['PUT', 'PATCH']:
            return CityCreateSerializer
        return CityDetailSerializer

class CityGeoJSONView(generics.ListAPIView):
    """
    Return cities as GeoJSON for mapping applications
    """
    queryset = City.objects.all()
    serializer_class = CityGeoJSONSerializer
    pagination_class = GeoJSONResultsSetPagination
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_class = CityFilter
    search_fields = ['name', 'country']

@api_view(['GET'])
def city_statistics(request):
    """
    Return statistical summary of cities data
    """
    stats = {
        'total_cities': City.objects.count(),
        'total_population': City.objects.aggregate(
            total=Sum('population')
        )['total'] or 0,
        'countries_count': City.objects.values('country').distinct().count(),
        'capitals_count': City.objects.filter(is_capital=True).count(),
        'average_population': City.objects.aggregate(
            avg=Avg('population')
        )['avg'] or 0,
    }

    # Largest and smallest cities
    largest = City.objects.order_by('-population').first()
    smallest = City.objects.order_by('population').first()

    stats['largest_city'] = str(largest) if largest else 'N/A'
    stats['smallest_city'] = str(smallest) if smallest else 'N/A'

    serializer = CitySummarySerializer(stats)
    return Response(serializer.data)

@api_view(['POST'])
def cities_within_radius(request):
    """
    Find cities within specified radius of a point
    """
    serializer = DistanceSerializer(data=request.data)
    if serializer.is_valid():
        data = serializer.validated_data
        center_point = Point(
            data['longitude'],
            data['latitude'],
            srid=4326
        )

        cities = City.objects.within_radius(
            center_point,
            data['radius_km']
        ).annotate(
            distance=Distance('location', center_point)
        ).order_by('distance')

        # Add distance to serialized data
        city_data = CityListSerializer(cities, many=True).data
        for i, city in enumerate(cities):
            city_data[i]['distance_km'] = round(city.distance.km, 2)

        return Response({
            'center': {
                'latitude': data['latitude'],
                'longitude': data['longitude']
            },
            'radius_km': data['radius_km'],
            'count': cities.count(),
            'cities': city_data
        })

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
def cities_in_bounding_box(request):
    """
    Find cities within a bounding box
    """
    serializer = BoundingBoxSerializer(data=request.data)
    if serializer.is_valid():
        data = serializer.validated_data
        bbox = [
            data['min_longitude'],
            data['min_latitude'],
            data['max_longitude'],
            data['max_latitude']
        ]

        cities = City.objects.in_bounding_box(bbox)

        return Response({
            'bounding_box': {
                'min_longitude': data['min_longitude'],
                'min_latitude': data['min_latitude'],
                'max_longitude': data['max_longitude'],
                'max_latitude': data['max_latitude']
            },
            'count': cities.count(),
            'cities': CityListSerializer(cities, many=True).data
        })

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
def countries_list(request):
    """
    Return list of countries with city counts
    """
    countries = (City.objects
                 .values('country')
                 .annotate(city_count=Count('id'))
                 .annotate(total_population=Sum('population'))
                 .annotate(capitals_count=Count('id', filter=Q(is_capital=True)))
                 .order_by('country'))

    return Response(list(countries))

@api_view(['GET'])
def api_info(request):
    """
    Return API information and available endpoints
    """
    base_url = request.build_absolute_uri('/api/cities/')

    endpoints = {
        'cities_list': f"{base_url}",
        'cities_geojson': f"{base_url}geojson/",
        'city_detail': f"{base_url}{id}/",
        'cities_within_radius': f"{base_url}within-radius/",
        'cities_in_bbox': f"{base_url}bbox/",
        'statistics': f"{base_url}stats/",
        'countries': f"{base_url}countries/",
        'api_docs': request.build_absolute_uri('/api/docs/'),
    }

    return Response({
        'api_name': 'Cities API',
        'version': '1.0',
        'description': 'RESTful API for city data with spatial capabilities',
        'endpoints': endpoints,
        'features': [
            'City CRUD operations',
            'GeoJSON output',
            'Spatial queries (radius, bounding box)',
            'Filtering and search',
            'Pagination',
            'Statistics'
        ]
    })



@api_view(['GET'])
def cities_geojson(request):
    """Export cities as GeoJSON"""
    from cities_api.models import City
    cities = City.objects.all()

    features = []
    for city in cities:
        feature = {
            'type': 'Feature',
            'properties': {
                'name': city.name,
                'country': city.country,
                'population': city.population,
            },
            'geometry': {
                'type': 'Point',
                'coordinates': [city.longitude, city.latitude]
            }
        }
        features.append(feature)

    return Response({
        'type': 'FeatureCollection',
        'features': features
    })



def parse_search_parameters(data, include_radius=False):
    try:
        lat = float(data["lat"])
        lng = float(data["lng"])
    except (KeyError, TypeError, ValueError):
        return None, Response(
            {"error": "Provide numeric lat and lng values."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    radius_km = None
    if include_radius:
        try:
            radius_km = float(data.get("radius_km", 100))
        except (TypeError, ValueError):
            return None, Response(
                {"error": "radius_km must be a number."},
                status=status.HTTP_400_BAD_REQUEST,
            )

    if not -90 <= lat <= 90 or not -180 <= lng <= 180:
        return None, Response(
            {"error": "Latitude must be between -90 and 90 and longitude between -180 and 180."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if include_radius and not 0 < radius_km <= 20000:
        return None, Response(
            {"error": "radius_km must be greater than 0 and no more than 20000."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    return (lat, lng, radius_km), None


# Only the fields serialize_city() reads; skips region, timestamps, etc.
PROXIMITY_FIELDS = ("id", "name", "country", "population", "location")


def nearest_cities_queryset(search_point, limit=10):
    return City.objects.filter(location__isnull=False).only(
        *PROXIMITY_FIELDS
    ).annotate(
        distance=Distance("location", search_point)
    ).order_by("distance")[:limit]


def cities_within_radius_queryset(search_point, radius_km):
    return City.objects.filter(
        location__isnull=False,
        location__distance_lte=(search_point, D(km=radius_km)),
    ).only(
        *PROXIMITY_FIELDS
    ).annotate(
        distance=Distance("location", search_point)
    ).order_by("distance")


def serialize_city(city, rank=None):
    result = {
        "id": city.id,
        "name": city.name,
        "country": city.country,
        "population": city.population,
        "coordinates": {
            "lat": city.location.y,
            "lng": city.location.x,
        },
        "distance_km": round(city.distance.km, 2),
    }
    if rank is not None:
        result["rank"] = rank
    return result


@api_view(["POST"])
def find_nearest_cities(request):
    """POST /api/cities/nearest/ with {"lat": 53.3498, "lng": -6.2603}."""
    parameters, error = parse_search_parameters(request.data)
    if error:
        return error

    lat, lng, _ = parameters
    search_point = Point(lng, lat, srid=4326)
    cities = nearest_cities_queryset(search_point)
    results = [serialize_city(city, rank) for rank, city in enumerate(cities, 1)]

    return Response({
        "search_point": {"lat": lat, "lng": lng},
        "total_found": len(results),
        "nearest_cities": results,
    })


@api_view(["POST"])
def find_cities_within_radius(request):
    """POST /api/cities/radius/ with lat, lng, and optional radius_km."""
    parameters, error = parse_search_parameters(request.data, include_radius=True)
    if error:
        return error

    lat, lng, radius_km = parameters
    search_point = Point(lng, lat, srid=4326)
    cities = cities_within_radius_queryset(search_point, radius_km)
    results = [serialize_city(city) for city in cities]

    return Response({
        "search_point": {"lat": lat, "lng": lng},
        "radius_km": radius_km,
        "total_found": len(results),
        "cities": results,
    })