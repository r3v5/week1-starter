from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.gis.geos import Polygon
from django.contrib.gis.db.models import Q
from django.db.models import Count, Avg, Sum, Min, Max
from django.utils import timezone
from django.core.paginator import Paginator
from django.conf import settings
import json
import time
from collections import Counter
from datetime import datetime, timedelta
import logging

from .models import AdvancedCity, PolygonAnalysis, SearchSession

# Set up logging
logger = logging.getLogger(__name__)

def index_view(request):
    """
    Homepage view with application overview and quick statistics.
    Provides entry point to main application features.
    """
    context = {
        'total_cities': AdvancedCity.objects.filter(is_active=True).count(),
        'total_countries': AdvancedCity.objects.filter(is_active=True).values('country').distinct().count(),
        'recent_analyses': PolygonAnalysis.objects.filter(
            analysis_timestamp__gte=timezone.now() - timedelta(days=7)
        ).count(),
        'app_version': '1.0.0',
        'last_updated': timezone.now().date()
    }

    return render(request, 'advanced_js_mapping/index.html', context)


def map_view(request):
    """
    Interactive map interface with drawing tools and real-time spatial analysis.
    Main application interface for polygon-based city searches.
    """
    # Get basic statistics for map info panel
    total_cities = AdvancedCity.objects.filter(is_active=True).count()

    # Get sample cities for initial map display (optional)
    sample_cities = AdvancedCity.objects.filter(
        is_active=True,
        population__gte=1000000  # Only major cities for initial load
    )[:50]  # Limit for performance

    # Convert to GeoJSON for map display
    cities_geojson = {
        "type": "FeatureCollection",
        "features": [city.to_geojson_feature() for city in sample_cities]
    }

    context = {
        'total_cities': total_cities,
        'cities_geojson': json.dumps(cities_geojson),
        'map_center_lat': 54.5,  # Center on Europe
        'map_center_lng': 15.0,
        'map_zoom': 4
    }

    return render(request, 'advanced_js_mapping/map.html', context)


