import django_filters
from django_filters import rest_framework as filters
from cities.models import City
from regions.models import Region

class CityFilter(filters.FilterSet):
    # Population filters
    population_min = filters.NumberFilter(field_name="population", lookup_expr='gte')
    population_max = filters.NumberFilter(field_name="population", lookup_expr='lte')
    population_range = filters.RangeFilter(field_name="population")

    # Population density filters
    density_min = filters.NumberFilter(field_name="population_density", lookup_expr='gte')
    density_max = filters.NumberFilter(field_name="population_density", lookup_expr='lte')

    # Area filters
    urban_area_min = filters.NumberFilter(field_name="urban_area_km2", lookup_expr='gte')
    urban_area_max = filters.NumberFilter(field_name="urban_area_km2", lookup_expr='lte')

    # Economic filters
    gdp_min = filters.NumberFilter(field_name="gdp_per_capita", lookup_expr='gte')
    gdp_max = filters.NumberFilter(field_name="gdp_per_capita", lookup_expr='lte')
    unemployment_max = filters.NumberFilter(field_name="unemployment_rate", lookup_expr='lte')

    # Green space filter
    green_space_min = filters.NumberFilter(field_name="green_space_percentage", lookup_expr='gte')

    # Geographic filters
    country = filters.CharFilter(lookup_expr='icontains')
    region_code = filters.CharFilter(lookup_expr='exact')

    # Multiple choice filters
    city_type = filters.MultipleChoiceFilter(choices=City._meta.get_field('city_type').choices)

    # Custom method filters
    large_cities = filters.BooleanFilter(method='filter_large_cities')
    eco_friendly = filters.BooleanFilter(method='filter_eco_friendly')

    class Meta:
        model = City
        fields = {
            'name': ['icontains', 'istartswith'],
            'population_year': ['exact', 'gte', 'lte'],
            'elevation': ['gte', 'lte'],
        }

    def filter_large_cities(self, queryset, name, value):
        """Filter for cities with population > 1 million"""
        if value:
            return queryset.filter(population__gte=1000000)
        return queryset

    def filter_eco_friendly(self, queryset, name, value):
        """Filter for cities with high green space percentage"""
        if value:
            return queryset.filter(green_space_percentage__gte=30)
        return queryset

class RegionFilter(filters.FilterSet):
    # Population filters
    population_min = filters.NumberFilter(field_name="total_population", lookup_expr='gte')
    population_max = filters.NumberFilter(field_name="total_population", lookup_expr='lte')
    population_range = filters.RangeFilter(field_name="total_population")

    # Population density filters
    density_min = filters.NumberFilter(field_name="population_density", lookup_expr='gte')
    density_max = filters.NumberFilter(field_name="population_density", lookup_expr='lte')

    # Area filters
    area_min = filters.NumberFilter(field_name="area_km2", lookup_expr='gte')
    area_max = filters.NumberFilter(field_name="area_km2", lookup_expr='lte')
    area_range = filters.RangeFilter(field_name="area_km2")

    # Economic filters
    gdp_total_min = filters.NumberFilter(field_name="gdp_total", lookup_expr='gte')
    gdp_per_capita_min = filters.NumberFilter(field_name="gdp_per_capita", lookup_expr='gte')
    unemployment_max = filters.NumberFilter(field_name="unemployment_rate", lookup_expr='lte')

    # Land use filters
    urban_pct_min = filters.NumberFilter(field_name="urban_area_pct", lookup_expr='gte')
    forest_pct_min = filters.NumberFilter(field_name="forest_area_pct", lookup_expr='gte')
    agricultural_pct_min = filters.NumberFilter(field_name="agricultural_area_pct", lookup_expr='gte')

    # Administrative filters
    region_type = filters.MultipleChoiceFilter(choices=Region._meta.get_field('region_type').choices)
    admin_level = filters.NumberFilter()
    country = filters.CharFilter(lookup_expr='icontains')

    # Custom filters
    high_density = filters.BooleanFilter(method='filter_high_density')
    rural_dominant = filters.BooleanFilter(method='filter_rural_dominant')

    class Meta:
        model = Region
        fields = {
            'name': ['icontains', 'istartswith'],
            'population_year': ['exact', 'gte', 'lte'],
        }

    def filter_high_density(self, queryset, name, value):
        """Filter for high population density regions (>100 people/km²)"""
        if value:
            return queryset.filter(population_density__gte=100)
        return queryset

    def filter_rural_dominant(self, queryset, name, value):
        """Filter for regions with low urban population percentage"""
        if value:
            return queryset.filter(urban_population_pct__lte=30)
        return queryset