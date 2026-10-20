from django.db.models import Avg, Count, Max, Min, Sum
from django.shortcuts import render

from cities.models import City
from regions.models import Region


def index(request):
    """Main dashboard view"""
    context = {
        'total_cities': City.objects.count(),
        'total_regions': Region.objects.count(),
        'countries': City.objects.values_list('country', flat=True).distinct().order_by('country'),
        'region_types': Region.objects.values_list('region_type', flat=True).distinct(),
        'city_types': [choice[0] for choice in City._meta.get_field('city_type').choices],
    }
    return render(request, 'dashboard/index.html', context)


def analytics(request):
    """Analytics page with detailed statistics"""
    city_queryset = City.objects.all()
    city_stats = city_queryset.aggregate(
        total_cities=Count('id'),
        total_population=Sum('population'),
        avg_population=Avg('population'),
        max_population=Max('population'),
        min_population=Min('population'),
        avg_area=Avg('urban_area_km2'),
    )

    region_queryset = Region.objects.all()
    region_stats = region_queryset.aggregate(
        total_regions=Count('id'),
        avg_population=Avg('total_population'),
        max_population=Max('total_population'),
        min_population=Min('total_population'),
        avg_area=Avg('area_km2'),
        avg_gdp_per_capita=Avg('gdp_per_capita'),
    )
    # Separate query: an alias named 'total_population' would shadow the
    # model field and break the other aggregates over it.
    region_stats['total_population'] = region_queryset.aggregate(
        total=Sum('total_population'))['total']

    context = {
        'city_stats': city_stats,
        'region_stats': region_stats,
    }
    return render(request, 'dashboard/analytics.html', context)