@csrf_exempt
@require_http_methods(["POST"])
def polygon_search(request):
    """
    API endpoint for polygon-based spatial search of cities.

    Accepts a polygon defined by coordinates and returns all cities within that polygon.
    Includes performance monitoring and analytics tracking.
    """
    start_time = time.time()

    try:
        # Parse request data
        data = json.loads(request.body)
        coordinates = data.get('coordinates', [])

        if not coordinates or len(coordinates) < 3:
            return JsonResponse({
                'status': 'error',
                'message': 'Invalid polygon coordinates. At least 3 points required.',
                'error_code': 'INVALID_COORDINATES'
            }, status=400)

        # Validate coordinates format
        for coord in coordinates:
            if not isinstance(coord, list) or len(coord) != 2:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Each coordinate must be [longitude, latitude].',
                    'error_code': 'INVALID_COORDINATE_FORMAT'
                }, status=400)

            # Basic coordinate validation
            lng, lat = coord
            if not (-180 <= lng <= 180) or not (-90 <= lat <= 90):
                return JsonResponse({
                    'status': 'error',
                    'message': f'Invalid coordinate values: longitude={lng}, latitude={lat}',
                    'error_code': 'COORDINATE_OUT_OF_BOUNDS'
                }, status=400)

        # Ensure polygon is closed
        if coordinates[0] != coordinates[-1]:
            coordinates.append(coordinates[0])

        # Create PostGIS polygon
        try:
            polygon = Polygon(coordinates, srid=4326)
        except Exception as e:
            logger.error(f"Failed to create polygon: {e}")
            return JsonResponse({
                'status': 'error',
                'message': 'Failed to create valid polygon from coordinates.',
                'error_code': 'POLYGON_CREATION_FAILED'
            }, status=400)

        # Perform spatial query
        query_start = time.time()
        cities_within = AdvancedCity.objects.filter(
            location__within=polygon,
            is_active=True
        ).select_related().order_by('-population')

        # Execute query and measure performance
        cities_list = list(cities_within)
        query_duration = (time.time() - query_start) * 1000  # milliseconds

        # Calculate statistics
        total_cities = len(cities_list)
        total_population = sum(city.population for city in cities_list if city.population)

        # Calculate average GDP (only for cities with GDP data)
        cities_with_gdp = [city for city in cities_list if city.gdp_per_capita]
        average_gdp = sum(city.gdp_per_capita for city in cities_with_gdp) / len(cities_with_gdp) if cities_with_gdp else 0

        # Build response data
        cities_data = []
        for city in cities_list:
            cities_data.append({
                'id': city.id,
                'name': city.name,
                'country': city.country,
                'region': city.region,
                'population': city.population,
                'gdp_per_capita': city.gdp_per_capita,
                'latitude': float(city.latitude) if city.latitude is not None else None,
                'longitude': float(city.longitude) if city.longitude is not None else None,
                'city_type': city.city_type,
                'elevation_m': city.elevation_m,
                'area_km2': city.area_km2,
                'population_density': city.population_density,
                'timezone': city.timezone_name,
                'climate_zone': city.climate_zone
            })

        # Create GeoJSON response
        geojson = {
            "type": "FeatureCollection",
            "features": [city.to_geojson_feature() for city in cities_list]
        }

        # Calculate polygon area (approximate)
        try:
            # Transform to appropriate projection for area calculation
            polygon_area_km2 = polygon.transform(3857, clone=True).area / 1000000  # Convert m² to km²
        except Exception as e:
            logger.warning(f"Failed to calculate polygon area: {e}")
            polygon_area_km2 = None

        # Track analysis for analytics
        try:
            session_id = request.session.session_key or f"anon_{request.META.get('REMOTE_ADDR', 'unknown')}"

            analysis = PolygonAnalysis.objects.create(
                session_id=session_id,
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                ip_address=request.META.get('REMOTE_ADDR'),
                polygon_coordinates=coordinates,
                polygon_area_km2=polygon_area_km2,
                cities_count=total_cities,
                cities_found=[city.id for city in cities_list],
                total_population=total_population,
                average_gdp=average_gdp,
                query_duration_ms=int(query_duration),
                centroid_latitude=polygon.centroid.y,
                centroid_longitude=polygon.centroid.x,
                analysis_type='polygon'
            )

            # Update or create search session
            session, created = SearchSession.objects.get_or_create(
                session_id=session_id,
                defaults={
                    'user_agent': request.META.get('HTTP_USER_AGENT', ''),
                    'ip_address': request.META.get('REMOTE_ADDR'),
                }
            )
            session.update_metrics()

        except Exception as e:
            logger.error(f"Failed to save analysis tracking: {e}")
            # Continue with response even if tracking fails

        total_time = (time.time() - start_time) * 1000  # milliseconds

        # Build successful response
        response = {
            'status': 'success',
            'timestamp': timezone.now().isoformat(),
            'cities_found': total_cities,
            'total_population': total_population,
            'average_gdp': round(average_gdp, 2) if average_gdp else None,
            'polygon_area_km2': round(polygon_area_km2, 2) if polygon_area_km2 else None,
            'query_time_ms': round(query_duration, 2),
            'total_time_ms': round(total_time, 2),
            'cities': cities_data,
            'geojson': geojson,
            'statistics': {
                'countries_represented': len(set(city['country'] for city in cities_data)),
                'largest_city': cities_data[0] if cities_data else None,
                'city_types': dict(Counter(city['city_type'] for city in cities_data if city['city_type'])),
                'population_range': {
                    'min': min((city['population'] for city in cities_data if city['population'] is not None), default=0),
                    'max': max((city['population'] for city in cities_data if city['population'] is not None), default=0)
                }
            }
        }

        logger.info(f"Polygon search completed: {total_cities} cities found in {total_time:.2f}ms")
        return JsonResponse(response)

    except json.JSONDecodeError:
        return JsonResponse({
            'status': 'error',
            'message': 'Invalid JSON in request body.',
            'error_code': 'INVALID_JSON'
        }, status=400)

    except Exception as e:
        logger.error(f"Unexpected error in polygon_search: {e}", exc_info=True)
        return JsonResponse({
            'status': 'error',
            'message': 'Internal server error occurred.',
            'error_code': 'INTERNAL_ERROR'
        }, status=500)


