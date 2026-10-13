import django_filters
from .models import City

class CityFilter(django_filters.FilterSet):
    """Filter set for City model"""

    name = django_filters.CharFilter(lookup_expr='icontains')
    country = django_filters.CharFilter(lookup_expr='icontains')
    region = django_filters.CharFilter(lookup_expr='icontains')

    min_population = django_filters.NumberFilter(
        field_name='population',
        lookup_expr='gte'
    )
    max_population = django_filters.NumberFilter(
        field_name='population',
        lookup_expr='lte'
    )

    min_founded_year = django_filters.NumberFilter(
        field_name='founded_year',
        lookup_expr='gte'
    )
    max_founded_year = django_filters.NumberFilter(
        field_name='founded_year',
        lookup_expr='lte'
    )

    is_capital = django_filters.BooleanFilter()

    class Meta:
        model = City
        fields = [
            'name', 'country', 'region', 'is_capital',
            'min_population', 'max_population',
            'min_founded_year', 'max_founded_year'
        ]