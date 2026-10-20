from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='dashboard_index'),
    path('analytics/', views.analytics, name='dashboard_analytics'),
]