from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('comptes/', include('django.contrib.auth.urls')),
    path('api/', include('inventaire.api_urls')),
    path('', include('inventaire.urls')),
]
