from django.urls import path
from . import views

app_name = 'advanced_js_mapping'

urlpatterns = [
    # Main application views
    path('', views.index_view, name='index'),
    path('map/', views.map_view, name='map'),
    path('analytics/', views.analytics_view, name='analytics'),

    # API endpoints
    path('api/polygon-search/', views.polygon_search, name='polygon_search'),
    path('api/cities/', views.cities_api, name='cities_api'),
    path('api/distance-search/', views.distance_search, name='distance_search'),
]
