from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('comptes/', include('django.contrib.auth.urls')),
    path('api/', include('inventaire.api_urls')),
    path('api/', include('acces.api_urls')),
    path('acces/', include('acces.urls')),
    path('', include('inventaire.urls')),
]
