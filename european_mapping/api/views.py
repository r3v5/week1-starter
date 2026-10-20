# api/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.gis.geos import Point
from django.contrib.gis.db.models.functions import Distance
from django.db.models import Count, Avg, Min, Max, Sum

from cities.models import City
from regions.models import Region
from .serializers import CitySerializer, RegionSerializer

class CityViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = City.objects.all()
    serializer_class = CitySerializer
    pagination_class = None  # Disable pagination for clean GeoJSON

    def get_queryset(self):
        queryset = City.objects.all()

        # Population filters
        population_min = self.request.query_params.get('population_min')
        population_max = self.request.query_params.get('population_max')

        if population_min:
            queryset = queryset.filter(population__gte=population_min)
        if population_max:
            queryset = queryset.filter(population__lte=population_max)

        # Area filters
        urban_area_min = self.request.query_params.get('urban_area_min')
        urban_area_max = self.request.query_params.get('urban_area_max')

        if urban_area_min:
            queryset = queryset.filter(urban_area_km2__gte=urban_area_min)
        if urban_area_max:
            queryset = queryset.filter(urban_area_km2__lte=urban_area_max)

        # Category filters
        country = self.request.query_params.get('country')
        city_type = self.request.query_params.get('city_type')

        if country:
            queryset = queryset.filter(country=country)
        if city_type:
            queryset = queryset.filter(city_type=city_type)

        return queryset

    def list(self, request, *args, **kwargs):
        """Override list to return proper GeoJSON FeatureCollection"""
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get comprehensive cities statistics"""
        queryset = self.get_queryset()

        stats = {
            'total_cities': queryset.count(),
            'total_population': queryset.aggregate(Sum('population'))['population__sum'] or 0,
            'population_stats': {
                'min': queryset.aggregate(Min('population'))['population__min'] or 0,
                'max': queryset.aggregate(Max('population'))['population__max'] or 0,
                'avg': int(queryset.aggregate(Avg('population'))['population__avg'] or 0),
            },
            'countries_count': queryset.values('country').distinct().count(),
            'city_types_distribution': dict(
                queryset.values('city_type')
                .annotate(count=Count('id'))
                .values_list('city_type', 'count')
            ),
        }

        return Response(stats)

    @action(detail=False, methods=['get'])
    def nearby(self, request):
        """Find cities near a point"""
        lat = request.query_params.get('lat')
        lng = request.query_params.get('lng')
        distance_km = request.query_params.get('distance', 50)

        if not lat or not lng:
            return Response(
                {'error': 'lat and lng parameters are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            point = Point(float(lng), float(lat), srid=4326)
            distance_m = float(distance_km) * 1000

            nearby_cities = City.objects.filter(
                location__distance_lte=(point, distance_m)
            ).annotate(
                distance=Distance('location', point)
            ).order_by('distance')

            serializer = self.get_serializer(nearby_cities, many=True)
            return Response(serializer.data)

        except (ValueError, TypeError):
            return Response(
                {'error': 'Invalid coordinates or distance'},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=False, methods=['post'])
    def within_bounds(self, request):
        """Find cities within bounding box"""
        data = request.data
        required_fields = ['west', 'south', 'east', 'north']

        if not all(field in data for field in required_fields):
            return Response(
                {'error': f'Required fields: {required_fields}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            west, south, east, north = [float(data[field]) for field in required_fields]

            cities_in_bounds = City.objects.filter(
                latitude__gte=south,
                latitude__lte=north,
                longitude__gte=west,
                longitude__lte=east
            )

            serializer = self.get_serializer(cities_in_bounds, many=True)
            return Response(serializer.data)

        except (ValueError, TypeError):
            return Response(
                {'error': 'Invalid bounding box coordinates'},
                status=status.HTTP_400_BAD_REQUEST
            )


class RegionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Region.objects.all()
    serializer_class = RegionSerializer
    pagination_class = None  # Disable pagination for clean GeoJSON

    def get_queryset(self):
        queryset = Region.objects.all()

        # Area filters
        area_min = self.request.query_params.get('area_min')
        area_max = self.request.query_params.get('area_max')

        if area_min:
            queryset = queryset.filter(area_km2__gte=area_min)
        if area_max:
            queryset = queryset.filter(area_km2__lte=area_max)

        # Population filters
        population_min = self.request.query_params.get('population_min')
        population_max = self.request.query_params.get('population_max')

        if population_min:
            queryset = queryset.filter(total_population__gte=population_min)
        if population_max:
            queryset = queryset.filter(total_population__lte=population_max)

        # Category filters
        country = self.request.query_params.get('country')
        region_type = self.request.query_params.get('region_type')

        if country:
            queryset = queryset.filter(country=country)
        if region_type:
            queryset = queryset.filter(region_type=region_type)

        return queryset

    def list(self, request, *args, **kwargs):
        """Override list to return proper GeoJSON FeatureCollection"""
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get comprehensive regions statistics"""
        queryset = self.get_queryset()

        stats = {
            'total_regions': queryset.count(),
            'total_population': queryset.aggregate(Sum('total_population'))['total_population__sum'] or 0,
            'total_area_km2': queryset.aggregate(Sum('area_km2'))['area_km2__sum'] or 0,
            'region_types_distribution': dict(
                queryset.values('region_type')
                .annotate(count=Count('id'))
                .values_list('region_type', 'count')
            ),
            'countries_count': queryset.values('country').distinct().count(),
        }

        return Response(stats)