from django.urls import path
from rest_framework.routers import DefaultRouter
from .api import BadgeViewSet, JournalAccesViewSet, PorteViewSet, passage_badge

router = DefaultRouter()
router.register('portes', PorteViewSet)
router.register('badges', BadgeViewSet)
router.register('journal-acces', JournalAccesViewSet)
urlpatterns = [path('acces/', passage_badge, name='api-acces')] + router.urls