def cities_api(request):
    """
    API endpoint to list all cities with optional filtering and pagination.
    Supports various query parameters for filtering and sorting.
    """
    try:
        # Get query parameters
        country = request.GET.get('country')
        city_type = request.GET.get('type')
        min_population = request.GET.get('min_population')
        max_population = request.GET.get('max_population')
        sort_by = request.GET.get('sort', 'name')  # Default sort by name
        page = int(request.GET.get('page', 1))
        limit = min(int(request.GET.get('limit', 50)), 1000)  # Max 1000 per page

        # Build query
        queryset = AdvancedCity.objects.filter(is_active=True)

        # Apply filters
        if country:
            queryset = queryset.filter(country__icontains=country)

        if city_type:
            queryset = queryset.filter(city_type=city_type)

        if min_population:
            try:
                queryset = queryset.filter(population__gte=int(min_population))
            except ValueError:
                pass

        if max_population:
            try:
                queryset = queryset.filter(population__lte=int(max_population))
            except ValueError:
                pass

        # Apply sorting
        valid_sort_fields = ['name', 'country', 'population', '-population', 'gdp_per_capita', '-gdp_per_capita']
        if sort_by in valid_sort_fields:
            queryset = queryset.order_by(sort_by)
        else:
            queryset = queryset.order_by('name')

        # Apply pagination
        paginator = Paginator(queryset, limit)
        cities_page = paginator.get_page(page)

        # Build response
        cities_data = []
        for city in cities_page:
            cities_data.append({
                'id': city.id,
                'name': city.name,
                'country': city.country,
                'region': city.region,
                'population': city.population,
                'gdp_per_capita': city.gdp_per_capita,
                'latitude': float(city.latitude) if city.latitude is not None else None,
                'longitude': float(city.longitude) if city.longitude is not None else None,
                'city_type': city.city_type,
                'coordinates': city.coordinates
            })

        response = {
            'status': 'success',
            'count': len(cities_data),
            'total_count': paginator.count,
            'total_pages': paginator.num_pages,
            'current_page': page,
            'has_next': cities_page.has_next(),
            'has_previous': cities_page.has_previous(),
            'cities': cities_data
        }

        return JsonResponse(response)

    except Exception as e:
        logger.error(f"Error in cities_api: {e}", exc_info=True)
        return JsonResponse({
            'status': 'error',
            'message': 'Failed to retrieve cities data.'
        }, status=500)


def analytics_view(request):
    """
    Analytics dashboard view with comprehensive statistics and visualizations.
    Shows charts, metrics, and insights about city data and user searches.
    """
    try:
        # Basic statistics
        total_cities = AdvancedCity.objects.filter(is_active=True).count()
        total_countries = AdvancedCity.objects.filter(is_active=True).values('country').distinct().count()
        total_population = AdvancedCity.objects.filter(is_active=True).aggregate(
            total=Sum('population')
        )['total'] or 0

        # Analysis statistics
        total_analyses = PolygonAnalysis.objects.count()
        recent_analyses = PolygonAnalysis.objects.filter(
            analysis_timestamp__gte=timezone.now() - timedelta(days=7)
        ).count()

        try:
            avg_cities_per_search = PolygonAnalysis.objects.aggregate(
                avg=Avg('cities_count')
            )['avg'] or 0

            avg_query_time = PolygonAnalysis.objects.filter(
                query_duration_ms__isnull=False
            ).aggregate(avg=Avg('query_duration_ms'))['avg'] or 0
        except Exception as e:
            logger.warning(f"Failed to calculate analysis averages: {e}")
            avg_cities_per_search = 0
            avg_query_time = 0

        # Countries data for chart
        try:
            countries_data = AdvancedCity.objects.filter(is_active=True).values('country').annotate(
                count=Count('id')
            ).order_by('-count')[:10]  # Top 10 countries

            countries_labels = [item['country'] for item in countries_data]
            countries_counts = [item['count'] for item in countries_data]
        except Exception as e:
            logger.warning(f"Failed to generate countries chart data: {e}")
            countries_labels = []
            countries_counts = []

        # City types data
        try:
            city_types_data = AdvancedCity.objects.filter(is_active=True).values('city_type').annotate(
                count=Count('id')
            ).order_by('-count')

            city_types_labels = [item['city_type'].title() for item in city_types_data if item['city_type']]
            city_types_counts = [item['count'] for item in city_types_data if item['city_type']]
        except Exception as e:
            logger.warning(f"Failed to generate city types chart data: {e}")
            city_types_labels = []
            city_types_counts = []

        # Population distribution
        try:
            population_ranges = [
                ('< 100K', 0, 100000),
                ('100K - 500K', 100000, 500000),
                ('500K - 1M', 500000, 1000000),
                ('1M - 5M', 1000000, 5000000),
                ('> 5M', 5000000, float('inf'))
            ]

            population_labels = []
            population_counts = []

            for label, min_pop, max_pop in population_ranges:
                if max_pop == float('inf'):
                    count = AdvancedCity.objects.filter(
                        is_active=True,
                        population__gte=min_pop
                    ).count()
                else:
                    count = AdvancedCity.objects.filter(
                        is_active=True,
                        population__gte=min_pop,
                        population__lt=max_pop
                    ).count()

                if count > 0:  # Only include ranges with data
                    population_labels.append(label)
                    population_counts.append(count)
        except Exception as e:
            logger.warning(f"Failed to generate population distribution: {e}")
            population_labels = []
            population_counts = []

        # Top cities by population
        try:
            top_cities_by_population = AdvancedCity.objects.filter(
                is_active=True,
                population__isnull=False
            ).order_by('-population')[:10]
        except Exception as e:
            logger.warning(f"Failed to get top cities by population: {e}")
            top_cities_by_population = []

        # Top cities by GDP
        try:
            top_cities_by_gdp = AdvancedCity.objects.filter(
                is_active=True,
                gdp_per_capita__isnull=False
            ).order_by('-gdp_per_capita')[:10]
        except Exception as e:
            logger.warning(f"Failed to get top cities by GDP: {e}")
            top_cities_by_gdp = []

        # Recent analyses list
        try:
            recent_analyses_list = PolygonAnalysis.objects.filter(
                analysis_timestamp__gte=timezone.now() - timedelta(days=30)
            ).order_by('-analysis_timestamp')[:20]
        except Exception as e:
            logger.warning(f"Failed to get recent analyses: {e}")
            recent_analyses_list = []

        context = {
            # Basic stats
            'total_cities': total_cities,
            'total_countries': total_countries,
            'total_population': total_population,
            'total_analyses': total_analyses,
            'recent_analyses': recent_analyses,
            'avg_cities_per_search': round(avg_cities_per_search, 1),
            'avg_query_time': round(avg_query_time, 0),

            # Chart data - need to be JSON serializable
            'countries_labels': json.dumps(countries_labels),
            'countries_data': json.dumps(countries_counts),
            'city_types_labels': json.dumps(city_types_labels),
            'city_types_data': json.dumps(city_types_counts),
            'population_labels': json.dumps(population_labels),
            'population_data': json.dumps(population_counts),

            # Data tables
            'top_cities_by_population': top_cities_by_population,
            'top_cities_by_gdp': top_cities_by_gdp,
            'recent_analyses_list': recent_analyses_list,
        }

        return render(request, 'advanced_js_mapping/analytics.html', context)

    except Exception as e:
        logger.error(f"Error in analytics_view: {e}", exc_info=True)
        # Provide fallback context with error message
        context = {
            'error_message': 'Some analytics data could not be loaded. Please try refreshing the page.',
            'total_cities': 0,
            'total_countries': 0,
            'total_population': 0,
            'total_analyses': 0,
            'recent_analyses': 0,
            'avg_cities_per_search': 0,
            'avg_query_time': 0,
            'countries_labels': json.dumps([]),
            'countries_data': json.dumps([]),
            'city_types_labels': json.dumps([]),
            'city_types_data': json.dumps([]),
            'population_labels': json.dumps([]),
            'population_data': json.dumps([]),
            'top_cities_by_population': [],
            'top_cities_by_gdp': [],
            'recent_analyses_list': [],
        }

        return render(request, 'advanced_js_mapping/analytics.html', context)


