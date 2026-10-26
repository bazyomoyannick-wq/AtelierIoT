from django.urls import path
from rest_framework.authtoken.views import obtain_auth_token
from rest_framework.routers import DefaultRouter
from .api import (ObjetViewSet, CapteurViewSet, ActionneurViewSet, MesureViewSet,
                  CommandeViewSet, SuppressionViewSet, inscription)

router = DefaultRouter()
router.register('objets', ObjetViewSet)
router.register('capteurs', CapteurViewSet)
router.register('actionneurs', ActionneurViewSet)
router.register('mesures', MesureViewSet)
router.register('commandes', CommandeViewSet)
router.register('suppressions', SuppressionViewSet)
urlpatterns = [
    path('inscription/', inscription, name='api-inscription'),
    path('jeton/', obtain_auth_token, name='api-jeton'),
] + router.urls
