from django.urls import path
from . import views

app_name = 'cities_api'

urlpatterns = [
    # Basic CRUD endpoints
    path('', views.CityListCreateView.as_view(), name='city-list-create'),
    path('<int:pk>/', views.CityDetailView.as_view(), name='city-detail'),

    # Special format endpoints
    path('geojson/', views.CityGeoJSONView.as_view(), name='city-geojson'),

    # Spatial query endpoints
    path('within-radius/', views.cities_within_radius, name='cities-within-radius'),
    path('bbox/', views.cities_in_bounding_box, name='cities-bbox'),

    # Statistics and metadata
    path('stats/', views.city_statistics, name='city-statistics'),
    path('countries/', views.countries_list, name='countries-list'),
    path('info/', views.api_info, name='api-info'),
]