def distance_search(request):
    """
    API endpoint for distance-based (radius) search around a point.
    Alternative to polygon search for circular area analysis.
    """
    try:
        # Parse request data
        data = json.loads(request.body)
        latitude = data.get('latitude')
        longitude = data.get('longitude')
        radius_km = data.get('radius_km', 10)  # Default 10km radius

        if latitude is None or longitude is None:
            return JsonResponse({
                'status': 'error',
                'message': 'Latitude and longitude are required.'
            }, status=400)

        # Validate coordinates
        if not (-90 <= latitude <= 90) or not (-180 <= longitude <= 180):
            return JsonResponse({
                'status': 'error',
                'message': 'Invalid coordinate values.'
            }, status=400)

        # Validate radius
        if not (0 < radius_km <= 1000):  # Max 1000km radius
            return JsonResponse({
                'status': 'error',
                'message': 'Radius must be between 0 and 1000 kilometers.'
            }, status=400)

        from django.contrib.gis.geos import Point
        from django.contrib.gis.measure import Distance

        # Create point and search within radius
        center_point = Point(longitude, latitude, srid=4326)

        cities_within = AdvancedCity.objects.filter(
            location__distance_lte=(center_point, Distance(km=radius_km)),
            is_active=True
        ).order_by('-population')

        # Build response
        cities_data = []
        for city in cities_within:
            # Calculate actual distance
            distance_km = city.location.distance(center_point) * 111  # Approximate conversion

            cities_data.append({
                'id': city.id,
                'name': city.name,
                'country': city.country,
                'population': city.population,
                'gdp_per_capita': city.gdp_per_capita,
                'latitude': city.latitude,
                'longitude': city.longitude,
                'distance_km': round(distance_km, 2)
            })

        response = {
            'status': 'success',
            'center_point': {'latitude': latitude, 'longitude': longitude},
            'radius_km': radius_km,
            'cities_found': len(cities_data),
            'cities': cities_data
        }

        return JsonResponse(response)

    except Exception as e:
        logger.error(f"Error in distance_search: {e}", exc_info=True)
        return JsonResponse({
            'status': 'error',
            'message': 'Distance search failed.'
        }, status=500)
