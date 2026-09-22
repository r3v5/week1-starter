from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('spatial/', include('spatial_analysis.urls')),
    path('', include('mapping.urls')),
]