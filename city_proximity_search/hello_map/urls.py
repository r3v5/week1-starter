from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('cities_api.urls')),  # Week 3 REST API
    path('map/', TemplateView.as_view(template_name='map.html'), name='map'),  # NEW
    path('', TemplateView.as_view(template_name='map.html'), name='map_home'),  # Root redirect
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)